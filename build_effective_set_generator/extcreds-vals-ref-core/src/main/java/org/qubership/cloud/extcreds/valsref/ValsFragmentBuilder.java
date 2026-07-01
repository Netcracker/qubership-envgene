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

import static org.qubership.cloud.extcreds.valsref.ValsRefMessages.*;

public final class ValsFragmentBuilder {

    private ValsFragmentBuilder() {
    }

    /**
     * Builds the URI fragment suffix for a VALS reference from credential shape and optional property.
     *
     * @param credId         credential identifier (used in validation error messages)
     * @param property       optional property from a credRef; {@code null} for single-value credentials
     * @param propertyNames  names from {@code Credential.properties}; empty or {@code null} for single-value
     * @param storeType      target secret store type
     * @return fragment string such as {@code #/username}, {@code #/value}, or empty string
     */
    public static String buildFragment(String credId, String property, List<String> propertyNames, SecretStoreType storeType) {
        if (property != null) {
            validateMultiValProperty(propertyNames, credId, property);
            return "#/" + property;
        }
        validateSingleValProperty(credId, propertyNames);
        if (storeType == SecretStoreType.vault) {
            return "#/value";
        }
        return "";
    }

    public static void validateSingleValProperty(String credId, List<String> propertyNames) {
        if (propertyNames != null && !propertyNames.isEmpty()) {
            throw new ExternalCredValsException(String.format(MULTI_PROPERTY_ERROR, credId));
        }
    }

    public static void validateMultiValProperty(List<String> propertyNames, String credId, String property) {
        if (propertyNames == null || propertyNames.isEmpty()) {
            throw new ExternalCredValsException(String.format(SINGLE_PROPERTY_ERROR, credId));
        }
        boolean exists = propertyNames.stream().anyMatch(property::equals);
        if (!exists) {
            throw new ExternalCredValsException(String.format(INVALID_PROPERTY, property, credId));
        }
    }
}
