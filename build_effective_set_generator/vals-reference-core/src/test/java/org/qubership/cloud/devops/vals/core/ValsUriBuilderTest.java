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

package org.qubership.cloud.devops.vals.core;

import org.junit.jupiter.api.Test;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.Arguments;
import org.junit.jupiter.params.provider.MethodSource;
import org.qubership.cloud.devops.vals.core.dto.SecretStoreDTO;
import org.qubership.cloud.devops.vals.core.dto.SecretStoreType;
import org.qubership.cloud.devops.vals.core.exceptions.SecretReferenceException;

import java.util.stream.Stream;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;

public class ValsUriBuilderTest {

    private static Stream<Arguments> valsUriCases() {
        return Stream.of(
                Arguments.of(
                        SecretStoreDTO.builder().type(SecretStoreType.vault).mountPath("secret").build(),
                        "ref+vault://secret/cluster/env/cred"
                ),
                Arguments.of(
                        SecretStoreDTO.builder().type(SecretStoreType.azure).vaultName("myvault").build(),
                        "ref+azurekeyvault://myvault/cluster--env--cred"
                ),
                Arguments.of(
                        SecretStoreDTO.builder().type(SecretStoreType.aws).region("eu-west-1").build(),
                        "ref+awssecrets://cluster/env/cred?region=eu-west-1"
                ),
                Arguments.of(
                        SecretStoreDTO.builder().type(SecretStoreType.gcp).projectId("project1").build(),
                        "ref+gcpsecrets://project1/cluster--env--cred"
                )
        );
    }

    @ParameterizedTest
    @MethodSource("valsUriCases")
    void buildValsUriTest(SecretStoreDTO store, String expectedUri) {
        String result = ValsUriBuilder.buildValsUri( "cred", "cluster/env","default_store", store);
        assertEquals(expectedUri, result);
    }

    @Test
    void appendStoreIdForNonDefaultStore() {
        SecretStoreDTO store = SecretStoreDTO.builder().type(SecretStoreType.azure).vaultName("myvault").build();
        String result = ValsUriBuilder.buildValsUri("cred", "cluster/env", "my_store", store);
        assertEquals("ref+azurekeyvault://myvault/cluster--env--cred?secret_store_id=my_store", result);
    }

    @Test
    void ampersandForAwsSecretStoreId() {
        SecretStoreDTO store = SecretStoreDTO.builder().type(SecretStoreType.aws).region("eu-west-1").build();
        String result = ValsUriBuilder.buildValsUri( "cred", "cluster/env","my_store", store);
        assertEquals("ref+awssecrets://cluster/env/cred?region=eu-west-1&secret_store_id=my_store", result);
    }

    @Test
    void exceptionForInvalidSecretNameInput() {
        SecretStoreDTO store = SecretStoreDTO.builder().type(SecretStoreType.azure).vaultName("myvault").build();
        assertThrows(SecretReferenceException.class,
                () -> ValsUriBuilder.buildValsUri("cred", "", "default_store", store));
    }
}
