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

package org.qubership.cloud.devops.commons.utils;

import org.qubership.cloud.devops.commons.pojo.credentials.model.Credential;
import org.qubership.cloud.devops.commons.pojo.credentials.model.UsernamePasswordCredentials;
import org.apache.commons.codec.binary.Base64;

import java.nio.charset.StandardCharsets;

public interface CredentialUtils {


    Credential getCredentialsById(String id);

    default String getCredentialsBasicAuthHeader(String credentialId) {
        var credentials =
                (UsernamePasswordCredentials) getCredentialsById(credentialId);
        if (credentials == null) {
            return null;
        }
        final String auth = credentials.getUsername() + ":" + credentials.getPassword();
        final byte[] encodedAuth = Base64.encodeBase64(auth.getBytes(StandardCharsets.ISO_8859_1));
        return "Basic " + new String(encodedAuth, StandardCharsets.UTF_8);
    }
}
