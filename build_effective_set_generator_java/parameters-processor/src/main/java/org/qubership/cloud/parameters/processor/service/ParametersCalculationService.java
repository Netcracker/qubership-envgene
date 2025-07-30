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

package org.qubership.cloud.parameters.processor.service;

import jakarta.enterprise.context.ApplicationScoped;
import jakarta.inject.Inject;
import org.apache.commons.collections4.MapUtils;
import org.qubership.cloud.devops.commons.utils.ParameterUtils;
import org.qubership.cloud.devops.commons.utils.Parameter;
import org.qubership.cloud.parameters.processor.ParametersProcessor;
import org.qubership.cloud.parameters.processor.dto.DeployerInputs;
import org.qubership.cloud.parameters.processor.dto.ParameterBundle;
import org.qubership.cloud.parameters.processor.dto.ParameterType;
import org.qubership.cloud.parameters.processor.dto.Params;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.util.*;

import static org.qubership.cloud.devops.commons.utils.constant.ApplicationConstants.*;

@ApplicationScoped
public class ParametersCalculationService {
    public static final Logger LOGGER = LoggerFactory.getLogger(ParametersCalculationService.class.getName());
    private final ParametersProcessor parametersProcessor;
    private final List<String> entities = Arrays.asList(SERVICES, CONFIGURATIONS, FRONTENDS, SMARTPLUG, CDN, SAMPLREPO);

    @Inject
    public ParametersCalculationService(ParametersProcessor parametersProcessor) {
        this.parametersProcessor = parametersProcessor;
    }

    public ParameterBundle getCliParameter(String tenantName, String cloudName, String namespaceName, String applicationName,
                                           DeployerInputs deployerInputs, String originalNamespace, Map<String, String> k8TokenMap) {
        return getParameterBundle(tenantName, cloudName, namespaceName, applicationName, deployerInputs, originalNamespace, k8TokenMap);
    }

    public ParameterBundle getCliE2EParameter(String tenantName, String cloudName) {
        return getE2EParameterBundle(tenantName, cloudName);
    }

    public ParameterBundle getCleanupParameterBundle(String tenantName, String cloudName, String namespaceName,
                                                     DeployerInputs deployerInputs, String originalNamespace,
                                                     Map<String, String> k8TokenMap) {
        Params parameters = parametersProcessor.processNamespaceParameters(tenantName,
                cloudName,
                namespaceName,
                "false",
                deployerInputs,
                originalNamespace);


        ParameterBundle parameterBundle = ParameterBundle.builder().build();
        prepareSecureInsecureParams(parameters.getCleanupParams(), parameterBundle, ParameterType.CLEANUP, k8TokenMap, originalNamespace);
        return parameterBundle;
    }

    private ParameterBundle getParameterBundle(String tenantName, String cloudName, String namespaceName, String applicationName,
                                               DeployerInputs deployerInputs, String originalNamespace, Map<String, String> k8TokenMap) {
        Params parameters = parametersProcessor.processAllParameters(tenantName,
                cloudName,
                namespaceName,
                applicationName,
                "false",
                deployerInputs,
                originalNamespace);


        ParameterBundle parameterBundle = ParameterBundle.builder().build();
        if (MapUtils.isNotEmpty(parameters.getDeployParams()) && parameters.getDeployParams().containsKey(PER_SERVICE_DEPLOY_PARAMS)) {
            processPerServiceParams(parameters, parameterBundle);
        }
        if (MapUtils.isNotEmpty(parameters.getDeployParams()) && parameters.getDeployParams().containsKey(DEPLOY_DESC)) {
            processDeploymentDescriptorParams(parameters, parameterBundle);
        }
        prepareSecureInsecureParams(parameters.getDeployParams(), parameterBundle, ParameterType.DEPLOY, k8TokenMap, originalNamespace);
        prepareSecureInsecureParams(parameters.getTechParams(), parameterBundle, ParameterType.TECHNICAL, k8TokenMap, originalNamespace);
        return parameterBundle;
    }

    private static void processPerServiceParams(Params parameters, ParameterBundle parameterBundle) {
        Parameter parameter = parameters.getDeployParams().get(PER_SERVICE_DEPLOY_PARAMS);
        if (parameter.getValue() == null) {
            parameters.getDeployParams().remove(PER_SERVICE_DEPLOY_PARAMS);
            parameterBundle.setPerServiceParams(new HashMap<>());
            return;
        }
        parameterBundle.setProcessPerServiceParams(true);
        Map<String, Object> perServiceParams = ParametersProcessor.convertParameterMapToObject((Map<String, Object>) parameter.getValue());

        parameterBundle.setPerServiceParams(perServiceParams);
        parameters.getDeployParams().remove(PER_SERVICE_DEPLOY_PARAMS);
    }

    private static void processDeploymentDescriptorParams(Params parameters, ParameterBundle parameterBundle) {
        Parameter commParameter = parameters.getDeployParams().get(COMMON_DEPLOY_DESC);
        if (commParameter.getValue() == null) {
            parameters.getDeployParams().remove(COMMON_DEPLOY_DESC);
            parameters.getDeployParams().remove(DEPLOY_DESC);
            parameterBundle.setDeployDescParams(new HashMap<>());
            return;
        }
        Parameter parameter = parameters.getDeployParams().get(DEPLOY_DESC);
        if (parameter.getValue() == null) {
            parameters.getDeployParams().remove(DEPLOY_DESC);
        }
        Map<String, Object> finalDeployDescMap = new LinkedHashMap<>();
        Map<String, Object> deployDescParams = ParametersProcessor.convertParameterMapToObject((Map<String, Object>) parameter.getValue());


        Map<String, Object> commonParamMap = new LinkedHashMap<>();
        Map<String, Object> commonDepDescMap = ParametersProcessor.convertParameterMapToObject((Map<String, Object>) commParameter.getValue());
        commonDepDescMap.entrySet().stream().forEach(entry -> commonParamMap.putAll((Map<String, Object>) entry.getValue()));

        Map<String, Object> deployDescParamMap = new LinkedHashMap<>();
        deployDescParamMap.put("deployDescriptor", deployDescParams);

        Map<String, Object> globalMap = new HashMap<>();
        globalMap.put("global", deployDescParamMap);
        globalMap.entrySet().stream().forEach(entry -> finalDeployDescMap.put(entry.getKey(), entry.getValue()));

        Map<String, Object> serviceParamsMap = new LinkedHashMap<>();
        commonParamMap.entrySet().stream().forEach(entry -> serviceParamsMap.put(entry.getKey(), entry.getValue()));
        serviceParamsMap.put("deployDescriptor", deployDescParamMap.get("deployDescriptor"));
        serviceParamsMap.put("global", finalDeployDescMap.get("global"));

        deployDescParamMap.entrySet().stream().forEach(entry -> finalDeployDescMap.put(entry.getKey(), entry.getValue()));
        deployDescParams.entrySet().stream().forEach(entry -> finalDeployDescMap.put(entry.getKey(), serviceParamsMap));
        commonParamMap.entrySet().stream().forEach(entry -> finalDeployDescMap.put(entry.getKey(), entry.getValue()));


        parameterBundle.setDeployDescParams(finalDeployDescMap);
        parameters.getDeployParams().remove(DEPLOY_DESC);
        parameters.getDeployParams().remove(COMMON_DEPLOY_DESC);
    }

    private ParameterBundle getE2EParameterBundle(String tenantName, String cloudName) {
        Params parameters = parametersProcessor.processE2EParameters(tenantName, cloudName, null, null, "false", null, null);
        ParameterBundle parameterBundle = ParameterBundle.builder().build();
        prepareSecureInsecureParams(parameters.getE2eParams(), parameterBundle, ParameterType.E2E, null, null);
        return parameterBundle;
    }

    public void prepareSecureInsecureParams(Map<String, Parameter> parameters, ParameterBundle parameterBundle
            , ParameterType parameterType, Map<String, String> k8TokenMap, String originalNamespace) {
        Map<String, Parameter> securedParams = new TreeMap<>();
        Map<String, Parameter> inSecuredParams = new TreeMap<>();
        if (parameters == null || parameters.isEmpty()) {
            LOGGER.debug("No Parameters found. Check if the input values are correct");
            return;
        }
        filterSecuredParams(parameters, securedParams, inSecuredParams, parameterType);

        Map<String, Object> finalSecuredParams = ParametersProcessor.convertParameterMapToObject(securedParams);
        Map<String, Object> inSecuredParamsAsObject = ParametersProcessor.convertParameterMapToObject(inSecuredParams);
        parseBooleanParams(finalSecuredParams);
        parseBooleanParams(inSecuredParamsAsObject);
        if (parameterType == ParameterType.E2E) {
            parameterBundle.setSecuredE2eParams(finalSecuredParams);
            parameterBundle.setE2eParams(inSecuredParamsAsObject);
        } else if (parameterType == ParameterType.DEPLOY) {
            Object appChartName = inSecuredParamsAsObject.get(APPR_CHART_NAME);
            parameterBundle.setAppChartName(appChartName != null ? appChartName.toString() : "");
            inSecuredParamsAsObject.remove(APPR_CHART_NAME); //remove app chart name from parameters once after the usage
            parameterBundle.setCollisionDeployParameters(getCollisionParams(inSecuredParamsAsObject));
            parameterBundle.setCollisionSecureParameters(getCollisionParams(finalSecuredParams));
            copyParams(finalSecuredParams, inSecuredParamsAsObject, k8TokenMap, originalNamespace);
            Map<String, Object> finalInsecureParams = prepareFinalParams(inSecuredParamsAsObject, parameterBundle.isProcessPerServiceParams());
            Map<String, Object> finalSecParams = prepareFinalParams(finalSecuredParams, true);
            parameterBundle.setSecuredDeployParams(finalSecParams);
            parameterBundle.setDeployParams(finalInsecureParams);
        } else if (parameterType == ParameterType.TECHNICAL) {
            parameterBundle.setSecuredConfigParams(finalSecuredParams);
            parameterBundle.setConfigServerParams(inSecuredParamsAsObject);
        } else if (parameterType == ParameterType.CLEANUP) {
            finalSecuredParams.put(K8S_TOKEN, k8TokenMap.get(originalNamespace));
            parameterBundle.setCleanupSecureParameters(finalSecuredParams);
            parameterBundle.setCleanupParameters(inSecuredParamsAsObject);
        }
    }

    private void copyParams(Map<String, Object> finalSecParams, Map<String, Object> finalInsecureParams,
                            Map<String, String> k8TokenMap, String originalNamespace) {
        SECURED_KEYS.stream()
                .filter(finalInsecureParams::containsKey)
                .forEach(key -> {
                    finalSecParams.put(key, finalInsecureParams.get(key));
                    finalInsecureParams.remove(key);
                });
        finalSecParams.put(K8S_TOKEN, k8TokenMap.get(originalNamespace));
    }

    private Map<String, Object> getCollisionParams(Map<String, Object> parameters) {
        Map<String, Object> serviceMap = new LinkedHashMap<>();
        Map<String, Object> collisionParams = new LinkedHashMap<>();
        if (parameters.containsKey(SERVICES)) {
            serviceMap = (Map<String, Object>) parameters.get(SERVICES);
        }
        Set<String> services = serviceMap.keySet();
        parameters.entrySet().forEach(entry -> {
            if (services.contains(entry.getKey()) && !entities.contains(entry.getKey())) {
                collisionParams.put(entry.getKey(), entry.getValue());
            }
        });
        return collisionParams;
    }

    private Map<String, Object> prepareFinalParams(Map<String, Object> parameters, boolean processPerServiceParams) {
        Map<String, Object> finalMap = new LinkedHashMap<>();
        Map<String, Object> orderedMap = new LinkedHashMap<>();

        entities.stream()
                .map(key -> (Map<String, Object>) parameters.remove(key))
                .filter(Objects::nonNull)
                .forEach(finalMap::putAll);
        Map<String, Object> sortedMap = new TreeMap<>(parameters);
        orderedMap.putAll(sortedMap);
        if (parameters != null && !parameters.isEmpty()) {
            orderedMap.put("global", sortedMap);
        }
        if (processPerServiceParams) {
            finalMap.forEach((key, value) -> {
                if (value instanceof Map) {
                    finalMap.put(key, sortedMap);
                }
            });
        } else {
            finalMap.forEach((key, value) -> {
                if (value instanceof Map) {
                    Map<String, Object> valueMap = (Map<String, Object>) value;
                    valueMap.put("!merge", sortedMap);
                    Map<String, Object> sortedValueMap = new TreeMap<>(valueMap);
                    finalMap.put(key, sortedValueMap);
                }
            });
        }
        orderedMap.putAll(finalMap);
        return orderedMap;
    }

    private void parseBooleanParams(Map<String, Object> orderedMap) {
        orderedMap.entrySet().stream().forEach(entry -> {
            if (entry.getValue() instanceof String) {
                String text = entry.getValue().toString();
                boolean isBooleanString = text.equalsIgnoreCase("true") || text.equalsIgnoreCase("false");
                if (isBooleanString) {
                    entry.setValue(Boolean.parseBoolean(text));
                }
            }
        });
    }

    private void filterSecuredParams(Map<String, Parameter> map, Map<String, Parameter> securedParams, Map<String, Parameter> inSecuredParams, ParameterType parameterType) {
        ParameterUtils.splitBySecure(map, securedParams, inSecuredParams);
        for (Map.Entry<String, Parameter> entry : map.entrySet()) {
            if (parameterType == ParameterType.DEPLOY && entities.contains(entry.getKey())) {
                securedParams.put(entry.getKey(), entry.getValue());
            }
            if (entities.contains(entry.getKey())) {
                inSecuredParams.put(entry.getKey(), entry.getValue());
            }
        }
    }
}
