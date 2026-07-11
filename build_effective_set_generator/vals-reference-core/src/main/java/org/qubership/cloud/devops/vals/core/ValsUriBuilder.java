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

import org.qubership.cloud.devops.vals.core.dto.SecretStoreDTO;
import org.qubership.cloud.devops.vals.core.dto.SecretStoreType;

import static org.qubership.cloud.devops.vals.core.constants.SecretReferenceConstants.DEFAULT_STORE;

public class ValsUriBuilder {

    public static String buildValsUri(String credId, String remoteRefPath,
                                      String secretStoreId, SecretStoreDTO store) {
        String normalizedName = SecretNameBuilder.buildNormalizedSecretName(
                remoteRefPath, credId, store.getType());
        return buildBaseValsUri(store, normalizedName, secretStoreId);


    }

    private static String buildBaseValsUri(SecretStoreDTO store, String normalizedSecretName, String secretStoreId) {
        SecretStoreType type = store.getType();
        String baseUri = switch (type) {
            case vault -> "ref+vault://" + store.getMountPath() + "/" + normalizedSecretName;
            case azure -> "ref+azurekeyvault://" + store.getVaultName() + "/" + normalizedSecretName;
            case aws -> "ref+awssecrets://" + normalizedSecretName + "?region=" + store.getRegion();
            case gcp -> "ref+gcpsecrets://" + store.getProjectId() + "/" + normalizedSecretName;
        };
        if (DEFAULT_STORE.equals(secretStoreId)) {
            return baseUri;
        }
        String separator = (type == SecretStoreType.aws) ? "&" : "?";
        return baseUri + separator + "secret_store_id=" + secretStoreId;
    }
}
