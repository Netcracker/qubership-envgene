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

import java.util.List;

public final class ValsReferenceBuilder {

    private ValsReferenceBuilder() {
    }

    public static String buildValsReference(
            String credId,
            String remoteRefPath,
            String property,
            List<String> propertyNames,
            SecretStoreConfig store
    ) {
        String normalizedSecretName = SecretNameBuilder.buildNormalizedSecretName(
                remoteRefPath, credId, store.getType());
        String fragment = ValsFragmentBuilder.buildFragment(credId, property, propertyNames, store.getType());
        return ValsUriBuilder.buildValsUri(store, normalizedSecretName, fragment);
    }

    public static String buildNormalizedSecretName(String credId, String remoteRefPath, SecretStoreConfig store) {
        return SecretNameBuilder.buildNormalizedSecretName(remoteRefPath, credId, store.getType());
    }
}
