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

package org.qubership.cloud.devops.commons.utils.deserializer;

import com.fasterxml.jackson.core.JsonParser;
import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.DeserializationContext;
import com.fasterxml.jackson.databind.JsonDeserializer;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.qubership.cloud.devops.commons.pojo.credentials.dto.*;
import org.qubership.cloud.devops.commons.pojo.credentials.model.Credential;
import org.qubership.cloud.devops.commons.pojo.credentials.model.CredentialsTypeEnum;

import java.io.IOException;
import java.util.List;
import java.util.Map;

public class CredentialDTODeserializer extends JsonDeserializer<CredentialDTO> {

    private final ObjectMapper mapper = new ObjectMapper();

    @Override
    public CredentialDTO deserialize(JsonParser p, DeserializationContext ctxt) throws IOException {
        String credId = p.currentName();
        Map<String, Object> node = p.readValueAs(Map.class);
        CredentialsTypeEnum type =
                CredentialsTypeEnum.valueOf(((String) node.get("type")));

        CredentialDTO.CredentialDTOBuilder builder = CredentialDTO.builder()
                .type(type)
                .credentialsId(credId);
        if (type == CredentialsTypeEnum.external) {
            String secretStore = (String) node.get("secretStore");
            if (secretStore == null || secretStore.isBlank()) {
                secretStore = "default_store";
            }
            builder.create((Boolean) node.getOrDefault("create", Boolean.FALSE))
                    .secretStore(secretStore)
                    .remoteRefPath((String) node.get("remoteRefPath"))
                    .properties(convertProps(node.get("properties")));
        } else {
            Object dataNode = node.get("data");
            if (dataNode != null) {
                Credential data;
                switch (type) {
                    case usernamePassword:
                        data = mapper.convertValue(dataNode, UsernamePasswordCredentialsDTO.class);
                        break;

                    case secret:
                        data = mapper.convertValue(dataNode, SecretCredentialsDTO.class);
                        break;

                    case secretFile:
                        data = mapper.convertValue(dataNode, SecretFileCredentialsDTO.class);
                        break;

                    case vaultAppRole:
                        data = mapper.convertValue(dataNode, VaultAppRoleCredentialsDTO.class);
                        break;

                    default:
                        throw new IllegalArgumentException("Unsupported type: " + type);
                }
                builder.data(data);
            }
            builder.description((String) node.get("description"));
        }
        return builder.build();
    }

    private List<CredentialDTO.Property> convertProps(Object obj) {
        if (obj == null) return null;
        return mapper.convertValue(obj, new TypeReference<List<CredentialDTO.Property>>() {});
    }
}
