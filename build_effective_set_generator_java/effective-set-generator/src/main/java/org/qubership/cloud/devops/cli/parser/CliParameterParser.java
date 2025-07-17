/*
 * Copyright 2024-2025 NetCracker Technology Corporation
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

package org.qubership.cloud.devops.cli.parser;


import jakarta.enterprise.context.Dependent;
import jakarta.inject.Inject;
import lombok.extern.slf4j.Slf4j;
import org.apache.commons.lang3.StringUtils;
import org.qubership.cloud.devops.cli.exceptions.DirectoryCreateException;
import org.qubership.cloud.devops.cli.pojo.dto.input.InputData;
import org.qubership.cloud.devops.cli.pojo.dto.sd.SBApplicationDTO;
import org.qubership.cloud.devops.cli.pojo.dto.sd.SolutionBomDTO;
import org.qubership.cloud.devops.cli.pojo.dto.shared.SharedData;
import org.qubership.cloud.devops.commons.exceptions.ConsumerFileProcessingException;
import org.qubership.cloud.devops.commons.exceptions.CreateWorkDirException;
import org.qubership.cloud.devops.commons.exceptions.NotFoundException;
import org.qubership.cloud.devops.commons.pojo.consumer.ConsumerDTO;
import org.qubership.cloud.devops.commons.pojo.credentials.dto.CredentialDTO;
import org.qubership.cloud.devops.commons.pojo.credentials.dto.SecretCredentialsDTO;
import org.qubership.cloud.devops.commons.repository.interfaces.FileDataConverter;
import org.qubership.cloud.parameters.processor.dto.DeployerInputs;
import org.qubership.cloud.parameters.processor.dto.ParameterBundle;
import org.qubership.cloud.parameters.processor.service.ParametersCalculationService;

import java.io.IOException;
import java.util.HashMap;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

import static org.qubership.cloud.devops.cli.exceptions.constants.ExceptionMessage.APP_PARSE_ERROR;
import static org.qubership.cloud.devops.cli.exceptions.constants.ExceptionMessage.APP_PROCESS_FAILED;
import static org.qubership.cloud.devops.commons.exceptions.constant.ExceptionAdditionalInfoMessages.ENTITY_NOT_FOUND;
import static org.qubership.cloud.devops.commons.exceptions.constant.ExceptionAdditionalInfoMessages.ENTITY_NOT_FOUND_PARAMS;
import static org.qubership.cloud.devops.commons.utils.ConsoleLogger.*;

@Dependent
@Slf4j
public class CliParameterParser {
    private final ParametersCalculationService parametersService;
    private final InputData inputData;
    private final FileDataConverter fileDataConverter;
    private final SharedData sharedData;


    @Inject
    public CliParameterParser(ParametersCalculationService parametersService,
                              InputData inputData,
                              FileDataConverter fileDataConverter,
                              SharedData sharedData) {
        this.parametersService = parametersService;
        this.inputData = inputData;
        this.fileDataConverter = fileDataConverter;
        this.sharedData = sharedData;

    }

    public void generateEffectiveSet() throws IOException, IllegalArgumentException, DirectoryCreateException {
        checkIfEntitiesExist();
        SolutionBomDTO solutionDescriptor = inputData.getSolutionBomDTO();

        List<SBApplicationDTO> applicationDTOList = solutionDescriptor.getApplications();
        String tenantName = inputData.getTenantDTO().getName();
        String cloudName = inputData.getCloudDTO().getName();

        processAndSaveParameters(applicationDTOList, tenantName, cloudName);
    }

    private void processAndSaveParameters(List<SBApplicationDTO> applicationDTOList, String tenantName, String cloudName) throws IOException {
        Map<String, Object> mappingFileData = new ConcurrentHashMap<>();
        Map<String, String> errorList = new ConcurrentHashMap<>();
        Map<String, String> k8TokenMap = new ConcurrentHashMap<>();
        applicationDTOList.parallelStream()
                .forEach(app -> {
                    String namespaceName = app.getNamespace();
                    try {
                        logInfo("Started processing of application: " + app.getAppName() + ":" + app.getAppVersion() + " from the namespace " + namespaceName);
                        generateOutput(tenantName, cloudName, namespaceName, app.getAppName(), app.getAppVersion(), app.getAppFileRef(), k8TokenMap);
                        String deployPostFixDir = String.format("%s/%s/%s/%s", sharedData.getEnvsPath(), sharedData.getEnvId(), "Namespaces", namespaceName);
                        mappingFileData.put(inputData.getNamespaceDTOMap().get(namespaceName).getName(), deployPostFixDir);
                        logInfo("Finished processing of application: " + app.getAppName() + ":" + app.getAppVersion() + " from the namespace " + namespaceName);
                    } catch (Exception e) {
                        log.debug(String.format(APP_PARSE_ERROR, app.getAppName(), namespaceName, e.getMessage()));
                        log.debug("stack trace for further details: ", e);
                        errorList.computeIfAbsent(app.getAppName() + ":" + namespaceName, k -> e.getMessage());
                    }
                });
        if ("v2.0".equalsIgnoreCase(sharedData.getEffectiveSetVersion())) {
            generateE2EOutput(tenantName, cloudName, k8TokenMap);
            fileDataConverter.writeToFile(mappingFileData, sharedData.getOutputDir(), "deployment", "mapping.yaml");
            fileDataConverter.writeToFile(mappingFileData, sharedData.getOutputDir(), "runtime", "mapping.yaml");
        } else {
            fileDataConverter.writeToFile(mappingFileData, sharedData.getOutputDir(), "mapping.yaml");
        }
        if (!errorList.isEmpty()) {
            errorList.forEach((key, value) -> {
                String[] valueSplits = key.split(":");
                logError(String.format(APP_PROCESS_FAILED, valueSplits[0], valueSplits[1], value));
            });
            throw new RuntimeException("Application processing failed");
        }

    }

    public void generateE2EOutput(String tenantName, String cloudName, Map<String, String> k8TokenMap) throws IOException {
        ParameterBundle parameterBundle = parametersService.getCliE2EParameter(tenantName, cloudName);
        parameterBundle.getE2eParams().put("composite_structure", inputData.getCompositeStructureMap());
        parameterBundle.getSecuredE2eParams().put("k8s_tokens", k8TokenMap);
        createE2EFiles(parameterBundle);
        createConsumerFiles(parameterBundle);
    }

    private void createConsumerFiles(ParameterBundle parameterBundle) {
        String pipelineDir = String.format("%s/%s", sharedData.getOutputDir(), "pipeline");
        Map<String, ConsumerDTO> consumerDTOMap = inputData.getConsumerDTOMap();
        consumerDTOMap.forEach((key, value) -> {
            Map<String, Object> consumerParamsMap = new LinkedHashMap<>();
            Map<String, Object> consumersecureMap = new LinkedHashMap<>();
            String parametersFilename = key + "-parameters.yaml";
            String secureFilename = key + "-credentials.yaml";
            value.getProperties().forEach(k -> {
                Object obj = parameterBundle.getE2eParams().get(k.getName());
                if (obj != null) {
                    consumerParamsMap.put(k.getName(), obj);
                } else {
                    obj = parameterBundle.getSecuredE2eParams().get(k.getName());
                    if (obj != null) {
                        consumersecureMap.put(k.getName(), obj);
                    }
                }
                if (obj == null && StringUtils.isNotEmpty(k.getValue())) {
                    consumerParamsMap.put(k.getName(), k.getValue());
                }
                if (obj == null && StringUtils.isEmpty(k.getValue()) && k.isRequired()) {
                    throw new ConsumerFileProcessingException("Property " + k + " is required and no value is defined in E2E configurations");
                }
            });
            try {
                fileDataConverter.writeToFile(consumerParamsMap, pipelineDir, parametersFilename);
                fileDataConverter.writeToFile(consumersecureMap, pipelineDir, secureFilename);
            } catch (IOException e) {
                throw new CreateWorkDirException(e.getMessage());
            }
        });
    }

    private void createE2EFiles(ParameterBundle parameterBundle) throws IOException {
        String pipelineDir = String.format("%s/%s", sharedData.getOutputDir(), "pipeline");
        fileDataConverter.writeToFile(parameterBundle.getE2eParams(), pipelineDir, "parameters.yaml");
        fileDataConverter.writeToFile(parameterBundle.getSecuredE2eParams(), pipelineDir, "credentials.yaml");
    }

    public void generateOutput(String tenantName, String cloudName, String namespaceName, String appName,
                               String appVersion, String appFileRef, Map<String, String> k8TokenMap) throws IOException {
        DeployerInputs deployerInputs = DeployerInputs.builder().appVersion(appVersion).appFileRef(appFileRef).build();
        ParameterBundle parameterBundle = parametersService.getCliParameter(tenantName,
                cloudName,
                namespaceName,
                appName,
                deployerInputs);
        String credentialsId = findDefaultCredentialsId(namespaceName);
        if (StringUtils.isNotEmpty(credentialsId)) {
            CredentialDTO credentialDTO = inputData.getCredentialDTOMap().get(credentialsId);
            if (credentialDTO != null) {
                SecretCredentialsDTO secCred = (SecretCredentialsDTO) credentialDTO.getData();
                k8TokenMap.put(namespaceName, secCred.getSecret());
            }
        }
        createFiles(namespaceName, appName, parameterBundle);
    }

    private String findDefaultCredentialsId(String namespace) {
        return !StringUtils.isEmpty(inputData.getNamespaceDTOMap().get(namespace).getCredentialsId()) ?
                inputData.getNamespaceDTOMap().get(namespace).getCredentialsId() : inputData.getCloudDTO().getDefaultCredentialsId();
    }

    private void createFiles(String namespaceName, String appName, ParameterBundle parameterBundle) throws IOException {
        if ("v2.0".equalsIgnoreCase(sharedData.getEffectiveSetVersion())) {
            String deploymentDir = String.format("%s/%s/%s/%s/%s", sharedData.getOutputDir(), "deployment", namespaceName, appName, "values");
            String runtimeDir = String.format("%s/%s/%s/%s", sharedData.getOutputDir(), "runtime", namespaceName, appName);

            //deployment
            fileDataConverter.writeToFile(parameterBundle.getDeployParams(), deploymentDir, "deployment-parameters.yaml");
            fileDataConverter.writeToFile(parameterBundle.getSecuredDeployParams(), deploymentDir, "credentials.yaml");
            fileDataConverter.writeToFile(new HashMap<>(), deploymentDir, "deploy-descriptor.yaml");

            //runtime parameters
            fileDataConverter.writeToFile(parameterBundle.getConfigServerParams(), runtimeDir, "parameters.yaml");
            fileDataConverter.writeToFile(parameterBundle.getSecuredConfigParams(), runtimeDir, "credentials.yaml");
        } else {
            String appDirectory = String.format("%s/%s/%s", sharedData.getOutputDir(), namespaceName, appName);
            fileDataConverter.writeToFile(parameterBundle.getDeployParams(), appDirectory, "deployment-parameters.yaml");
            fileDataConverter.writeToFile(parameterBundle.getConfigServerParams(), appDirectory, "technical-configuration-parameters.yaml");
            fileDataConverter.writeToFile(parameterBundle.getSecuredDeployParams(), appDirectory, "credentials.yaml");
        }
    }

    private void checkIfEntitiesExist() {
        if (inputData.getSolutionBomDTO() == null) {
            throw new NotFoundException(String.format(ENTITY_NOT_FOUND, "Solution BOM"));
        }
        if (inputData.getTenantDTO() == null) {
            throw new NotFoundException(String.format(ENTITY_NOT_FOUND, "Tenant"));
        }
        if (inputData.getCloudDTO() == null) {
            throw new NotFoundException(String.format(ENTITY_NOT_FOUND, "Cloud"));
        }
        if (inputData.getRegistryDTOMap() == null) {
            logWarning(String.format(ENTITY_NOT_FOUND_PARAMS, "Registry"));
        }
    }


}
