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

import org.junit.jupiter.api.Test;
import org.qubership.cloud.devops.vals.cli.TestDataFactory;
import org.qubership.cloud.devops.vals.cli.dto.ValsUriRequest;

import java.util.Map;

import static org.junit.jupiter.api.Assertions.assertEquals;

public class ValsReferenceServiceTest {
    private final ValsReferenceService service = new ValsReferenceService();

    @Test
    void buildValsReferenceMap() {
        ValsUriRequest request = TestDataFactory.createValidRequest().build();

        Map<String, String> result = service.buildValsReferenceMap(request);

        assertEquals(1, result.size());
        assertEquals(
                "ref+vault://secret/data/cluster/env/app-custom-cred?secret_store_id=vault_store",
                result.get("app-custom-cred"));
    }
}
