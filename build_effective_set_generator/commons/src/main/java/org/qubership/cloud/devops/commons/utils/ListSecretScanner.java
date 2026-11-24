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

import org.qubership.cloud.devops.commons.exceptions.ExternalCredProcessingException;
import org.qubership.cloud.devops.commons.pojo.extcreds.ExtCredEntities;
import org.qubership.cloud.devops.commons.utils.extcreds.ExternalCredUtils;

import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

import static org.qubership.cloud.devops.commons.exceptions.constant.ExternalCredExceptionMessages.INVALID_CRED_TYPE;

/**
 * Decides in one traversal whether a list parameter holds a secret at any depth, and resolves the
 * external credential references it contains.
 * <p>
 * Helm replaces lists as a whole, so a list must never be divided between the secure and the insecure
 * output. The caller puts the whole {@link #getResolvedValue() resolved value} on one side, chosen by
 * {@link #containsSecret()}.
 * <p>
 * A list or map is copied only when something below it was resolved. Without external references the
 * original list is returned.
 * <p>
 * In a local (not external-only) environment the traversal stops at the first secret: nothing is left
 * to resolve, so the rest of the list is returned as it is.
 */
public class ListSecretScanner {

    private final ExtCredEntities extCredEntities;
    private final boolean externalOnly;
    private boolean containsSecret;
    private boolean skipKey;
    private Object resolvedValue;

    private ListSecretScanner(ExtCredEntities extCredEntities) {
        this.extCredEntities = extCredEntities;
        this.externalOnly = extCredEntities != null && extCredEntities.isExternalOnly;
    }

    public static ListSecretScanner scan(List<?> list, ExtCredEntities extCredEntities) {
        ListSecretScanner scanner = new ListSecretScanner(extCredEntities);
        scanner.resolvedValue = scanner.scanNode(list);
        return scanner;
    }

    public boolean containsSecret() {
        return containsSecret;
    }

    /**
     * An external reference of a parameter type that is not resolved here. The whole key is left out of
     * both outputs.
     */
    public boolean isKeySkipped() {
        return skipKey;
    }

    public Object getResolvedValue() {
        return resolvedValue;
    }

    private Object scanNode(Object node) {
        if (containsSecret && !externalOnly) {
            return node;
        }
        if (node instanceof Parameter) {
            return scanParameter((Parameter) node);
        }
        if (node instanceof List<?>) {
            return scanList((List<?>) node);
        }
        return node;
    }

    private Object scanParameter(Parameter param) {
        if (param.isSecured()) {
            containsSecret = true;
        }
        Object value = param.getValue();
        if (value instanceof Map<?, ?>) {
            Map<String, Parameter> childParams = (Map<String, Parameter>) value;
            if (ExternalCredUtils.isExternalCred(childParams)) {
                return resolveExternalRef(param, childParams);
            }
            Map<String, Parameter> resolvedChildParams = null;
            for (Map.Entry<String, Parameter> entry : childParams.entrySet()) {
                Object resolvedChild = scanNode(entry.getValue());
                if (resolvedChild != entry.getValue()) {
                    if (resolvedChildParams == null) {
                        resolvedChildParams = new LinkedHashMap<>(childParams);
                    }
                    resolvedChildParams.put(entry.getKey(), (Parameter) resolvedChild);
                }
            }
            return resolvedChildParams == null ? param : ParameterUtils.copyOldValues(param, resolvedChildParams);
        }
        if (value instanceof List<?>) {
            Object resolvedList = scanList((List<?>) value);
            return resolvedList == value ? param : ParameterUtils.copyOldValues(param, resolvedList);
        }
        return param;
    }

    private Object scanList(List<?> list) {
        List<Object> resolvedList = null;
        int index = 0;
        for (Object item : list) {
            Object resolvedItem = scanNode(item);
            if (resolvedItem != item && resolvedList == null) {
                resolvedList = new ArrayList<>(list);
            }
            if (resolvedList != null) {
                resolvedList.set(index, resolvedItem);
            }
            index++;
        }
        return resolvedList == null ? list : resolvedList;
    }

    private Parameter resolveExternalRef(Parameter param, Map<String, Parameter> refMap) {
        if (!externalOnly) {
            throw new ExternalCredProcessingException(String.format(INVALID_CRED_TYPE, refMap));
        }
        if (!ParameterUtils.SUPPORTED_PARAMETER_TYPES.contains(extCredEntities.getParameterType())) {
            skipKey = true;
            return param;
        }
        Object finalValue = ExternalCredUtils.getFinalParam(refMap, extCredEntities.getRefShape());
        if (finalValue == null) {
            return param;
        }
        containsSecret = true;
        return ParameterUtils.copyOldValues(param, finalValue);
    }
}
