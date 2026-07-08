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

package org.qubership.cloud.devops.cli.utils;

import io.quarkus.arc.Unremovable;
import jakarta.enterprise.context.ApplicationScoped;
import jakarta.inject.Inject;
import org.qubership.cloud.devops.cli.pojo.dto.input.InputData;
import org.qubership.cloud.devops.commons.pojo.extcreds.SecretStoreDTO;
import org.qubership.cloud.devops.commons.utils.SecretStoresUtils;

import java.util.Map;

@ApplicationScoped
@Unremovable
public class SecretStoreUtilsCliImpl implements SecretStoresUtils {

    private final InputData inputData;

    @Inject
    public SecretStoreUtilsCliImpl(InputData inputData) {
        this.inputData = inputData;
    }

    @Override
    public SecretStoreDTO getStoresById(String id) {
        Map<String, SecretStoreDTO> secretStoreMap = inputData.getSecretStoreDTOMap();
        SecretStoreDTO secretStoreDTO = secretStoreMap.get(id);
        if (secretStoreDTO == null) {
            return null;
        }
        return secretStoreDTO;
    }
}
