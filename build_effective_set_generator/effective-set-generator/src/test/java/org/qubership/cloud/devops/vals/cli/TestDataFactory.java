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

package org.qubership.cloud.devops.vals.cli;

import org.qubership.cloud.devops.vals.cli.dto.CredentialRequest;
import org.qubership.cloud.devops.vals.cli.dto.ValsUriRequest;
import org.qubership.cloud.devops.vals.core.dto.SecretStoreDTO;
import org.qubership.cloud.devops.vals.core.dto.SecretStoreType;

public class TestDataFactory {
    public static ValsUriRequest.ValsUriRequestBuilder createValidRequest() {
        CredentialRequest credential = CredentialRequest.builder()
                .remoteRefPath("cluster/env")
                .secretStore("vault_store")
                .build();

        SecretStoreDTO store = SecretStoreDTO.builder()
                .type(SecretStoreType.vault)
                .mountPath("secret")
                .build();

        return ValsUriRequest.builder()
                .credentialId("app-custom-cred")
                .credential(credential)
                .secretStore(store);
    }
}
