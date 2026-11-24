package org.qubership.cloud.devops.commons.utils;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.qubership.cloud.devops.commons.Injector;
import org.qubership.cloud.devops.commons.exceptions.ExternalCredProcessingException;
import org.qubership.cloud.devops.commons.pojo.credentials.dto.CredentialDTO;
import org.qubership.cloud.devops.commons.pojo.credentials.model.Credential;
import org.qubership.cloud.devops.commons.pojo.credentials.model.ExternalCredentials;
import org.qubership.cloud.devops.commons.pojo.extcreds.ExtCredEntities;
import org.qubership.cloud.devops.vals.core.dto.SecretStoreDTO;
import org.qubership.cloud.devops.vals.core.dto.SecretStoreType;

import java.util.*;

import static org.junit.jupiter.api.Assertions.*;

class ParameterUtilsTest {

    private final Map<String, Parameter> secureOut = new LinkedHashMap<>();
    private final Map<String, Parameter> insecureOut = new LinkedHashMap<>();

    private static Parameter plain(Object value) {
        return Parameter.builder().value(value).secured(false).build();
    }

    private static Parameter secret(Object value) {
        return Parameter.builder().value(value).secured(true).build();
    }

    /** Builds an ordered parameter map from alternating key, Parameter arguments. */
    private static Map<String, Parameter> params(Object... keysAndValues) {
        Map<String, Parameter> result = new LinkedHashMap<>();
        for (int i = 0; i < keysAndValues.length; i += 2) {
            result.put((String) keysAndValues[i], (Parameter) keysAndValues[i + 1]);
        }
        return result;
    }

    private void split(Map<String, Parameter> input) {
        ParameterUtils.splitBySecure(input, secureOut, insecureOut, null);
    }

    private static List<?> listOf(Parameter param) {
        return (List<?>) param.getValue();
    }

    private static Set<String> keysOf(Parameter param) {
        return ((Map<String, ?>) param.getValue()).keySet();
    }

    @Test
    void listOfMapsWithSecuredFieldGoesWholeToSecure() {
        List<Object> users = List.of(
                plain(params("user", plain("a"), "password", secret("s"))),
                plain(params("user", plain("b"))));
        split(params("users", plain(users)));

        assertFalse(insecureOut.containsKey("users"));
        assertEquals(2, listOf(secureOut.get("users")).size());
    }

    @Test
    void listOfMapsWithoutSecuredFieldStaysInInsecure() {
        List<Object> users = List.of(plain(params("user", plain("a"))));
        split(params("users", plain(users)));

        assertFalse(secureOut.containsKey("users"));
        assertSame(users, insecureOut.get("users").getValue());
    }

    @Test
    void listOfScalarsWithOneSecuredGoesWholeToSecure() {
        List<Object> values = List.of(plain("a"), secret("b"));
        split(params("values", plain(values)));

        assertFalse(insecureOut.containsKey("values"));
        assertEquals(2, listOf(secureOut.get("values")).size());
    }

    @Test
    void listWithSecuredFirstElementKeepsAllElementsInLocalEnvironment() {
        // Local environments stop scanning at the first secret, the rest must still be kept.
        List<Object> values = List.of(secret("a"), plain("b"), plain("c"));
        split(params("values", plain(values)));

        assertFalse(insecureOut.containsKey("values"));
        assertEquals(3, listOf(secureOut.get("values")).size());
    }

    @Test
    void mapWithNestedSecuredListKeepsScalarKeysInsecure() {
        Map<String, Parameter> nested = params(
                "name", plain("x"),
                "values", plain(List.of(plain("a"), secret("b"))));
        split(params("config", plain(nested)));

        assertEquals(Set.of("values"), keysOf(secureOut.get("config")));
        assertEquals(Set.of("name"), keysOf(insecureOut.get("config")));
    }

    @Test
    void mapWithoutListSplitsPerKey() {
        Map<String, Parameter> nested = params("host", plain("h"), "token", secret("t"));
        split(params("config", plain(nested)));

        assertEquals(Set.of("token"), keysOf(secureOut.get("config")));
        assertEquals(Set.of("host"), keysOf(insecureOut.get("config")));
    }

    // External credentials

    private static final String STORE_ID = "store-1";

    @BeforeEach
    void registerExternalCredentialLookups() {
        CredentialDTO.Property username = new CredentialDTO.Property();
        username.setName("username");
        Credential appCred = new ExternalCredentials(false, STORE_ID, List.of(username), "secret/app");
        SecretStoreDTO store = SecretStoreDTO.builder().type(SecretStoreType.vault).mountPath("secret").build();

        Injector injector = new Injector();
        injector.getDi().add(new CredentialUtils() {
            @Override
            public Credential getCredentialsById(String id) {
                return "app-cred".equals(id) ? appCred : null;
            }

            @Override
            public Map<String, CredentialDTO> getCredsFromYaml() {
                return Map.of();
            }
        });
        injector.getDi().add((SecretStoresUtils) id -> STORE_ID.equals(id) ? store : null);
    }

    private static Parameter credRef(String property) {
        return plain(params(
                "$type", plain("credRef"),
                "credId", plain("app-cred"),
                "property", plain(property)));
    }

    private void splitExternalOnly(String parameterType, Map<String, Parameter> input) {
        ExtCredEntities extCreds = ExtCredEntities.builder()
                .isExternalOnly(true)
                .refShape("eso")
                .parameterType(parameterType)
                .build();
        ParameterUtils.splitBySecure(input, secureOut, insecureOut, extCreds);
    }

    /** The resolved value of the single credential reference held by a list element map. */
    private static Map<?, ?> resolvedRefOf(Object listElement, String key) {
        Parameter element = (Parameter) listElement;
        Parameter ref = ((Map<String, Parameter>) element.getValue()).get(key);
        return (Map<?, ?>) ref.getValue();
    }

    @Test
    void listWithCredentialReferenceGoesWholeToSecureWithReferenceResolved() {
        List<Object> appParam = List.of(
                plain(params("APP_USER", credRef("username"))),
                plain(params("STATIC_VAL", plain("abc"))));
        splitExternalOnly("DEPLOY", params("APP_PARAM", plain(appParam)));

        assertFalse(insecureOut.containsKey("APP_PARAM"));
        List<?> resolved = listOf(secureOut.get("APP_PARAM"));
        assertEquals(2, resolved.size());
        Map<?, ?> user = resolvedRefOf(resolved.get(0), "APP_USER");
        assertEquals(STORE_ID, ((Parameter) user.get("secretStoreId")).getValue());
        assertFalse(user.containsKey("$type"));
        assertEquals("abc", ((Parameter) ((Map<String, Parameter>) ((Parameter) resolved.get(1)).getValue())
                .get("STATIC_VAL")).getValue());
    }

    @Test
    void referenceAfterSecuredElementIsStillResolvedInExternalOnlyEnvironment() {
        // Unlike a local environment, scanning must not stop at the first secret here.
        List<Object> values = List.of(
                secret("first"),
                plain(params("APP_USER", credRef("username"))));
        splitExternalOnly("DEPLOY", params("values", plain(values)));

        assertFalse(insecureOut.containsKey("values"));
        List<?> resolved = listOf(secureOut.get("values"));
        assertEquals(2, resolved.size());
        assertEquals(STORE_ID,
                ((Parameter) resolvedRefOf(resolved.get(1), "APP_USER").get("secretStoreId")).getValue());
    }

    @Test
    void listWithoutReferenceStaysInInsecureInExternalOnlyEnvironment() {
        List<Object> users = List.of(plain(params("user", plain("a"))));
        splitExternalOnly("DEPLOY", params("users", plain(users)));

        assertFalse(secureOut.containsKey("users"));
        assertSame(users, insecureOut.get("users").getValue());
    }

    @Test
    void listWithReferenceIsLeftOutOfBothOutputsForUnsupportedParameterType() {
        List<Object> appParam = List.of(
                plain(params("APP_USER", credRef("username"))),
                plain(params("STATIC_VAL", plain("abc"))));
        splitExternalOnly("TECHNICAL", params("APP_PARAM", plain(appParam)));

        assertFalse(secureOut.containsKey("APP_PARAM"));
        assertFalse(insecureOut.containsKey("APP_PARAM"));
    }

    @Test
    void listWithReferenceFailsInLocalEnvironment() {
        List<Object> appParam = List.of(plain(params("APP_USER", credRef("username"))));

        assertThrows(ExternalCredProcessingException.class,
                () -> split(params("APP_PARAM", plain(appParam))));
    }
}
