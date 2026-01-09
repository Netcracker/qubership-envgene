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
import org.apache.commons.collections4.MapUtils;
import org.apache.commons.lang3.StringUtils;
import org.apache.commons.lang3.exception.ExceptionUtils;
import org.qubership.cloud.devops.cli.exceptions.DirectoryCreateException;
import org.qubership.cloud.devops.cli.pojo.dto.input.InputData;
import org.qubership.cloud.devops.cli.pojo.dto.sd.SBApplicationDTO;
import org.qubership.cloud.devops.cli.pojo.dto.sd.SolutionBomDTO;
import org.qubership.cloud.devops.cli.pojo.dto.shared.EffectiveSetVersion;
import org.qubership.cloud.devops.cli.pojo.dto.shared.SharedData;
import org.qubership.cloud.devops.cli.utils.FileSystemUtils;
import org.qubership.cloud.devops.commons.Injector;
import org.qubership.cloud.devops.commons.exceptions.ConsumerFileProcessingException;
import org.qubership.cloud.devops.commons.exceptions.CreateWorkDirException;
import org.qubership.cloud.devops.commons.exceptions.NotFoundException;
import org.qubership.cloud.devops.commons.pojo.bg.BgDomainEntityDTO;
import org.qubership.cloud.devops.commons.pojo.consumer.ConsumerDTO;
import org.qubership.cloud.devops.commons.pojo.credentials.dto.CredentialDTO;
import org.qubership.cloud.devops.commons.pojo.credentials.dto.SecretCredentialsDTO;
import org.qubership.cloud.devops.commons.pojo.credentials.model.Credential;
import org.qubership.cloud.devops.commons.pojo.credentials.model.UsernamePasswordCredentials;
import org.qubership.cloud.devops.commons.pojo.namespaces.dto.NamespaceDTO;
import org.qubership.cloud.devops.commons.repository.interfaces.FileDataConverter;
import org.qubership.cloud.devops.commons.utils.CredentialUtils;
import org.qubership.cloud.devops.commons.utils.HelmNameNormalizer;
import org.qubership.cloud.devops.commons.utils.ParameterUtils;
import org.qubership.cloud.devops.commons.utils.Parameter;
import org.qubership.cloud.parameters.processor.dto.DeployerInputs;
import org.qubership.cloud.parameters.processor.dto.ParameterBundle;
import org.qubership.cloud.parameters.processor.service.ParametersCalculationServiceV1;
import org.qubership.cloud.parameters.processor.service.ParametersCalculationServiceV2;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.*;
import java.util.concurrent.ConcurrentHashMap;

import static org.qubership.cloud.devops.cli.exceptions.constants.ExceptionMessage.APP_PARSE_ERROR;
import static org.qubership.cloud.devops.cli.exceptions.constants.ExceptionMessage.APP_PROCESS_FAILED;
import static org.qubership.cloud.devops.commons.exceptions.constant.ExceptionAdditionalInfoMessages.ENTITY_NOT_FOUND;
import static org.qubership.cloud.devops.commons.utils.ConsoleLogger.*;

@Dependent
@Slf4j
public class CliParameterParser {
    private final ParametersCalculationServiceV1 parametersServiceV1;
    private final ParametersCalculationServiceV2 parametersServiceV2;
    private final InputData inputData;
    private final FileDataConverter fileDataConverter;
    private final SharedData sharedData;
    private final FileSystemUtils fileSystemUtils;


    @Inject
    public CliParameterParser(ParametersCalculationServiceV1 parametersServiceV1,
                              ParametersCalculationServiceV2 parametersServiceV2,
                              InputData inputData,
                              FileDataConverter fileDataConverter,
                              SharedData sharedData,
                              FileSystemUtils fileSystemUtils) {
        this.parametersServiceV1 = parametersServiceV1;
        this.parametersServiceV2 = parametersServiceV2;
        this.inputData = inputData;
        this.fileDataConverter = fileDataConverter;
        this.sharedData = sharedData;
        this.fileSystemUtils = fileSystemUtils;

    }

    public void generateEffectiveSet() throws IOException, IllegalArgumentException, DirectoryCreateException {
        checkIfEntitiesExist();
        String tenantName = inputData.getTenantDTO().getName();
        String cloudName = inputData.getCloudDTO().getName();
        Map<String, NamespaceDTO> namespaceDTOMap = inputData.getNamespaceDTOMap();
        processAndSaveParameters(inputData.getSolutionBomDTO(), tenantName, cloudName, namespaceDTOMap);
    }

    private void processAndSaveParameters(Optional<SolutionBomDTO> solutionDescriptor, String tenantName, String cloudName, Map<String,NamespaceDTO> namespaceDTOMap) throws IOException {
        Map<String, Object> deployMappingFileData = new ConcurrentHashMap<>();
        Map<String, Object> runtimeMappingFileData = new ConcurrentHashMap<>();
        Map<String, Object> cleanupMappingFileData = new ConcurrentHashMap<>();
        Map<String, String> errorList = new ConcurrentHashMap<>();
        Map<String, String> k8TokenMap = new ConcurrentHashMap<>();
        namespaceDTOMap.keySet().parallelStream().forEach(namespaceName -> {
            String credentialsId = findDefaultCredentialsId(namespaceName);
            if (StringUtils.isNotEmpty(credentialsId)) {
                CredentialDTO credentialDTO = inputData.getCredentialDTOMap().get(credentialsId);
                if (credentialDTO != null) {
                    SecretCredentialsDTO secCred = (SecretCredentialsDTO) credentialDTO.getData();
                    k8TokenMap.put(namespaceName, secCred.getSecret());
                }
            }
        });
        List<SBApplicationDTO> applicationDTOList = solutionDescriptor.map(SolutionBomDTO::getApplications)
                .orElseGet(Collections::emptyList);
        applicationDTOList.parallelStream()
                .forEach(app -> {
                    String namespaceName = app.getNamespace();
                    try {
                        logInfo("Started processing of application: " + app.getAppName() + ":" + app.getAppVersion() + " from the namespace " + namespaceName);
                        generateOutput(tenantName, cloudName, namespaceName, app.getAppName(), app.getAppVersion(), app.getAppFileRef(), k8TokenMap);
                        String deployPostFixDir = EffectiveSetVersion.V2_0 == sharedData.getEffectiveSetVersion() ? String.format("%s/%s/%s/%s", sharedData.getEnvsPath(), sharedData.getEnvId(), "effective-set/deployment", namespaceName).replace('\\', '/') :
                                String.format("%s/%s/%s/%s", sharedData.getEnvsPath(), sharedData.getEnvId(), "effective-set", namespaceName).replace('\\', '/');
                        String runtimePostFixDir = String.format("%s/%s/%s/%s", sharedData.getEnvsPath(), sharedData.getEnvId(), "effective-set/runtime", namespaceName).replace('\\', '/');
                        String cleanupPostFixDir = String.format("%s/%s/%s/%s", sharedData.getEnvsPath(), sharedData.getEnvId(), "effective-set/cleanup", namespaceName).replace('\\', '/');
                        int index = deployPostFixDir.indexOf("/environments/");
                        if (index != 1) {
                            deployPostFixDir = deployPostFixDir.substring(index);
                        }
                        index = runtimePostFixDir.indexOf("/environments/");
                        if (index != 1) {
                            runtimePostFixDir = runtimePostFixDir.substring(index);
                        }
                        index = cleanupPostFixDir.indexOf("/environments/");
                        if (index != 1) {
                            cleanupPostFixDir = cleanupPostFixDir.substring(index);
                        }
                        deployMappingFileData.put(inputData.getNamespaceDTOMap().get(namespaceName).getName(), deployPostFixDir);
                        runtimeMappingFileData.put(inputData.getNamespaceDTOMap().get(namespaceName).getName(), runtimePostFixDir);
                        cleanupMappingFileData.put(inputData.getNamespaceDTOMap().get(namespaceName).getName(), cleanupPostFixDir);
                        logInfo("Finished processing of application: " + app.getAppName() + ":" + app.getAppVersion() + " from the namespace " + namespaceName);
                    } catch (Exception e) {
                        logDebug(String.format(APP_PARSE_ERROR, app.getAppName(), namespaceName, e.getMessage()));
                        logDebug(String.format("Stack trace for further details: %s", ExceptionUtils.getStackTrace(e)));
                        errorList.computeIfAbsent(app.getAppName() + ":" + namespaceName, k -> e.getMessage());
                    }
                });
        if (EffectiveSetVersion.V2_0 == sharedData.getEffectiveSetVersion()) {
            generateE2EOutput(tenantName, cloudName, k8TokenMap);
            if (solutionDescriptor.isPresent()) {
                fileDataConverter.writeToFile(new TreeMap<>(deployMappingFileData), sharedData.getOutputDir(), "deployment", "mapping.yaml");
                fileDataConverter.writeToFile(new TreeMap<>(runtimeMappingFileData), sharedData.getOutputDir(), "runtime", "mapping.yaml");
                fileDataConverter.writeToFile(new TreeMap<>(cleanupMappingFileData), sharedData.getOutputDir(), "cleanup", "mapping.yaml");
            }
        } else {
            fileDataConverter.writeToFile(new TreeMap<>(deployMappingFileData), sharedData.getOutputDir(), "mapping.yaml");
        }
        if (!errorList.isEmpty()) {
            errorList.forEach((key, value) -> {
                String[] valueSplits = key.split(":");
                logError(String.format(APP_PROCESS_FAILED, valueSplits[0], valueSplits[1], value));
            });
            throw new RuntimeException("Application processing failed");
        }

    }

    private void generateE2EOutput(String tenantName, String cloudName, Map<String, String> k8TokenMap) throws IOException {
        ParameterBundle parameterBundle = parametersServiceV2.getCliE2EParameter(tenantName, cloudName, sharedData.isEnableTraceability());
        if (parameterBundle.getE2eParams() == null) {
            parameterBundle.setE2eParams(new HashMap<>());
        }
        if (parameterBundle.getSecuredE2eParams() == null) {
            parameterBundle.setSecuredE2eParams(new HashMap<>());
        }
        processBgDomainParameters();
        createTopologyFiles(tenantName, cloudName, k8TokenMap);
        createE2EFiles(parameterBundle);
        createPipelineFiles(parameterBundle);
    }

    private void generateCleanupOutput(String tenantName, String cloudName, String namespace, String originalNamespace, Map<String, String> k8TokenMap) throws IOException {
        ParameterBundle parameterBundle = parametersServiceV2.getCleanupParameterBundle(tenantName, cloudName, namespace, null, originalNamespace, k8TokenMap, sharedData.isEnableTraceability());
        if (parameterBundle.getCleanupParameters() == null) {
            parameterBundle.setCleanupParameters(new HashMap<>());
        }
        if (parameterBundle.getCleanupSecureParameters() == null) {
            parameterBundle.setCleanupSecureParameters(new HashMap<>());
        }
        createCleanupFiles(parameterBundle, namespace);
    }

    private void processBgDomainParameters() {
        BgDomainEntityDTO bgDomainEntityDTO = inputData.getBgDomainEntityDTO();
        if (bgDomainEntityDTO != null && bgDomainEntityDTO.getControllerNamespace().getCredentials() != null) {
            CredentialUtils credentialUtils = Injector.getInstance().getDi().get(CredentialUtils.class);
            Credential credentialPojo = credentialUtils.getCredentialsById(bgDomainEntityDTO.getControllerNamespace().getCredentials());
            if (credentialPojo instanceof UsernamePasswordCredentials) {
                UsernamePasswordCredentials usernamePasswordCredentials = (UsernamePasswordCredentials) credentialPojo;
                bgDomainEntityDTO.getControllerNamespace().setUserName(usernamePasswordCredentials.getUsername());
                bgDomainEntityDTO.getControllerNamespace().setPassword(usernamePasswordCredentials.getPassword());
            }
        }
    }

    private void createCleanupFiles(ParameterBundle parameterBundle, String namespace) throws IOException {
        String cleanupDir = String.format("%s/%s/%s", sharedData.getOutputDir(), "cleanup", namespace);
        fileDataConverter.writeToFile(parameterBundle.getCleanupParameters(), cleanupDir, "parameters.yaml");
        fileDataConverter.writeToFile(parameterBundle.getCleanupSecureParameters(), cleanupDir, "credentials.yaml");
    }

    private void createTopologyFiles(String tenantName, String cloudName, Map<String, String> k8TokenMap) throws IOException {
        Map<String, Object> topologyParams = new TreeMap<>();
        Map<String, Object> topologySecuredParams = new TreeMap<>();
        Map<String, Object> clusterParameterMap = getClusterMap();
        
        // Wrap topology values in Parameter objects with origin information for traceability
        boolean enableTraceability = sharedData.isEnableTraceability();
        
        // Construct origin strings with tenant and cloud names
        String cloudOrigin = "Env/Cloud: " + tenantName + "/" + cloudName;
        
        // composite_structure comes from composite_structure.yaml file
        Object compositeStructure = getObjectMap(inputData.getCompositeStructureDTO());
        if (enableTraceability && compositeStructure instanceof Map) {
            topologyParams.put("composite_structure", wrapMapWithOrigin((Map<String, Object>) compositeStructure, "composite-structure"));
        } else {
            topologyParams.put("composite_structure", compositeStructure);
        }
        
        // environments comes from cluster/environments configuration
        Object environments = inputData.getClusterMap();
        if (enableTraceability && environments instanceof Map) {
            topologyParams.put("environments", wrapMapWithOrigin((Map<String, Object>) environments, cloudOrigin));
        } else {
            topologyParams.put("environments", environments);
        }
        
        // cluster comes from cloud.yaml file
        if (enableTraceability && clusterParameterMap != null && !clusterParameterMap.isEmpty()) {
            topologyParams.put("cluster", wrapMapWithOrigin(clusterParameterMap, cloudOrigin));
        } else {
            topologyParams.put("cluster", clusterParameterMap);
        }
        
        // k8s_tokens come from credentials
        if (enableTraceability && k8TokenMap != null && !k8TokenMap.isEmpty()) {
            topologySecuredParams.put("k8s_tokens", wrapMapWithOrigin(new TreeMap<>(k8TokenMap), cloudOrigin));
        } else {
            topologySecuredParams.put("k8s_tokens", k8TokenMap);
        }
        
        Map<String, Object> bgDomainMap = getObjectMap(inputData.getBgDomainEntityDTO());
        Map<String, Object> bgDomainSecureMap = new LinkedHashMap<>();
        Map<String, Object> bgDomainParamsMap = new LinkedHashMap<>();
        ParameterUtils.splitBgDomainParams(bgDomainMap, bgDomainSecureMap, bgDomainParamsMap);
        
        // bg_domain comes from bg-domain.yaml file
        if (enableTraceability) {
            if (bgDomainSecureMap != null && !bgDomainSecureMap.isEmpty()) {
                topologySecuredParams.put("bg_domain", wrapMapWithOrigin(bgDomainSecureMap, "bg-domain"));
            } else {
                topologySecuredParams.put("bg_domain", bgDomainSecureMap);
            }
            if (bgDomainParamsMap != null && !bgDomainParamsMap.isEmpty()) {
                topologyParams.put("bg_domain", wrapMapWithOrigin(bgDomainParamsMap, "bg-domain"));
            } else {
                topologyParams.put("bg_domain", bgDomainParamsMap);
            }
        } else {
            topologySecuredParams.put("bg_domain", bgDomainSecureMap);
            topologyParams.put("bg_domain", bgDomainParamsMap);
        }
        
        String topologyDir = String.format("%s/%s", sharedData.getOutputDir(), "topology");
        fileDataConverter.writeToFile(topologyParams, topologyDir, "parameters.yaml");
        fileDataConverter.writeToFile(topologySecuredParams, topologyDir, "credentials.yaml");

    }

    private <T> Map<String, Object> getObjectMap(T input) {
        return fileDataConverter.getObjectMap(input != null ? input : new HashMap<>());
    }
    
    /**
     * Recursively wraps values in a map with Parameter objects containing origin information.
     * This ensures that nested values also get origin comments in the output YAML.
     */
    private Map<String, Object> wrapMapWithOrigin(Map<String, Object> map, String origin) {
        if (map == null || map.isEmpty()) {
            return map;
        }
        Map<String, Object> wrapped = new TreeMap<>();
        for (Map.Entry<String, Object> entry : map.entrySet()) {
            Object value = entry.getValue();
            if (value instanceof Map) {
                // Recursively wrap nested maps - wrap the map itself, not individual values
                Map<String, Object> nestedMap = (Map<String, Object>) value;
                Map<String, Object> wrappedNested = wrapMapWithOrigin(nestedMap, origin);
                wrapped.put(entry.getKey(), new Parameter(wrappedNested, origin, false));
            } else if (value instanceof List) {
                // Wrap list items
                List<Object> wrappedList = new java.util.ArrayList<>();
                for (Object item : (List<Object>) value) {
                    if (item instanceof Map) {
                        Map<String, Object> wrappedItem = wrapMapWithOrigin((Map<String, Object>) item, origin);
                        wrappedList.add(new Parameter(wrappedItem, origin, false));
                    } else {
                        wrappedList.add(new Parameter(item, origin, false));
                    }
                }
                wrapped.put(entry.getKey(), new Parameter(wrappedList, origin, false));
            } else {
                // Wrap scalar values
                wrapped.put(entry.getKey(), new Parameter(value, origin, false));
            }
        }
        return wrapped;
    }

    private Map<String, Object> getClusterMap() {
        Map<String, Object> clusterParameterMap = new TreeMap<>();
        clusterParameterMap.put("api_url", inputData.getCloudDTO().getApiUrl());
        clusterParameterMap.put("api_port", inputData.getCloudDTO().getApiPort());
        clusterParameterMap.put("public_url", inputData.getCloudDTO().getPublicUrl());
        clusterParameterMap.put("protocol", inputData.getCloudDTO().getProtocol());
        return clusterParameterMap;
    }

    private void createPipelineFiles(ParameterBundle parameterBundle) {
        String pipelineDir = String.format("%s/%s", sharedData.getOutputDir(), "pipeline");
        Map<String, ConsumerDTO> consumerDTOMap = inputData.getConsumerDTOMap();
        boolean enableTraceability = sharedData.isEnableTraceability();
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
                    // Wrap plain values in Parameter objects with origin information for traceability
                    if (enableTraceability) {
                        consumerParamsMap.put(k.getName(), new Parameter(k.getValue(), "envgene pipeline parameter", false));
                    } else {
                        consumerParamsMap.put(k.getName(), k.getValue());
                    }
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
        String originalNamespace = inputData.getNamespaceDTOMap().get(namespaceName).getName();
        String credentialsId = findDefaultCredentialsId(namespaceName);
        if (StringUtils.isNotEmpty(credentialsId)) {
            CredentialDTO credentialDTO = inputData.getCredentialDTOMap().get(credentialsId);
            if (credentialDTO != null) {
                SecretCredentialsDTO secCred = (SecretCredentialsDTO) credentialDTO.getData();
                k8TokenMap.put(originalNamespace, secCred.getSecret());
            }
        }
        ParameterBundle parameterBundle = null;
        if (EffectiveSetVersion.V2_0 == sharedData.getEffectiveSetVersion()) {
            parameterBundle = parametersServiceV2.getCliParameter(tenantName,
                    cloudName,
                    namespaceName,
                    appName,
                    deployerInputs,
                    originalNamespace,
                    k8TokenMap,
                    sharedData.isEnableTraceability());
            generateCleanupOutput(tenantName, cloudName, namespaceName, originalNamespace, k8TokenMap);
        } else {
            parameterBundle = parametersServiceV1.getCliParameter(tenantName,
                    cloudName,
                    namespaceName,
                    appName,
                    deployerInputs,
                    originalNamespace,
                    k8TokenMap,
                    sharedData.isEnableTraceability());

        }
        createFiles(namespaceName, appName, parameterBundle, originalNamespace);
    }

    private String findDefaultCredentialsId(String namespace) {
        return !StringUtils.isEmpty(inputData.getNamespaceDTOMap().get(namespace).getCredentialsId()) ?
                inputData.getNamespaceDTOMap().get(namespace).getCredentialsId() : inputData.getCloudDTO().getDefaultCredentialsId();
    }

    private void createFiles(String namespaceName, String appName, ParameterBundle parameterBundle, String originalNamespace) throws IOException {
        if (EffectiveSetVersion.V2_0 == sharedData.getEffectiveSetVersion()) {
            Path appChartPath = null;
            if (StringUtils.isNotBlank(parameterBundle.getAppChartName())) {
                String normalizedName = HelmNameNormalizer.normalize(parameterBundle.getAppChartName(), originalNamespace);
                appChartPath = fileSystemUtils.getFileFromGivenPath(sharedData.getOutputDir(), "deployment", namespaceName, appName, "values", "per-service-parameters", normalizedName).toPath();
                Files.createDirectories(appChartPath);
            }

            String deploymentDir = String.format("%s/%s/%s/%s/%s", sharedData.getOutputDir(), "deployment", namespaceName, appName, "values");
            String runtimeDir = String.format("%s/%s/%s/%s", sharedData.getOutputDir(), "runtime", namespaceName, appName);

            //deployment
            fileDataConverter.writeToFile(parameterBundle.getDeployParams(), deploymentDir, "deployment-parameters.yaml");
            if (StringUtils.isNotBlank(parameterBundle.getAppChartName())) {
                // For app chart, write per-service params directly - FileDataConverter will extract origins recursively
                // The structure is: { "service1": Parameter(Map(...)), "service2": Parameter(Map(...)) }
                // FileDataConverter.extractOriginMapRecursive will find Parameter objects at all levels
                Map<String, Object> perServiceParams = parameterBundle.getPerServiceParams();
                fileDataConverter.writeToFile(perServiceParams, appChartPath.toString(), "deployment-parameters.yaml");
            }
            fileDataConverter.writeToFile(parameterBundle.getCollisionSecureParameters(), deploymentDir, "collision-credentials.yaml");
            fileDataConverter.writeToFile(parameterBundle.getCollisionDeployParameters(), deploymentDir, "collision-deployment-parameters.yaml");
            if (StringUtils.isBlank(parameterBundle.getAppChartName()) && MapUtils.isNotEmpty(parameterBundle.getPerServiceParams())) {
                parameterBundle.getPerServiceParams().entrySet().stream().forEach(entry -> {
                    try {
                        Path servicePath = fileSystemUtils.getFileFromGivenPath(sharedData.getOutputDir(), "deployment", namespaceName, appName, "values", "per-service-parameters", entry.getKey()).toPath();
                        Files.createDirectories(servicePath);
                        // Extract the service parameters map, handling Parameter objects if present
                        // Pass the value directly - FileDataConverter will handle Parameter objects recursively
                        // If value is a Parameter wrapping a Map, extractOriginMapRecursive will find nested Parameter objects
                        Object value = entry.getValue();
                        Map<String, Object> serviceParams;
                        if (value instanceof Parameter) {
                            // If value is a Parameter object, extract the Map from it
                            // The inner Map should contain Parameter objects for nested values with origins
                            Object paramValue = ((Parameter) value).getValue();
                            if (paramValue instanceof Map) {
                                serviceParams = (Map<String, Object>) paramValue;
                            } else {
                                serviceParams = new TreeMap<>();
                            }
                        } else if (value instanceof Map) {
                            serviceParams = (Map<String, Object>) value;
                        } else {
                            serviceParams = new TreeMap<>();
                        }
                        // Write the service params - FileDataConverter will extract origins from nested Parameter objects
                        fileDataConverter.writeToFile(serviceParams, servicePath.toString(), "deployment-parameters.yaml");
                    } catch (IOException e) {
                        throw new RuntimeException("Failed to write per service parameters of service " + entry.getKey());
                    }
                });
            }
            fileDataConverter.writeToFile(parameterBundle.getSecuredDeployParams(), deploymentDir, "credentials.yaml");
            fileDataConverter.writeToFile(parameterBundle.getDeployDescParams(), deploymentDir, "deploy-descriptor.yaml");

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
        if (inputData.getTenantDTO() == null) {
            throw new NotFoundException(String.format(ENTITY_NOT_FOUND, "Tenant"));
        }
        if (inputData.getCloudDTO() == null) {
            throw new NotFoundException(String.format(ENTITY_NOT_FOUND, "Cloud"));
        }
    }

}
