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

package org.qubership.cloud.devops.commons.utils.convert;


import com.fasterxml.jackson.core.JsonParser;
import com.fasterxml.jackson.databind.DeserializationContext;
import com.fasterxml.jackson.databind.JsonDeserializer;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.dataformat.yaml.YAMLFactory;
import com.fasterxml.jackson.dataformat.yaml.YAMLGenerator;
import org.yaml.snakeyaml.error.YAMLException;

import java.io.IOException;
import java.util.HashMap;
import java.util.Iterator;
import java.util.Map;

public class CustomDeserializer extends JsonDeserializer<Map<String, Object>> {

    @Override
    public Map<String, Object> deserialize(JsonParser jsonParser, DeserializationContext deserializationContext) {
        try {
            JsonNode configNode = jsonParser.getCodec().readTree(jsonParser);
            Iterator<Map.Entry<String, JsonNode>> fields = configNode.fields();
            Map<String, Object> finals = new HashMap<>();

            YAMLFactory yamlFactory = new YAMLFactory();
            yamlFactory.disable(YAMLGenerator.Feature.WRITE_DOC_START_MARKER);
            ObjectMapper objectMapper = new ObjectMapper(yamlFactory);
            while (fields.hasNext()) {
                Map.Entry<String, JsonNode> entry = fields.next();
                JsonNode type = entry.getValue();
                if (type.isArray() || type.isObject()) {
                    String input = objectMapper.writerWithDefaultPrettyPrinter().writeValueAsString(type);
                    String finalString = "'" + input + "'";
                    finals.put(entry.getKey(), finalString);
                } else if (type.isDouble()) {
                    finals.put(entry.getKey(), entry.getValue().doubleValue());
                } else if (type.isInt()) {
                    finals.put(entry.getKey(), entry.getValue().intValue());
                } else if (type.isBoolean()) {
                    finals.put(entry.getKey(), entry.getValue().booleanValue());
                } else if (type.isBigDecimal()) {
                    finals.put(entry.getKey(), entry.getValue().decimalValue());
                } else {
                    finals.put(entry.getKey(), !type.isNull() ? type.asText() : "");
                }
            }
            return finals;
        } catch (IOException e) {
            throw new YAMLException(e.getMessage());
        }
    }
}
