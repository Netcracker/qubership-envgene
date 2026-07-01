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

import com.fasterxml.jackson.databind.ObjectMapper;
import lombok.experimental.UtilityClass;
import org.qubership.cloud.devops.commons.Injector;
import org.qubership.cloud.devops.commons.exceptions.ExternalCredProcessingException;
import org.qubership.cloud.devops.commons.pojo.credentials.dto.CredentialDTO;
import org.qubership.cloud.devops.commons.pojo.credentials.model.Credential;
import org.qubership.cloud.devops.commons.pojo.credentials.model.CredentialsTypeEnum;
import org.qubership.cloud.devops.commons.pojo.credentials.model.ExternalCredentials;
import org.qubership.cloud.devops.commons.pojo.extcreds.SecretStoreDTO;
import org.qubership.cloud.devops.commons.pojo.extcreds.SecretStoreType;
import org.qubership.cloud.devops.commons.utils.CredentialUtils;
import org.qubership.cloud.devops.commons.utils.Parameter;
import org.qubership.cloud.devops.commons.utils.SecretStoresUtils;
import org.qubership.cloud.extcreds.valsref.ExternalCredValsException;
import org.qubership.cloud.extcreds.valsref.SecretStoreConfig;
import org.qubership.cloud.extcreds.valsref.ValsFragmentBuilder;
import org.qubership.cloud.extcreds.valsref.ValsUriBuilder;

import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

import static org.qubership.cloud.devops.commons.exceptions.constant.ExternalCredExceptionMessages.*;
import static org.qubership.cloud.devops.commons.utils.constant.ExternalCredConstants.*;

@UtilityClass
public class ExternalCredUtils {

    private static final ObjectMapper MAPPER = new ObjectMapper();

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
            throw new ExternalCredProcessingException(String.format(SECRET_NOT_FOUND ,credentials.getSecretStore(), credId));
        }
        String normalizedSecretName = SecretNameBuilder.buildNormalizedSecretName(credentials.getRemoteRefPath(), credId, store.getType());
        List<CredentialDTO.Property> properties = credentials.getProperties();
        List<String> propertyNames = properties == null
                ? List.of()
                : properties.stream().map(CredentialDTO.Property::getName).toList();
        SecretStoreType type = store.getType();
        if (VALS.equals(refShape)) {
            String fragment = buildFragment(credId, property, propertyNames, type);
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

    private static String buildFragment(String credId, String property, List<String> propertyNames, SecretStoreType type) {
        try {
            return ValsFragmentBuilder.buildFragment(
                    credId,
                    property,
                    propertyNames,
                    org.qubership.cloud.extcreds.valsref.SecretStoreType.valueOf(type.name())
            );
        } catch (ExternalCredValsException e) {
            throw new ExternalCredProcessingException(e.getMessage());
        }
    }

    private static void checkSingleValProperty(String credId, List<CredentialDTO.Property> properties) {
        try {
            List<String> propertyNames = properties == null
                    ? List.of()
                    : properties.stream().map(CredentialDTO.Property::getName).toList();
            ValsFragmentBuilder.validateSingleValProperty(credId, propertyNames);
        } catch (ExternalCredValsException e) {
            throw new ExternalCredProcessingException(e.getMessage());
        }
    }

    private static void checkMultiValProperty(List<CredentialDTO.Property> properties, String credId, String prop) {
        try {
            List<String> propertyNames = properties == null
                    ? List.of()
                    : properties.stream().map(CredentialDTO.Property::getName).toList();
            ValsFragmentBuilder.validateMultiValProperty(propertyNames, credId, prop);
        } catch (ExternalCredValsException e) {
            throw new ExternalCredProcessingException(e.getMessage());
        }
    }

    private static String buildValsUri(SecretStoreDTO store, String normalizedSecretName, String fragment) {
        try {
            return ValsUriBuilder.buildValsUri(toStoreConfig(store), normalizedSecretName, fragment);
        } catch (ExternalCredValsException e) {
            throw new ExternalCredProcessingException(e.getMessage());
        }
    }

    private static SecretStoreConfig toStoreConfig(SecretStoreDTO store) {
        return SecretStoreConfig.builder()
                .type(org.qubership.cloud.extcreds.valsref.SecretStoreType.valueOf(store.getType().name()))
                .mountPath(store.getMountPath())
                .vaultName(store.getVaultName())
                .region(store.getRegion())
                .projectId(store.getProjectId())
                .build();
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
            CredentialDTO cred = entry.getValue();
            if (cred.getType() != CredentialsTypeEnum.external || !Boolean.TRUE.equals(cred.getCreate())) {
                continue;
            }
            String storeId = cred.getSecretStore();
            SecretStoreDTO store = secretStoresUtils.getStoresById(storeId);
            if (store == null) {
                throw new ExternalCredProcessingException(String.format(SECRET_NOT_FOUND ,store, credId));
            }
            storesOut.putIfAbsent(storeId, MAPPER.convertValue(store, Map.class));
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
}
