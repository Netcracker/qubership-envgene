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
                                           DeployerInputs deployerInputs) {
        return getParameterBundle(tenantName, cloudName, namespaceName, applicationName, deployerInputs);
    }

    public ParameterBundle getCliE2EParameter(String tenantName, String cloudName) {
        return getE2EParameterBundle(tenantName, cloudName);
    }

    private ParameterBundle getParameterBundle(String tenantName, String cloudName, String namespaceName, String applicationName, DeployerInputs deployerInputs) {
        Params parameters = parametersProcessor.processAllParameters(tenantName,
                cloudName,
                namespaceName,
                applicationName,
                "false",
                deployerInputs);


        ParameterBundle parameterBundle = ParameterBundle.builder().build();
        prepareSecureInsecureParams(parameters.getDeployParams(), parameterBundle, ParameterType.DEPLOY);
        prepareSecureInsecureParams(parameters.getTechParams(), parameterBundle, ParameterType.TECHNICAL);
        return parameterBundle;
    }

    private ParameterBundle getE2EParameterBundle(String tenantName, String cloudName) {
        Params parameters = parametersProcessor.processE2EParameters(tenantName, cloudName, null, null, "false", null);
        ParameterBundle parameterBundle = ParameterBundle.builder().build();
        prepareSecureInsecureParams(parameters.getE2eParams(), parameterBundle, ParameterType.E2E);
        return parameterBundle;
    }

    public void prepareSecureInsecureParams(Map<String, Parameter> parameters, ParameterBundle parameterBundle, ParameterType parameterType) {
        Map<String, Parameter> securedParams = new TreeMap<>();
        Map<String, Parameter> inSecuredParams = new TreeMap<>();
        if (parameters == null || parameters.isEmpty()) {
            LOGGER.warn("No Parameters found. Check if the input values are correct");
            return;
        }
        filterSecuredParams(parameters, securedParams, inSecuredParams);

        Map<String, Object> finalSecuredParams = ParametersProcessor.convertParameterMapToObject(securedParams);
        Map<String, Object> inSecuredParamsAsObject = ParametersProcessor.convertParameterMapToObject(inSecuredParams);
        if (parameterType == ParameterType.E2E) {
            parameterBundle.setSecuredE2eParams(finalSecuredParams);
            parameterBundle.setE2eParams(inSecuredParamsAsObject);
        } else if (parameterType == ParameterType.DEPLOY) {
            Map<String, Object> finalInsecureParams = prepareFinalParams(inSecuredParamsAsObject);
            parameterBundle.setSecuredDeployParams(finalSecuredParams);
            parameterBundle.setDeployParams(finalInsecureParams);
        } else if (parameterType == ParameterType.TECHNICAL) {
            parameterBundle.setSecuredConfigParams(finalSecuredParams);
            parameterBundle.setConfigServerParams(inSecuredParamsAsObject);
        }
    }

    private Map<String, Object> prepareFinalParams(Map<String, Object> parameters) {
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
        finalMap.forEach((key, value) -> {
            if (value instanceof Map) {
                Map<String, Object> valueMap = (Map<String, Object>) value;
                valueMap.put("!merge", sortedMap);
                Map<String, Object> sortedValueMap = new TreeMap<>(valueMap);
                finalMap.put(key, sortedValueMap);
            }
        });
        orderedMap.putAll(finalMap);
        return orderedMap;
    }

    private void filterSecuredParams(Map<String, Parameter> map, Map<String, Parameter> securedParams, Map<String, Parameter> inSecuredParams) {
        for (Map.Entry<String, Parameter> entry : map.entrySet()) {
            if (!entities.contains(entry.getKey()) && containsSecuredParams(entry.getValue())) {
                securedParams.put(entry.getKey(), entry.getValue());
            } else {
                inSecuredParams.put(entry.getKey(), entry.getValue());
            }
        }
    }

    private boolean containsSecuredParams(Parameter parameter) {
        if (parameter.isSecured()) {
            return true;
        }

        Object params = parameter.getValue();
        if (params instanceof Map) {
            return ((Map<String, Parameter>) params).values().stream().anyMatch(this::containsSecuredParams);
        } else if (params instanceof List) {
            return ((List<Parameter>) params).stream().anyMatch(this::containsSecuredParams);
        }

        return false;
    }
}
