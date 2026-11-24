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

    static final Set<String> SUPPORTED_PARAMETER_TYPES = Set.of("DEPLOY", "E2E");

    public static void splitBySecure(
            Map<String, Parameter> input,
            Map<String, Parameter> secureOut,
            Map<String, Parameter> insecureOut,
            ExtCredEntities extCredEntities
    ) {
        input.entrySet().forEach(entry -> {
            String key = entry.getKey();

            Parameter param = entry.getValue();
            Object value = param.getValue();
            if (value instanceof Map<?, ?>) {
                Map<String, Parameter> valueMap = (Map<String, Parameter>) value;
                if (shouldAddExtParams(secureOut, extCredEntities, key, param, valueMap)) return;
                Map<String, Parameter> secureChild = new LinkedHashMap<>();
                Map<String, Parameter> insecureChild = new LinkedHashMap<>();
                splitBySecure((Map<String, Parameter>) value, secureChild, insecureChild, extCredEntities);
                if (!secureChild.isEmpty()) {
                    secureOut.put(key, copyOldValues(param, secureChild));
                }
                if (!insecureChild.isEmpty()) {
                    insecureOut.put(key, copyOldValues(param, insecureChild));
                }
            } else if (value instanceof List<?>) {
                // Helm replaces lists as a whole, so a list is never divided between the outputs.
                ListSecretScanner scanner = ListSecretScanner.scan((List<?>) value, extCredEntities);
                if (scanner.isKeySkipped()) {
                    return;
                }
                if (scanner.containsSecret() || param.isSecured()) {
                    secureOut.put(key, copyOldValues(param, scanner.getResolvedValue()));
                } else {
                    insecureOut.put(key, param);
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

    private static boolean shouldAddExtParams(Map<String, Parameter> secureOut, ExtCredEntities extCredEntities, String key, Parameter param, Map<String, Parameter> valueMap) {
        if (ExternalCredUtils.isExternalCred(valueMap)) {
            if (extCredEntities == null || !extCredEntities.isExternalOnly) {
                throw new ExternalCredProcessingException(String.format(INVALID_CRED_TYPE, valueMap));
            }
            if (!SUPPORTED_PARAMETER_TYPES.contains(extCredEntities.getParameterType())) {
                return true;
            }
            Object finalVal = ExternalCredUtils.getFinalParam(valueMap, extCredEntities.getRefShape());
            if (finalVal != null) {
                secureOut.put(key, copyOldValues(param, finalVal));
                return true;
            }
        }
        return false;
    }
    static Parameter copyOldValues(Parameter original, Object newValue) {
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

}
