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

package org.qubership.cloud.extcreds.valsref;

import org.junit.jupiter.api.Test;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.CsvSource;

import java.util.List;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;

class ValsReferenceBuilderTest {

    @Test
    void vaultSingleValueReference() {
        SecretStoreConfig store = SecretStoreConfig.builder()
                .type(SecretStoreType.vault)
                .mountPath("secret/data/app")
                .build();

        String uri = ValsReferenceBuilder.buildValsReference(
                "app-sidecar-token",
                "test_cluster_01/env-1",
                null,
                List.of(),
                store
        );

        assertEquals(
                "ref+vault://secret/data/app/data/test_cluster_01/env-1/app-sidecar-token#/value",
                uri
        );
    }

    @Test
    void gcpMultiFieldReference() {
        SecretStoreConfig store = SecretStoreConfig.builder()
                .type(SecretStoreType.gcp)
                .projectId("agf56hoji8")
                .build();

        String uri = ValsReferenceBuilder.buildValsReference(
                "app-dbaas-cred",
                "test-cluster-01/env-1",
                "username",
                List.of("username", "password"),
                store
        );

        assertEquals(
                "ref+gcpsecrets://agf56hoji8/test-cluster-01--env-1--app-dbaas-cred#/username",
                uri
        );
    }

    @ParameterizedTest
    @CsvSource({
            "vault, test/path, cred-id, test/path/cred-id",
            "gcp, ocp-05/env-1, postgres-password, ocp-05--env-1--postgres-password"
    })
    void normalizedSecretName(String type, String remoteRefPath, String credId, String expected) {
        SecretStoreType storeType = SecretStoreType.valueOf(type);
        assertEquals(expected, SecretNameBuilder.buildNormalizedSecretName(remoteRefPath, credId, storeType));
    }

    @Test
    void fragmentValidationFailsWhenPropertyMissingForMultiField() {
        assertThrows(ExternalCredValsException.class, () ->
                ValsFragmentBuilder.buildFragment("cred", null, List.of("username"), SecretStoreType.gcp));
    }

    @Test
    void awsSingleValueOmitsFragment() {
        SecretStoreConfig store = SecretStoreConfig.builder()
                .type(SecretStoreType.aws)
                .region("India")
                .build();

        String uri = ValsReferenceBuilder.buildValsReference(
                "token-cred",
                "test-cluster-01/env-1",
                null,
                List.of(),
                store
        );

        assertEquals(
                "ref+awssecrets://test-cluster-01/env-1/token-cred?region=India",
                uri
        );
    }
}
