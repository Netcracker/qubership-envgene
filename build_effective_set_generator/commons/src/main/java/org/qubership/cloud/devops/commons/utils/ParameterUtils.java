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
import org.apache.commons.collections4.MapUtils;
import org.qubership.cloud.devops.commons.exceptions.ExternalCredProcessingException;
import org.qubership.cloud.devops.commons.pojo.extcreds.ExtCredEntities;
import org.qubership.cloud.devops.commons.pojo.parameterset.CustomParameterDTO;
import org.qubership.cloud.devops.commons.utils.extcreds.ExternalCredUtils;

import java.util.*;

import static org.qubership.cloud.devops.commons.exceptions.constant.ExternalCredExceptionMessages.INVALID_CRED_TYPE;

@UtilityClass
public class ParameterUtils {

    public static final String CONTROLLER_NAMESPACE = "controllerNamespace";
    public static final String USERNAME = "username";
    public static final String PASSWORD = "password";

    private static final String PARAM_TYPE = "DEPLOY";

    public static void splitBySecure(
            Map<String, Parameter> input,
            Map<String, Parameter> secureOut,
            Map<String, Parameter> insecureOut,
            Map<String, Parameter> paramsWithExtCredsOut,
            ExtCredEntities extCredEntities
    ) {
        input.entrySet().forEach(entry -> {
            String key = entry.getKey();

            Parameter param = entry.getValue();
            Object value = param.getValue();
            if (value instanceof Map<?, ?>) {
                Map<String, Parameter> valueMap = (Map<String, Parameter>) value;
                if (shouldAddExtParams(paramsWithExtCredsOut, extCredEntities, key, param, valueMap)) return;
                Map<String, Parameter> secureChild = new LinkedHashMap<>();
                Map<String, Parameter> insecureChild = new LinkedHashMap<>();
                Map<String, Parameter> externalChild = new LinkedHashMap<>();
                splitBySecure((Map<String, Parameter>) value, secureChild, insecureChild, externalChild, extCredEntities);
                if (!secureChild.isEmpty()) {
                    secureOut.put(key, copyOldValues(param, secureChild));
                }
                if (!insecureChild.isEmpty()) {
                    insecureOut.put(key, copyOldValues(param, insecureChild));
                }
                if (!externalChild.isEmpty()) {
                    paramsWithExtCredsOut.put(key, copyOldValues(param, externalChild));
                }
            } else if (value instanceof List<?>) {
                List<Object> secureList = new ArrayList<>();
                List<Object> insecureList = new ArrayList<>();
                List<Object> externalList = new ArrayList<>();
                for (Object item : (List<?>) value) {
                    if (item instanceof Parameter) {
                        Parameter itemParam = (Parameter) item;
                        Object itemVal = itemParam.getValue();
                        if (itemVal instanceof Map<?, ?>) {
                            Map<String, Parameter> secureNested = new LinkedHashMap<>();
                            Map<String, Parameter> insecureNested = new LinkedHashMap<>();
                            Map<String, Parameter> externalNested = new LinkedHashMap<>();
                            Map<String, Parameter> valueMap = (Map<String, Parameter>) itemVal;
                            if (shouldAddExtParams(paramsWithExtCredsOut, extCredEntities, key, param, valueMap)) return;
                            splitBySecure(valueMap, secureNested, insecureNested, externalNested, extCredEntities);
                            if (!secureNested.isEmpty()) {
                                secureList.add(copyOldValues(itemParam, secureNested));
                            }
                            if (!insecureNested.isEmpty()) {
                                insecureList.add(copyOldValues(itemParam, insecureNested));
                            }
                            if (!externalNested.isEmpty()) {
                                externalList.add(copyOldValues(itemParam, externalNested));
                            }
                        } else {
                            if (itemParam.isSecured()) {
                                secureList.add(itemParam);
                            } else {
                                insecureList.add(itemParam);
                            }
                        }
                    } else {
                        insecureList.add(item);
                    }
                }
                if (!secureList.isEmpty()) {
                    secureOut.put(key, copyOldValues(param, secureList));
                }
                if (!insecureList.isEmpty()) {
                    insecureOut.put(key, copyOldValues(param, insecureList));
                }
                if (!externalList.isEmpty()) {
                    paramsWithExtCredsOut.put(key, copyOldValues(param, externalList));
                }

            } else {
                if (param.isSecured()) {
                    secureOut.put(key, param);
                } else {
                    insecureOut.put(key, param);
                }
            }
        });
    }

    private static boolean shouldAddExtParams(Map<String, Parameter> paramsWithExtCredsOut, ExtCredEntities extCredEntities, String key, Parameter param, Map<String, Parameter> valueMap) {
        if (ExternalCredUtils.isExternalCred(valueMap)) {
            if (extCredEntities == null || !extCredEntities.isExternalOnly) {
                throw new ExternalCredProcessingException(String.format(INVALID_CRED_TYPE, valueMap));
            }
            if (!PARAM_TYPE.equals(extCredEntities.getParameterType())) {
                return true;
            }
            Object finalVal = ExternalCredUtils.getFinalParam(valueMap, extCredEntities.getRefShape());
            if (finalVal != null) {
                paramsWithExtCredsOut.put(key, copyOldValues(param, finalVal));
                return true;
            }
        }
        return false;
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

    public static Map<String, Object> deepSortMapKeysPreservingParameters(Map<?, ?> source) {
        Map<String, Object> out = new TreeMap<>();
        if (source != null) {
            for (Map.Entry<?, ?> e : source.entrySet()) {
                out.put(String.valueOf(e.getKey()), deepSortValuePreservingParameters(e.getValue()));
            }
        }
        return out;
    }

    private static Object deepSortValuePreservingParameters(Object value) {
        if (value instanceof Parameter p) {
            Object sorted = deepSortNestedValue(p.getValue());
            return copyOldValues(p, sorted);
        }
        return deepSortNestedValue(value);
    }

    private static Object deepSortNestedValue(Object value) {
        if (value instanceof Map<?, ?>) {
            return deepSortMapKeysPreservingParameters((Map<?, ?>) value);
        }
        if (value instanceof List<?>) {
            return deepSortListPreservingParameters((List<?>) value);
        }
        return value;
    }

    private static List<Object> deepSortListPreservingParameters(List<?> list) {
        if (list == null) {
            return null;
        }
        List<Object> out = new ArrayList<>(list.size());
        for (Object item : list) {
            out.add(deepSortValuePreservingParameters(item));
        }
        return out;
    }

    public static void splitBgDomainParams(Map<String, Object> bgDomainMap,
                                           Map<String, Object> bgDomainSecureMap,
                                           Map<String, Object> bgDomainParamsMap) {
        if (MapUtils.isEmpty(bgDomainMap)) {
            return;
        }
        bgDomainParamsMap.putAll(bgDomainMap);
        Map<String, Object> controller = (Map<String, Object>) bgDomainParamsMap.get(CONTROLLER_NAMESPACE);
        Object userName = controller.remove(USERNAME);
        Object password = controller.remove(PASSWORD);
        bgDomainParamsMap.put(CONTROLLER_NAMESPACE, controller);
        bgDomainSecureMap.put(CONTROLLER_NAMESPACE, Map.of(USERNAME, userName, PASSWORD, password));
    }

    public static void prepareCustomParams(CustomParameterDTO customParameterDTO,
                                           Map<String, Parameter> deployParams, Map<String, Parameter> technicalParams) {
        updateParameter(customParameterDTO.getAllParams(), deployParams);
        updateParameter(customParameterDTO.getAllParams(), technicalParams);
    }

    private static void updateParameter(Map<String, Parameter> customParams, Map<String, Parameter> params) {
        for (Map.Entry<String, Parameter> entry : customParams.entrySet()) {
            String key = entry.getKey();
            Parameter customParam = entry.getValue();

            if (params.containsKey(key)) {
                Parameter deployParam = params.get(key);
                customParam.setValue(deployParam.getValue());
            }
            params.remove(key);
        }
    }

    @SuppressWarnings("unchecked")
    public static void wrapPlainMapWithOrigin(Map<String, Object> map, String origin) {
        if (map == null || map.isEmpty()) {
            return;
        }
        for (Map.Entry<String, Object> entry : map.entrySet()) {
            Object value = entry.getValue();
            if (value instanceof Parameter) {
                ((Parameter) value).setOrigin(origin);
            } else if (value instanceof Map) {
                wrapPlainMapWithOrigin((Map<String, Object>) value, origin);
            } else if (value instanceof List) {
                wrapPlainListWithOrigin((List<Object>) value, origin);
            } else {
                entry.setValue(new Parameter(value, origin, false));
            }
        }
    }

    @SuppressWarnings("unchecked")
    public static List<Object> wrapPlainListWithOrigin(List<Object> list, String origin) {
        if (list == null || list.isEmpty()) {
            return list;
        }
        for (int i = 0; i < list.size(); i++) {
            Object item = list.get(i);
            if (item instanceof Parameter) {
                // Keep existing Parameter as is
            } else if (item instanceof Map) {
                wrapPlainMapWithOrigin((Map<String, Object>) item, origin);
            } else if (item instanceof List) {
                list.set(i, wrapPlainListWithOrigin((List<Object>) item, origin));
            } else {
                list.set(i, new Parameter(item, origin, false));
            }
        }
        return list;
    }


    public static Map<String, Object> unwrapParameterValues(
            Map<String, Object> inputMap) {
        if (inputMap == null) {
            return Collections.emptyMap();
        }

        Map<String, Object> result = new HashMap<>();

        for (Map.Entry<String, Object> entry : inputMap.entrySet()) {
            Object value = entry.getValue();

            if (value instanceof Parameter) {
                Parameter param = (Parameter) value;
                result.put(entry.getKey(), param.getValue());
            } else {
                result.put(entry.getKey(), value);
            }
        }
        return result;
    }

}
