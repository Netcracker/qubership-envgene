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

package org.qubership.cloud.parameters.processor;

import org.qubership.cloud.devops.commons.utils.Parameter;
import org.qubership.cloud.devops.commons.utils.otel.OpenTelemetryProvider;
import org.qubership.cloud.parameters.processor.dto.DeployerInputs;
import org.qubership.cloud.parameters.processor.dto.Params;
import org.qubership.cloud.parameters.processor.expression.ExpressionLanguage;
import org.qubership.cloud.parameters.processor.expression.Language;
import org.qubership.cloud.parameters.processor.expression.binding.Binding;
import jakarta.inject.Inject;
import jakarta.inject.Singleton;
import org.qubership.cloud.parameters.processor.expression.binding.CredentialsMap;

import java.io.Serializable;
import java.util.*;
import java.util.stream.Collectors;


@Singleton
public class ParametersProcessor implements Serializable {
    private static final long serialVersionUID = -5461238892186020722L;
    private final OpenTelemetryProvider openTelemetryProvider;

    @Inject
    public ParametersProcessor(OpenTelemetryProvider openTelemetryProvider) {
        this.openTelemetryProvider = openTelemetryProvider;
    }

    public Params processAllParameters(String tenant, String cloud, String namespace, String application, String defaultEscapeSequence, DeployerInputs deployerInputs, String originalNamespace) {
        return openTelemetryProvider.withSpan("process", () -> {
            Binding binding = new Binding(deployerInputs).init(tenant, cloud, namespace, application, originalNamespace);
            Language lang;
            lang = new ExpressionLanguage(binding);
            Map<String, Parameter> deploy = lang.processDeployment();
            Map<String, Parameter> tech = lang.processConfigServerApp();
            binding.additionalParameters(deploy);
            return Params.builder().deployParams(deploy).techParams(tech).build();
        });
    }

    public Params processE2EParameters(String tenant, String cloud, String namespace, String application, String defaultEscapeSequence, DeployerInputs deployerInputs, String originalNamespace) {
        return openTelemetryProvider.withSpan("process", () -> {
            Binding binding = new Binding(deployerInputs).init(tenant, cloud, namespace, application, originalNamespace);
            Language lang;
            lang = new ExpressionLanguage(binding);
            Map<String, Parameter> e2e = lang.processCloudE2E();
            return Params.builder().e2eParams(e2e).build();
        });
    }

    public Params processNamespaceParameters(String tenant, String cloud, String namespace, String defaultEscapeSequence, DeployerInputs deployerInputs, String originalNamespace) {
        return openTelemetryProvider.withSpan("process", () -> {
            Binding binding = new Binding(deployerInputs).init(tenant, cloud, namespace, null, originalNamespace);
            Language lang;
            lang = new ExpressionLanguage(binding);
            Map<String, Parameter> namespaceParams = lang.processNamespace();
            binding.additionalParameters(namespaceParams);
            return Params.builder().cleanupParams(namespaceParams).build();
        });
    }

    public Map<String, Parameter> processParameters(Map<String, String> parameters) {
        return openTelemetryProvider.withSpan("process", () -> {
            Binding binding = new Binding();
            binding.put("creds", new Parameter(new CredentialsMap(binding).init()));
            Language lang;
            lang = new ExpressionLanguage(binding);
            return lang.processParameters(parameters);
        });
    }

    private static Object convertParameterToObject(Object value) {
        if (value instanceof Parameter) {
            value = ((Parameter) value).getValue();
        }
        if (value instanceof Map) {
            value = convertParameterMapToObject((Map) value);
        } else if (value instanceof List) {
            value = convertParameterListToObject((List) value);
        }
        return value;
    }

    private static List<Object> convertParameterListToObject(List<Parameter> list) {
        return list.stream()
                .map(ParametersProcessor::convertParameterToObject)
                .collect(Collectors.toList());
    }

    public static Map<String, Object> convertParameterMapToObject(Map<String, ?> map) {
        return map.entrySet().stream()
                .map(entry -> {
                    if (entry.getValue() instanceof Parameter) {
                        return new AbstractMap.SimpleEntry<>(entry.getKey(), ((Parameter) entry.getValue()).getValue());
                    } else {
                        return new AbstractMap.SimpleEntry<>(entry.getKey(), entry.getValue());
                    }
                })
                .collect(TreeMap::new, (m, v) -> m.put(v.getKey(), convertParameterToObject(v.getValue())), TreeMap::putAll);
    }
}
