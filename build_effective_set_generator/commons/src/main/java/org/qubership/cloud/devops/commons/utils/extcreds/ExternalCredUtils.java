package org.qubership.cloud.devops.commons.utils.extcreds;

import jakarta.enterprise.context.ApplicationScoped;
import jakarta.inject.Inject;
import org.qubership.cloud.devops.commons.pojo.credentials.dto.CredentialDTO;
import org.qubership.cloud.devops.commons.pojo.extcreds.ExtCredEntities;
import org.qubership.cloud.devops.commons.pojo.extcreds.SecretStoreDTO;
import org.qubership.cloud.devops.commons.pojo.extcreds.SecretStoreType;
import org.qubership.cloud.devops.commons.utils.Parameter;

import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

import static org.qubership.cloud.devops.commons.utils.constant.ExternalCredConstants.*;

@ApplicationScoped
public class ExternalCredUtils {

    public static String resolveReferenceShape(Object secretFlow, Object esoSupport) {
        Object secretFlowVal = extractValue(secretFlow);
        Object esoSupportVal = extractValue(esoSupport);

        String flow = secretFlowVal != null ? secretFlowVal.toString() : HELM_VALUES;
        Boolean eso = (esoSupportVal instanceof Boolean) ? Boolean.TRUE.equals(esoSupport) : false;

        switch (flow) {
            case HELM_VALUES:
                return VALS;

            case EXT_VALUES:
                if (eso) {
                    return ESO;
                }
                throw new IllegalStateException("Secret Flow is \"external-values\" with ESO disabled which is not supported. Failing Effective set generation");

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

    public static Object getFinalParam(Map<String, Parameter> map, String refShape, Map<String, CredentialDTO> extCreds, Map<String, SecretStoreDTO> secretStores) {
        Parameter typeParam = map.get("$type");
        if (typeParam != null && typeParam.getValue() != null) {
            if ("credRef".equals(typeParam.getValue())) {
                Parameter credId = map.get("credId");
                Parameter property = map.get("property");
                if (credId != null && credId.getValue() instanceof String) {
                    String prop = property != null && property.getValue() != null ?   property.getValue().toString() : null;
                    Object finals =  prepareFinalValue(credId.getValue().toString(), prop, refShape, extCreds, secretStores);
                    return finals;
                }
            }
        }
        return null;
    }

    private static Object prepareFinalValue(String credId, String property, String refShape, Map<String, CredentialDTO> extCreds, Map<String, SecretStoreDTO> secretStores) {
        CredentialDTO credential = extCreds.get(credId);
        if (credential == null) {
            throw new IllegalArgumentException(String.format("Credential '%s' not found in External Credentials provided.", credId));
        }
        SecretStoreDTO store = secretStores.get(credential.getSecretStore());
        if (store == null) {
            throw new IllegalArgumentException(String.format("SecretStore '%s' not found in secret file for credential '%s'." ,credential.getSecretStore(), credId));
        }
        String normalizedSecretName = SecretNameBuilder.buildNormalizedSecretName(credential.getRemoteRefPath(), credId, store.getType());
        List<CredentialDTO.Property> properties = credential.getProperties();
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
            String secretStoreId = credential.getSecretStore();
            if (property != null) {
                checkMultiValProperty(properties, credId, property);
                return Map.of(
                        "secretStoreId", secretStoreId,
                        "normalizedSecretName", normalizedSecretName,
                        "secretKeys", List.of(
                                Map.of("remoteKeyName", property)
                        )
                );
            }
            else {
                checkSingleValProperty(credId, properties);
                return Map.of(
                        "secretStoreId", secretStoreId,
                        "normalizedSecretName", normalizedSecretName
                );
            }
        }
        throw new IllegalStateException(String.format("Unexpected flow in prepareFinalValue. refShape=%s, credId=%s, property=%s", refShape, credId, property));
    }

    private static void checkSingleValProperty(String credId, List<CredentialDTO.Property> properties) {
        if (properties != null && !properties.isEmpty()) {
            throw new IllegalArgumentException(String.format("Credential in external template has properties but no property provided in cred '%s' referenced in parameter.", credId));
        }
    }

    private static void checkMultiValProperty(List<CredentialDTO.Property> properties, String credId, String prop) {
        if (properties == null || properties.isEmpty()) {
            throw new IllegalArgumentException(String.format("No properties defined for credential %s in external credential template.", credId));
        }
        boolean exists = properties.stream().anyMatch(p -> prop.equals(p.getName()));
        if (!exists) {
            throw new IllegalArgumentException(String.format("Invalid property '%s' referred in parameter for external credential id '%s'.", prop, credId));
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

}
