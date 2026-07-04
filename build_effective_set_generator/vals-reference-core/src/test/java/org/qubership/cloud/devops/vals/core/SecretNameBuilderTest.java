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
import org.qubership.cloud.devops.vals.core.dto.SecretStoreType;
import org.qubership.cloud.devops.vals.core.exceptions.SecretReferenceException;

import java.util.stream.Stream;

import static org.junit.jupiter.api.Assertions.*;

public class SecretNameBuilderTest {
    private static Stream<Arguments> validSecretNameCases() {
        return Stream.of(
                Arguments.of("vault", "cred-id", "cluster/env", "cluster/env/cred-id"),
                Arguments.of("azure", "cred-id", "cluster/env", "cluster--env--cred-id"),
                Arguments.of("aws", "cred-id", "cluster/env", "cluster/env/cred-id"),
                Arguments.of("gcp", "cred-id", "cluster/env", "cluster--env--cred-id")
        );
    }

    @ParameterizedTest
    @MethodSource("validSecretNameCases")
    void buildNormalizedSecretName(String type, String credId, String remoteRefPath, String expected) {
        SecretStoreType storeType = SecretStoreType.valueOf(type);
        String result = SecretNameBuilder.buildNormalizedSecretName(remoteRefPath, credId, storeType);
        assertEquals(expected, result);
    }

    @Test
    void exceptionWhenCredIdExceedsMaxLength() {
        String credId = "a".repeat(251);
        assertThrows(
                SecretReferenceException.class,
                () -> SecretNameBuilder.buildNormalizedSecretName("path", credId, SecretStoreType.aws)
        );
    }

    @Test
    void exceptionWhenNormalizedSecretNameContainsInvalidCharacters() {
        SecretReferenceException ex = assertThrows(
                SecretReferenceException.class,
                () -> SecretNameBuilder.buildNormalizedSecretName("remote_ref_path", "cred", SecretStoreType.azure)
        );

        assertTrue(ex.getMessage().contains("Invalid"));
    }

    @Test
    void exceptionWhenNullRemoteRefPath() {
        assertThrows(SecretReferenceException.class,
                () -> SecretNameBuilder.buildNormalizedSecretName(null, "cred", SecretStoreType.vault));
    }

    @Test
    void truncateWhenSegmentExceedsMaxLength() {
        String longSegment = "abcdefghijklmnopqrstuvwxyz";
        String result = SecretNameBuilder.buildNormalizedSecretName(longSegment, "credId", SecretStoreType.azure);
        assertEquals("abcdefghijklmn-71c48--credId", result);
    }
}
