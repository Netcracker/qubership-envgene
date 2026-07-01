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

final class ValsRefMessages {

    static final String NORMALIZATION_INPUT_ERROR =
            "Inputs to build Normalized secret name is null. remoteRefPath = %s, credId = %s, secretStoreType = %s";
    static final String UNSUPPORTED_SECRET_TYPE =
            "Unsupported secret store type: '%s' for credId [%s] and remoteRefPath [%s]. Supported are vault, aws, gcp, azure.";
    static final String INVALID_CHARACTER =
            "Invalid characters in %s [%s] for type %s. %n Allowed pattern: %s. %n Please validate cred id and remoteRefPath.";
    static final String INVALID_LENGTH = "Length exceeded for %s [%s] for type %s. Max allowed: %d, actual: %d";
    static final String MULTI_PROPERTY_ERROR =
            "Credential in external template has properties but no property provided in cred '%s' referenced in parameter";
    static final String SINGLE_PROPERTY_ERROR =
            "No properties defined for credential %s in external credential template.";
    static final String INVALID_PROPERTY =
            "Invalid property '%s' referred in parameter for external credential id '%s'.";

    private ValsRefMessages() {
    }
}
