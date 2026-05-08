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
import org.qubership.cloud.devops.commons.pojo.credentials.model.CredentialsTypeEnum;
import org.qubership.cloud.devops.commons.pojo.credentials.model.ExternalCredentials;
import org.qubership.cloud.devops.commons.pojo.extcreds.SecretStoreDTO;
import org.qubership.cloud.devops.commons.pojo.extcreds.SecretStoreType;
import org.qubership.cloud.devops.commons.utils.CredentialUtils;
import org.qubership.cloud.devops.commons.utils.Parameter;
import org.qubership.cloud.devops.commons.utils.SecretStoresUtils;

import java.util.*;

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
                return VALS;
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
            return null;
        }
        Parameter credIdParam = map.get("credId");
        if (credIdParam == null || credIdParam.getValue() == null) {
            return null;
        }
        String credId = credIdParam.getValue().toString();
        String origin = credIdParam.getOrigin();
        Parameter propertyParam = map.get("property");
        String prop = (propertyParam != null && propertyParam.getValue() != null)
                ? propertyParam.getValue().toString()
                : null;
        return prepareFinalExtValue(credId, prop, refShape, origin);
    }

    private static Object prepareFinalExtValue(String credId, String property, String refShape, String origin) {
        ExternalCredentials credentials = (ExternalCredentials)Injector.getInstance().getDi().get(CredentialUtils.class).getCredentialsById(credId);
        if (credentials == null) {
            throw new ExternalCredProcessingException(String.format(EXT_CRED_NOT_FOUND, credId));
        }
        SecretStoreDTO store = Injector.getInstance().getDi().get(SecretStoresUtils.class).getStoresById(credentials.getSecretStore());
        if (store == null) {
            throw new ExternalCredProcessingException(String.format(SECRET_NOT_FOUND ,credentials.getSecretStore(), credId));
        }
        String normalizedSecretName = SecretNameBuilder.buildNormalizedSecretName(credentials.getRemoteRefPath(), credId, store.getType());
        List<CredentialDTO.Property> properties = credentials.getProperties();
        SecretStoreType type = store.getType();
        if (VALS.equals(refShape)) {
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
            return buildValsUri(store, normalizedSecretName, fragment);
        }
        if (ESO.equals(refShape)) {
            String secretStoreId = credentials.getSecretStore();
            Map<String, Parameter> resolvedParam = new LinkedHashMap<>();
            resolvedParam.put(SECRET_STORE_ID, Parameter.builder().value(secretStoreId).origin(origin).build());
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

    private static String buildValsUri(SecretStoreDTO store, String normalizedSecretName, String fragment) {
        SecretStoreType type = store.getType();
        String baseUri = switch (type) {
            case vault -> "ref+vault://" + store.getMountPath() + "/data/" + normalizedSecretName;
            case azure -> "ref+azurekeyvault://" + store.getVaultName() + "/" + normalizedSecretName;
            case aws -> "ref+awssecrets://" + normalizedSecretName + "?region=" + store.getRegion();
            case gcp -> "ref+gcpsecrets://" + store.getProjectId() + "/" + normalizedSecretName;
        };
        if (fragment != null && !fragment.isEmpty()) {
            return baseUri + fragment;
        }
        return baseUri;
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

    public static Map<String, Object>  generateExternalCredentialsMap() {
        Map<String, Object> result = new LinkedHashMap<>();
        Map<String, Object> credsOut = new LinkedHashMap<>();
        Map<String, Object> storesOut = new LinkedHashMap<>();
        Map<String, CredentialDTO> credentials  = Injector.getInstance().getDi().get(CredentialUtils.class).getCredsFromYaml();
        SecretStoresUtils secretStoresUtils = Injector.getInstance().getDi().get(SecretStoresUtils.class);
        for (Map.Entry<String, CredentialDTO> entry : credentials.entrySet()) {
            String credId = entry.getKey();
            CredentialDTO cred = credentials.get(credId);
            if (cred.getType() != CredentialsTypeEnum.external || !Boolean.TRUE.equals(cred.getCreate())) {
                continue;
            }
            String storeId = cred.getSecretStore();
            SecretStoreDTO store = secretStoresUtils.getStoresById(storeId);
            storesOut.putIfAbsent(storeId, buildStoreMap(store));
            Map<String, Object> credMap = new LinkedHashMap<>();
            credMap.put(SECRET_STORE_ID, storeId);
            String normalizedName = SecretNameBuilder.buildNormalizedSecretName(
                    cred.getRemoteRefPath(),
                    credId,
                    store.getType()
            );
            credMap.put(NORM_SECRET_NAME, normalizedName);
            if (cred.getProperties() != null && !cred.getProperties().isEmpty()) {
                List<Map<String, String>> props = cred.getProperties().stream()
                        .map(p -> Map.of("name", p.getName()))
                        .toList();

                credMap.put(PROPS, props);
            }
            credsOut.put(credId, credMap);
        }
        result.put(SECRET_STORES, storesOut);
        result.put(CREDS, credsOut);
        return result;
    }

    private static Map<String, Object> buildStoreMap(SecretStoreDTO store) {
        Map<String, Object> map = new LinkedHashMap<>();
        map.put(TYPE, store.getType().name().toLowerCase());
        map.put(URL, store.getUrl());
        switch (store.getType()) {
            case vault:
                map.put(MOUNT_PATH, store.getMountPath());
                break;
            case azure:
                map.put(VAULT_NAME, store.getVaultName());
                break;
            case aws:
                map.put(REGION, store.getRegion());
                break;
            case gcp:
                map.put(PROJECT_ID, store.getProjectId());
                break;
        }
        return map;
    }

}
