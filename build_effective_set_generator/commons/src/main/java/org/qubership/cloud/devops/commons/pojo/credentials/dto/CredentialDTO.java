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

package org.qubership.cloud.devops.commons.pojo.credentials.dto;

import com.fasterxml.jackson.annotation.JsonFormat;
import com.fasterxml.jackson.annotation.JsonPropertyOrder;
import com.fasterxml.jackson.annotation.JsonSubTypes;
import com.fasterxml.jackson.annotation.JsonTypeInfo;
import lombok.Builder;
import lombok.Data;
import lombok.extern.jackson.Jacksonized;
import org.qubership.cloud.devops.commons.pojo.credentials.model.Credential;
import org.qubership.cloud.devops.commons.pojo.credentials.model.CredentialsTypeEnum;

@Jacksonized
@Data
@Builder
@JsonPropertyOrder
public class CredentialDTO {
    private final String credentialsId;
    @JsonFormat(shape = JsonFormat.Shape.STRING)
    private final CredentialsTypeEnum type;
    @JsonTypeInfo(use = JsonTypeInfo.Id.NAME, property = "type", include = JsonTypeInfo.As.EXTERNAL_PROPERTY)
    @JsonSubTypes(value = {
            @JsonSubTypes.Type(value = SecretCredentialsDTO.class, name = CredentialsTypeEnum.Constants.SECRET_VALUE),
            @JsonSubTypes.Type(value = SecretFileCredentialsDTO.class, name = CredentialsTypeEnum.Constants.SECRET_FILE_VALUE),
            @JsonSubTypes.Type(value = UsernamePasswordCredentialsDTO.class, name = CredentialsTypeEnum.Constants.USERNAME_PASSWORD_VALUE),
            @JsonSubTypes.Type(value = VaultAppRoleCredentialsDTO.class, name = CredentialsTypeEnum.Constants.VAULT_APP_ROLE_VALUE)
    })
    private final Credential data;
    private final String description;
}
