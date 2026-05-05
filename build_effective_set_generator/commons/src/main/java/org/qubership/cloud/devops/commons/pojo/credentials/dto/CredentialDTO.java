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
import com.fasterxml.jackson.databind.annotation.JsonDeserialize;
import lombok.Builder;
import lombok.Data;
import lombok.extern.jackson.Jacksonized;
import org.qubership.cloud.devops.commons.pojo.credentials.model.Credential;
import org.qubership.cloud.devops.commons.pojo.credentials.model.CredentialsTypeEnum;
import org.qubership.cloud.devops.commons.utils.deserializer.CredentialDTODeserializer;

import java.util.List;


@Data
@Builder
@JsonPropertyOrder
@JsonDeserialize(using = CredentialDTODeserializer.class)
public class CredentialDTO {
    private final String credentialsId;
    @JsonFormat(shape = JsonFormat.Shape.STRING)
    private final CredentialsTypeEnum type;
    private final Credential data;
    private final String description;
    private final Boolean create;
    private final String secretStore;
    private final List<Property> properties;
    private final String remoteRefPath;

    @Data
    public static class Property {
        private String name;
    }
}
