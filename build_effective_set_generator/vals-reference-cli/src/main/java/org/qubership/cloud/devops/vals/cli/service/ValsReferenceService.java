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

package org.qubership.cloud.devops.vals.cli.service;

import jakarta.enterprise.context.ApplicationScoped;
import jakarta.validation.Valid;
import org.qubership.cloud.devops.vals.cli.dto.ValsUriRequest;
import org.qubership.cloud.devops.vals.core.ValsUriBuilder;

import java.util.LinkedHashMap;
import java.util.Map;

@ApplicationScoped
public class ValsReferenceService {

    public Map<String, String> buildValsReferenceMap(@Valid ValsUriRequest request) {
        Map<String, String> result = new LinkedHashMap<>();

        String uri = ValsUriBuilder.buildValsUri(
                request.getCredentialId(),
                request.getCredential().getRemoteRefPath(),
                request.getCredential().getSecretStore(),
                request.getSecretStore()
        );
        result.put(request.getCredentialId(), uri);

        return result;
    }
}

