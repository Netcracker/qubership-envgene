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

package org.qubership.cloud.devops.commons.pojo.credentials.model;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;
import org.qubership.cloud.devops.commons.pojo.credentials.dto.CredentialDTO;

import java.util.List;

@Data
@NoArgsConstructor
@AllArgsConstructor
public class ExternalCredentials implements Credential {
    private  Boolean create;
    private  String secretStore;
    private  List<CredentialDTO.Property> properties;
    private  String remoteRefPath;
}
