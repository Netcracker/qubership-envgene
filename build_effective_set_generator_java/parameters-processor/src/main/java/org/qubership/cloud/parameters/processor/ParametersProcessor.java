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
import org.qubership.cloud.parameters.processor.expression.PlainLanguage;
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
            Binding binding = new Binding(defaultEscapeSequence, deployerInputs).init(tenant, cloud, namespace, application, originalNamespace);
            Language lang;
            if (binding.getProcessorType().equals("true")) {
                lang = new ExpressionLanguage(binding);
            } else {
                lang = new PlainLanguage(binding);
            }

            Map<String, Parameter> deploy = lang.processDeployment();
            Map<String, Parameter> tech = lang.processConfigServerApp();
            binding.additionalParameters(deploy);
            return Params.builder().deployParams(deploy).techParams(tech).build();
        });
    }

    public Params processE2EParameters(String tenant, String cloud, String namespace, String application, String defaultEscapeSequence, DeployerInputs deployerInputs, String originalNamespace) {
        return openTelemetryProvider.withSpan("process", () -> {
            Binding binding = new Binding(defaultEscapeSequence, deployerInputs).init(tenant, cloud, namespace, application, originalNamespace);
            Language lang;
            if (binding.getProcessorType().equals("true")) {
                lang = new ExpressionLanguage(binding);
            } else {
                lang = new PlainLanguage(binding);
            }

            Map<String, Parameter> e2e = lang.processCloudE2E();
            return Params.builder().e2eParams(e2e).build();
        });
    }

    public Params processNamespaceParameters(String tenant, String cloud, String namespace, String defaultEscapeSequence, DeployerInputs deployerInputs, String originalNamespace) {
        return openTelemetryProvider.withSpan("process", () -> {
            Binding binding = new Binding(defaultEscapeSequence, deployerInputs).init(tenant, cloud, namespace, null, originalNamespace);
            Language lang;
            if (binding.getProcessorType().equals("true")) {
                lang = new ExpressionLanguage(binding);
            } else {
                lang = new PlainLanguage(binding);
            }

            Map<String, Parameter> namespaceParams = lang.processNamespace();
            binding.additionalParameters(namespaceParams);
            return Params.builder().cleanupParams(namespaceParams).build();
        });
    }

    public Map<String, Parameter> processParameters(Map<String, String> parameters) {
        return openTelemetryProvider.withSpan("process", () -> {
            Binding binding = new Binding("true");
            binding.put("creds", new Parameter(new CredentialsMap(binding).init()));
            Language lang;
            if (binding.getProcessorType().equals("true")) {
                lang = new ExpressionLanguage(binding);
            } else {
                lang = new PlainLanguage(binding);
            }

            return lang.processParameters(parameters);
        });
    }

    private static Object convertParameterToObject(Object value, String origin, boolean enableTraceability) {
        if (value instanceof Parameter) {
            Parameter param = (Parameter) value;
            String paramOrigin = param.getOrigin();
            // Use the parameter's origin if available, otherwise use the passed origin
            origin = (paramOrigin != null && !paramOrigin.isEmpty()) ? paramOrigin : origin;
            value = param.getValue();
        }
        if (value instanceof Map) {
            value = convertParameterMapToObject((Map) value, origin, enableTraceability);
        } else if (value instanceof List) {
            value = convertParameterListToObject((List) value, origin, enableTraceability);
        }
        return value;
    }

    private static Object convertParameterToObject(Object value) {
        return convertParameterToObject(value, null, false);
    }

    private static List<Object> convertParameterListToObject(List<Parameter> list, String parentOrigin, boolean enableTraceability) {
        return list.stream()
                .map(param -> convertParameterToObject(param, parentOrigin, enableTraceability))
                .collect(Collectors.toList());
    }

    private static List<Object> convertParameterListToObject(List<Parameter> list) {
        return convertParameterListToObject(list, null, false);
    }

    public static Map<String, Object> convertParameterMapToObject(Map<String, ?> map) {
        return convertParameterMapToObject(map, null, false);
    }

    public static Map<String, Object> convertParameterMapToObject(Map<String, ?> map, String parentOrigin) {
        return convertParameterMapToObject(map, parentOrigin, false);
    }

    /**
     * Unwraps Parameter objects from a map, returning a map with unwrapped values.
     * This is needed when the map needs to be processed further before serialization.
     * Also extracts and returns a map of key paths to origins for later re-wrapping.
     * Uses Parameter class origin field instead of ValueWithOrigin wrapper.
     */
    public static Map<String, Object> unwrapParameterMap(Map<String, Object> map) {
        return unwrapParameterMap(map, null);
    }
    
    /**
     * Unwraps Parameter objects from a map, returning a map with unwrapped values.
     * If originMap is provided, it will be populated with key paths to origins.
     * Tracks nested paths using dot notation (e.g., "services.service1.key") to handle
     * cases where nested structures are spread during processing.
     * Uses Parameter class origin field instead of ValueWithOrigin wrapper.
     */
    public static Map<String, Object> unwrapParameterMap(Map<String, Object> map, Map<String, String> originMap) {
        if (map == null) {
            return null;
        }
        return unwrapParameterMapRecursive(map, originMap, "");
    }
    
    /**
     * Recursively unwraps Parameter objects from a map, tracking nested paths for origin information.
     * 
     * @param map The map to unwrap
     * @param originMap Map to populate with path-to-origin mappings (can be null)
     * @param pathPrefix Current path prefix for nested structures (empty string for root level)
     * @return Unwrapped map
     */
    private static Map<String, Object> unwrapParameterMapRecursive(Map<String, Object> map, Map<String, String> originMap, String pathPrefix) {
        if (map == null) {
            return null;
        }
        Map<String, Object> unwrapped = new TreeMap<>();
        for (Map.Entry<String, Object> entry : map.entrySet()) {
            String key = entry.getKey();
            Object value = entry.getValue();
            String currentPath = pathPrefix.isEmpty() ? key : pathPrefix + "." + key;
            
            if (value instanceof Parameter) {
                Parameter param = (Parameter) value;
                if (originMap != null && param.getOrigin() != null && !param.getOrigin().isEmpty()) {
                    // Store origin for both the full path and the direct key (for spread scenarios)
                    originMap.put(currentPath, param.getOrigin());
                    originMap.put(key, param.getOrigin());
                }
                Object unwrappedValue = param.getValue();
                unwrapped.put(key, unwrapValueRecursive(unwrappedValue, originMap, currentPath));
            } else {
                unwrapped.put(key, unwrapValueRecursive(value, originMap, currentPath));
            }
        }
        return unwrapped;
    }
    
    /**
     * Re-wraps values in a map with origin information from the origin map using Parameter objects.
     * Handles both direct keys and nested paths to support cases where nested structures were spread.
     * Uses Parameter class origin field instead of ValueWithOrigin wrapper.
     */
    public static Map<String, Object> rewrapWithOrigin(Map<String, Object> map, Map<String, String> originMap) {
        if (map == null || originMap == null || originMap.isEmpty()) {
            return map;
        }
        return rewrapWithOriginRecursive(map, originMap, "");
    }
    
    /**
     * Recursively re-wraps values in a map with origin information, handling nested structures.
     * 
     * @param map The map to re-wrap
     * @param originMap Map containing path-to-origin mappings
     * @param pathPrefix Current path prefix for nested structures (empty string for root level)
     * @return Re-wrapped map with Parameter objects containing origin information
     */
    private static Map<String, Object> rewrapWithOriginRecursive(Map<String, Object> map, Map<String, String> originMap, String pathPrefix) {
        if (map == null || originMap == null || originMap.isEmpty()) {
            return map;
        }
        Map<String, Object> rewrapped = new TreeMap<>();
        for (Map.Entry<String, Object> entry : map.entrySet()) {
            String key = entry.getKey();
            String currentPath = pathPrefix.isEmpty() ? key : pathPrefix + "." + key;
            Object value = entry.getValue();
            
            // Check for origin using both the current path and the direct key
            // This handles cases where nested structures were spread (e.g., "services.service1" -> "service1")
            String origin = originMap.get(currentPath);
            if (origin == null || origin.isEmpty()) {
                origin = originMap.get(key);
            }
            
            if (origin != null && !origin.isEmpty()) {
                // If value is a map or list, recursively process it
                if (value instanceof Map) {
                    Map<String, Object> nestedMap = (Map<String, Object>) value;
                    Map<String, Object> rewrappedNested = rewrapWithOriginRecursive(nestedMap, originMap, currentPath);
                    rewrapped.put(key, new Parameter(rewrappedNested, origin, false));
                } else if (value instanceof List) {
                    List<Object> rewrappedList = rewrapListWithOrigin((List<Object>) value, originMap, currentPath);
                    rewrapped.put(key, new Parameter(rewrappedList, origin, false));
                } else {
                    rewrapped.put(key, new Parameter(value, origin, false));
                }
            } else {
                // No origin found, but still need to recursively process nested structures
                if (value instanceof Map) {
                    Map<String, Object> nestedMap = (Map<String, Object>) value;
                    rewrapped.put(key, rewrapWithOriginRecursive(nestedMap, originMap, currentPath));
                } else if (value instanceof List) {
                    rewrapped.put(key, rewrapListWithOrigin((List<Object>) value, originMap, currentPath));
                } else {
                    rewrapped.put(key, value);
                }
            }
        }
        return rewrapped;
    }
    
    /**
     * Recursively re-wraps list elements with origin information.
     */
    private static List<Object> rewrapListWithOrigin(List<Object> list, Map<String, String> originMap, String pathPrefix) {
        if (list == null) {
            return null;
        }
        List<Object> rewrapped = new ArrayList<>();
        for (int i = 0; i < list.size(); i++) {
            Object item = list.get(i);
            String itemPath = pathPrefix + "[" + i + "]";
            
            if (item instanceof Map) {
                Map<String, Object> nestedMap = (Map<String, Object>) item;
                String origin = originMap.get(itemPath);
                if (origin != null && !origin.isEmpty()) {
                    Map<String, Object> rewrappedNested = rewrapWithOriginRecursive(nestedMap, originMap, itemPath);
                    rewrapped.add(new Parameter(rewrappedNested, origin, false));
                } else {
                    rewrapped.add(rewrapWithOriginRecursive(nestedMap, originMap, itemPath));
                }
            } else if (item instanceof List) {
                rewrapped.add(rewrapListWithOrigin((List<Object>) item, originMap, itemPath));
            } else {
                String origin = originMap.get(itemPath);
                if (origin != null && !origin.isEmpty()) {
                    rewrapped.add(new Parameter(item, origin, false));
                } else {
                    rewrapped.add(item);
                }
            }
        }
        return rewrapped;
    }
    
    /**
     * Unwraps a value, removing Parameter wrappers recursively.
     * This version does not track origins (used when originMap is null).
     */
    private static Object unwrapValue(Object value) {
        if (value == null) {
            return null;
        }
        if (value instanceof Parameter) {
            return unwrapValue(((Parameter) value).getValue());
        } else if (value instanceof Map) {
            Map<String, Object> map = (Map<String, Object>) value;
            Map<String, Object> unwrapped = new TreeMap<>();
            for (Map.Entry<String, Object> entry : map.entrySet()) {
                unwrapped.put(entry.getKey(), unwrapValue(entry.getValue()));
            }
            return unwrapped;
        } else if (value instanceof List) {
            List<Object> list = (List<Object>) value;
            List<Object> unwrapped = new ArrayList<>();
            for (Object item : list) {
                unwrapped.add(unwrapValue(item));
            }
            return unwrapped;
        }
        return value;
    }
    
    /**
     * Recursively unwraps a value while tracking origin information for nested structures.
     * 
     * @param value The value to unwrap
     * @param originMap Map to populate with path-to-origin mappings (can be null)
     * @param pathPrefix Current path prefix for nested structures
     * @return Unwrapped value
     */
    private static Object unwrapValueRecursive(Object value, Map<String, String> originMap, String pathPrefix) {
        if (value == null) {
            return null;
        }
        if (value instanceof Parameter) {
            Parameter param = (Parameter) value;
            if (originMap != null && param.getOrigin() != null && !param.getOrigin().isEmpty()) {
                originMap.put(pathPrefix, param.getOrigin());
                // Also store at the direct key level if this is a nested path (for spread scenarios)
                // Extract the last key from the path (e.g., "services.service1" -> "service1")
                if (pathPrefix.contains(".")) {
                    String directKey = pathPrefix.substring(pathPrefix.lastIndexOf('.') + 1);
                    // Only store if not already present to avoid overwriting more specific origins
                    originMap.putIfAbsent(directKey, param.getOrigin());
                }
            }
            return unwrapValueRecursive(param.getValue(), originMap, pathPrefix);
        } else if (value instanceof Map) {
            Map<String, Object> map = (Map<String, Object>) value;
            Map<String, Object> unwrapped = new TreeMap<>();
            for (Map.Entry<String, Object> entry : map.entrySet()) {
                String nestedPath = pathPrefix.isEmpty() ? entry.getKey() : pathPrefix + "." + entry.getKey();
                unwrapped.put(entry.getKey(), unwrapValueRecursive(entry.getValue(), originMap, nestedPath));
            }
            return unwrapped;
        } else if (value instanceof List) {
            List<Object> list = (List<Object>) value;
            List<Object> unwrapped = new ArrayList<>();
            for (int i = 0; i < list.size(); i++) {
                String itemPath = pathPrefix + "[" + i + "]";
                unwrapped.add(unwrapValueRecursive(list.get(i), originMap, itemPath));
            }
            return unwrapped;
        }
        return value;
    }

    public static Map<String, Object> convertParameterMapToObject(Map<String, ?> map, String parentOrigin, boolean enableTraceability) {
        Map<String, Object> result = new TreeMap<>();
        map.entrySet().forEach(entry -> {
            String key = entry.getKey();
            Object value = entry.getValue();
            String origin = parentOrigin;
            
            if (value instanceof Parameter) {
                Parameter param = (Parameter) value;
                // Use the parameter's origin if available, otherwise use the parent origin
                origin = (param.getOrigin() != null && !param.getOrigin().isEmpty()) ? param.getOrigin() : parentOrigin;
                value = param.getValue();
            }
            
            Object convertedValue = convertParameterToObject(value, origin, enableTraceability);
            
            // Use Parameter object with origin if traceability is enabled
            // Only use parentOrigin as fallback if the value doesn't have its own origin
            // This ensures we don't assign origins to values that weren't actually from that source
            if (enableTraceability) {
                // Only wrap in Parameter if we have an origin (either from the value itself or from parent)
                // But prefer the value's own origin over parent origin
                String finalOrigin = (origin != null && !origin.isEmpty()) ? origin : parentOrigin;
                if (finalOrigin != null && !finalOrigin.isEmpty()) {
                    result.put(key, new Parameter(convertedValue, finalOrigin, false));
                } else {
                    // No origin available, don't wrap in Parameter
                    result.put(key, convertedValue);
                }
            } else {
                result.put(key, convertedValue);
            }
        });
        return result;
    }
}
