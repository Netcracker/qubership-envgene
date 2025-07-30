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

package org.qubership.cloud.devops.commons.utils;

import lombok.experimental.UtilityClass;

import java.util.*;

@UtilityClass
public class ParameterUtils {

    @SuppressWarnings("unchecked")
    public static void splitBySecure(
            Map<String, Parameter> input,
            Map<String, Parameter> secureOut,
            Map<String, Parameter> insecureOut
    ) {
        input.entrySet().forEach(entry -> {
            String key = entry.getKey();
            Parameter param = entry.getValue();
            Object value = param.getValue();

            if (value instanceof Map<?, ?>) {
                Map<String, Parameter> secureChild = new LinkedHashMap<>();
                Map<String, Parameter> insecureChild = new LinkedHashMap<>();

                splitBySecure((Map<String, Parameter>) value, secureChild, insecureChild);

                if (!secureChild.isEmpty()) {
                    secureOut.put(key, copyOldValues(param, secureChild));
                }
                if (!insecureChild.isEmpty()) {
                    insecureOut.put(key, copyOldValues(param, insecureChild));
                }

            } else if (value instanceof List<?>) {
                List<Object> secureList = new ArrayList<>();
                List<Object> insecureList = new ArrayList<>();

                for (Object item : (List<?>) value) {
                    if (item instanceof Parameter) {
                        Parameter itemParam = (Parameter) item;
                        Object itemVal = itemParam.getValue();
                        if (itemVal instanceof Map<?, ?>) {
                            Map<String, Parameter> secureNested = new LinkedHashMap<>();
                            Map<String, Parameter> insecureNested = new LinkedHashMap<>();

                            splitBySecure((Map<String, Parameter>) itemVal, secureNested, insecureNested);

                            if (!secureNested.isEmpty()) {
                                secureList.add(copyOldValues(itemParam, secureNested));
                            }
                            if (!insecureNested.isEmpty()) {
                                insecureList.add(copyOldValues(itemParam, insecureNested));
                            }

                        } else {
                            if (itemParam.isSecured()) {
                                secureList.add(itemParam);
                            } else {
                                insecureList.add(itemParam);
                            }
                        }
                    } else {
                        // If list item is not a Parameter, can't determine security → treat as insecure
                        insecureList.add(item);
                    }
                }

                if (!secureList.isEmpty()) {
                    secureOut.put(key, copyOldValues(param, secureList));
                }
                if (!insecureList.isEmpty()) {
                    insecureOut.put(key, copyOldValues(param, insecureList));
                }

            } else {
                // primitive value
                if (param.isSecured()) {
                    secureOut.put(key, param);
                } else {
                    insecureOut.put(key, param);
                }
            }
        });
    }

    private static Parameter copyOldValues(Parameter original, Object newValue) {
        return Parameter.builder()
                .value(newValue)
                .origin(original.getOrigin())
                .parsed(original.isParsed())
                .valid(original.isValid())
                .processed(original.isProcessed())
                .secured(original.isSecured())
                .translated(original.getTranslated())
                .build();
    }

}


