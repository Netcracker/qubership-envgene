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

package org.qubership.cloud.devops.commons.utils.extcreds;

import lombok.experimental.UtilityClass;
import org.qubership.cloud.devops.commons.Injector;
import org.qubership.cloud.devops.commons.exceptions.ExternalCredProcessingException;
import org.qubership.cloud.devops.commons.pojo.credentials.dto.CredentialDTO;
import org.qubership.cloud.devops.commons.pojo.credentials.model.Credential;
import org.qubership.cloud.devops.commons.pojo.credentials.model.CredentialsTypeEnum;
import org.qubership.cloud.devops.commons.pojo.credentials.model.ExternalCredentials;
import org.qubership.cloud.devops.commons.pojo.extcreds.Strategy;
import org.qubership.cloud.devops.commons.utils.CredentialUtils;
import org.qubership.cloud.devops.commons.utils.Parameter;
import org.qubership.cloud.devops.commons.utils.SecretStoresUtils;
import org.qubership.cloud.devops.commons.utils.di.DIWrapper;
import org.qubership.cloud.devops.vals.core.SecretNameBuilder;
import org.qubership.cloud.devops.vals.core.ValsUriBuilder;
import org.qubership.cloud.devops.vals.core.dto.SecretStoreDTO;
import org.qubership.cloud.devops.vals.core.dto.SecretStoreType;

import java.util.Collections;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

import static org.qubership.cloud.devops.commons.exceptions.constant.ExternalCredExceptionMessages.*;
import static org.qubership.cloud.devops.commons.utils.constant.ExternalCredConstants.*;

@UtilityClass
public class ExternalCredUtils {

    public static boolean isExternalCred(Map<String, Parameter> map) {
        Parameter typeParam = map.get("$type");
        if (typeParam != null && typeParam.getValue() instanceof String) {
            return "credRef".equals(typeParam.getValue());
        }
        return false;
    }

    public static String resolveReferenceShape(Object secretFlow, Object esoSupport) {
        Object secretFlowVal = extractValue(secretFlow);
        Object esoSupportVal = extractValue(esoSupport);
        String flow = secretFlowVal != null ? secretFlowVal.toString() : HELM_VALUES;
        boolean eso = esoSupportVal != null &&
                Boolean.parseBoolean(esoSupportVal.toString());
        switch (flow) {
            case HELM_VALUES:
                return VALS;

            case EXT_VALUES:
                if (eso) {
                    return ESO;
                }
                throw new ExternalCredProcessingException(ESO_DISABLED_MESSAGE);

            default:
                throw new ExternalCredProcessingException(String.format(INVALID_SECRET_FLOW, flow, HELM_VALUES, EXT_VALUES));
        }
    }

    private static Object extractValue(Object obj) {
        if (obj instanceof Parameter) {
            return ((Parameter) obj).getValue();
        }
        return obj;
    }

    public static Object getFinalParam(Map<String, Parameter> map, String refShape) {
        Parameter typeParam = map.get("$type");
        if (typeParam == null || typeParam.getValue() == null) {
            return null;
        }
        if (!"credRef".equals(typeParam.getValue())) {
            throw new ExternalCredProcessingException(String.format(INVALID_CRED_MAP, map));
        }
        Parameter credIdParam = map.get("credId");
        if (credIdParam == null || credIdParam.getValue() == null) {
            throw new ExternalCredProcessingException(String.format(INVALID_CRED_MAP, map));
        }
        String credId = credIdParam.getValue().toString();
        String origin = credIdParam.getOrigin();
        Parameter propertyParam = map.get("property");
        String prop = (propertyParam != null && propertyParam.getValue() != null)
                ? propertyParam.getValue().toString()
                : null;
        return prepareFinalExtValue(credId, prop, refShape, origin);
    }

    public static Object prepareFinalExtValue(String credId, String property, String refShape, String origin) {
        Credential rawCred = Injector.getInstance().getDi().get(CredentialUtils.class).getCredentialsById(credId);
        if (rawCred == null) {
            throw new ExternalCredProcessingException(String.format(EXT_CRED_NOT_FOUND, credId));
        }
        if (!(rawCred instanceof ExternalCredentials)) {
            throw new ExternalCredProcessingException(String.format(INVALID_CRED, credId));
        }
        ExternalCredentials credentials = (ExternalCredentials) rawCred;
        SecretStoreDTO store = Injector.getInstance().getDi().get(SecretStoresUtils.class).getStoresById(credentials.getSecretStore());
        if (store == null) {
            throw new ExternalCredProcessingException(String.format(SECRET_NOT_FOUND, credentials.getSecretStore(), credId));
        }

        List<CredentialDTO.Property> properties = credentials.getProperties();
        SecretStoreType type = store.getType();
        if (VALS.equals(refShape)) {
            String baseUri = ValsUriBuilder.buildValsUri(credId, credentials.getRemoteRefPath(), credentials.getSecretStore(), store);
            String fragment = "";
            if (property != null) {
                checkMultiValProperty(properties, credId, property);
                fragment = "#/" + property;
            } else {
                checkSingleValProperty(credId, properties);
                if (type == SecretStoreType.vault) {
                    fragment = "#/value";
                }
            }
            if (!fragment.isEmpty()) {
                return baseUri + fragment;
            }
            return baseUri;
        }
        if (ESO.equals(refShape)) {
            String secretStoreId = credentials.getSecretStore();
            Map<String, Parameter> resolvedParam = new LinkedHashMap<>();
            resolvedParam.put(SECRET_STORE_ID, Parameter.builder().value(secretStoreId).origin(origin).build());
            String normalizedSecretName = SecretNameBuilder.buildNormalizedSecretName(credentials.getRemoteRefPath(), credId, store.getType());
            resolvedParam.put(NORM_SECRET_NAME, Parameter.builder().value(normalizedSecretName).origin(origin).build());
            if (property != null) {
                checkMultiValProperty(properties, credId, property);
                resolvedParam.put(SECRET_KEYS,
                        buildSecretKeys(property, origin));
            } else {
                checkSingleValProperty(credId, properties);
            }
            return resolvedParam;
        }
        throw new ExternalCredProcessingException(String.format(UNEXPECTED_FLOW, refShape, credId, property));
    }

    private static void checkSingleValProperty(String credId, List<CredentialDTO.Property> properties) {
        if (properties != null && !properties.isEmpty()) {
            throw new ExternalCredProcessingException(String.format(MULTI_PROPERTY_ERROR, credId));
        }
    }

    private static void checkMultiValProperty(List<CredentialDTO.Property> properties, String credId, String prop) {
        if (properties == null || properties.isEmpty()) {
            throw new ExternalCredProcessingException(String.format(SINGLE_PROPERTY_ERROR, credId));
        }
        boolean exists = properties.stream().anyMatch(p -> prop.equals(p.getName()));
        if (!exists) {
            throw new ExternalCredProcessingException(String.format(INVALID_PROPERTY, prop, credId));
        }
    }


    private static Parameter buildSecretKeys(String property, String origin) {
        Map<String, Parameter> remoteKeyMap = Map.of(
                REMOTE_KEY, Parameter.builder()
                        .value(property)
                        .origin(origin)
                        .build()
        );
        Parameter secretKeyParam = Parameter.builder()
                .value(remoteKeyMap)
                .origin(origin)
                .build();
        return Parameter.builder()
                .value(List.of(secretKeyParam))
                .origin(origin)
                .build();
    }

    public static Map<String, Object> generateExternalCredentialsMap() {
        Map<String, Object> result = new LinkedHashMap<>();
        Map<String, Object> credentialEntries = new LinkedHashMap<>();
        DIWrapper di = Injector.getInstance().getDi();
        Map<String, CredentialDTO> credentials = di.get(CredentialUtils.class).getCredsFromYaml();
        SecretStoresUtils secretStoresUtils = di.get(SecretStoresUtils.class);
        for (Map.Entry<String, CredentialDTO> entry : credentials.entrySet()) {
            String credId = entry.getKey();
            CredentialDTO cred = entry.getValue();
            if (cred == null || CredentialsTypeEnum.external != cred.getType()) {
                continue;
            }
            String storeId = cred.getSecretStore();
            SecretStoreDTO store = secretStoresUtils.getStoresById(storeId);
            if (store == null) {
                throw new ExternalCredProcessingException(String.format(SECRET_NOT_FOUND, storeId, credId));
            }
            Map<String, Object> credMap = new LinkedHashMap<>();
            String valsUrl = ValsUriBuilder.buildValsUri(credId, cred.getRemoteRefPath(), cred.getSecretStore(), store);
            credMap.put(VALS, valsUrl);
            boolean createIfAbsent = Boolean.TRUE.equals(cred.getCreate());
            String strategy = createIfAbsent ? Strategy.CREATE_IF_ABSENT.getValue() : Strategy.FAIL_IF_ABSENT.getValue();
            credMap.put(STRATEGY, strategy);
            if (createIfAbsent) {
                credMap.put(DATA, buildData(cred, store));
            }
            credentialEntries.put(credId, credMap);
        }
        if (credentialEntries.isEmpty()) {
            return Collections.emptyMap();
        }
        result.put(CREDS, credentialEntries);
        return result;
    }

    private static Object buildData(CredentialDTO cred, SecretStoreDTO store) {
        if (cred.getProperties() != null && !cred.getProperties().isEmpty()) {
            Map<String, Object> dataMap = new LinkedHashMap<>();
            for (CredentialDTO.Property p : cred.getProperties()) {
                dataMap.put(p.getName(), GENERATE_MARKER);
            }
            return dataMap;
        }
        if (store.getType() == SecretStoreType.vault) {
            return Map.of(VALUE, GENERATE_MARKER);
        }
        return GENERATE_MARKER;
    }

}
