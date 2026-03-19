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

package org.qubership.cloud.devops.cli.repository.implementation;

import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.dataformat.yaml.YAMLFactory;
import org.cyclonedx.model.Bom;
import org.qubership.cloud.devops.cli.exceptions.constants.ExceptionMessage;
import org.qubership.cloud.devops.cli.utils.FileSystemUtils;
import org.qubership.cloud.devops.cli.utils.deserializer.BomMixin;
import org.qubership.cloud.devops.commons.exceptions.FileParseException;
import org.qubership.cloud.devops.commons.exceptions.JsonParseException;
import org.qubership.cloud.devops.commons.repository.interfaces.FileDataConverter;
import jakarta.enterprise.context.ApplicationScoped;
import jakarta.inject.Inject;
import lombok.extern.slf4j.Slf4j;
import org.yaml.snakeyaml.DumperOptions;
import org.yaml.snakeyaml.Yaml;
import org.yaml.snakeyaml.nodes.Node;
import org.yaml.snakeyaml.nodes.Tag;
import org.yaml.snakeyaml.representer.Representer;

import java.io.*;
import java.util.Base64;
import java.util.Map;
import java.util.TreeMap;

import static org.qubership.cloud.devops.commons.utils.ConsoleLogger.logError;


@ApplicationScoped
@Slf4j
public class FileDataConverterImpl implements FileDataConverter {
    public static final String CLEANUPER = "cleanuper";
    private final ObjectMapper objectMapper;
    private final FileSystemUtils fileSystemUtils;

    @Inject
    public FileDataConverterImpl(FileSystemUtils fileSystemUtils) {
        this.fileSystemUtils = fileSystemUtils;
        this.objectMapper = new ObjectMapper(new YAMLFactory());
    }

    @Override
    public <T> T parseInputFile(Class<T> type, File file) {
        try (InputStream inputStream = new FileInputStream(file)) {
            return objectMapper.readValue(inputStream, type);
        } catch (IOException | IllegalArgumentException e) {
            logError(String.format(ExceptionMessage.FILE_READ_ERROR, file.getAbsolutePath(), e.getMessage()));
            return null;
        }
    }

    @Override
    public Bom parseSbomFile(File file) {
        try {
            ObjectMapper bomMapper = new ObjectMapper();
            bomMapper.addMixIn(Bom.class, BomMixin.class);
            return bomMapper.readValue(file, Bom.class);
        } catch (IOException | IllegalArgumentException e) {
            if (file.getName().startsWith(CLEANUPER) &&
                    e instanceof FileNotFoundException) {
                logError("Issue while reading the file " + e.getMessage());
                return null;
            }
            throw new FileParseException(String.format(ExceptionMessage.FILE_READ_ERROR, file.getAbsolutePath(), e.getMessage()));
        }
    }


    @Override
    public <T> T parseInputFile(TypeReference<T> typeReference, File file) {
        try (InputStream inputStream = new FileInputStream(file)) {
            return objectMapper.readValue(inputStream, typeReference);
        } catch (IOException | IllegalArgumentException e) {
            logError(String.format(ExceptionMessage.FILE_READ_ERROR, file.getAbsolutePath(), e.getMessage()));
            return null;
        }
    }

    @Override
    public void writeToFile(Map<String, Object> params, String... args) throws IOException {
        File file = fileSystemUtils.getFileFromGivenPath(args);
        try (BufferedWriter writer = new BufferedWriter(new FileWriter(file))) {
            if (params != null && !params.isEmpty()) {
                getYamlObject().dump(params, writer);
            }
        }
    }


    @Override
    public <T> Map<String, Object> getObjectMap(T inputObject) {
        ObjectMapper objectMapper = new ObjectMapper();
        return objectMapper.convertValue(inputObject, new TypeReference<Map<String, Object>>() {
        });
    }


    private static Yaml getYamlObject() {
        DumperOptions options = new DumperOptions();
        options.setDefaultFlowStyle(DumperOptions.FlowStyle.BLOCK);
        options.setDefaultScalarStyle(DumperOptions.ScalarStyle.PLAIN);
        options.setPrettyFlow(false);
        Representer representer = new Representer(options) {
            @Override
            protected Node representScalar(Tag tag, String value, DumperOptions.ScalarStyle style) {
                if (value.equals("!merge")) {
                    value = "<<";
                    Node node = super.representScalar(tag, value, style);
                    node.setTag(Tag.MERGE);
                    return node;

                } else {
                    return super.representScalar(tag, value, style);
                }
            }


        };
        return new Yaml(representer, options);
    }

    public <T> T decodeAndParse(String encodedText, TypeReference<T> typeReference) {
        try {
            byte[] decoded = Base64.getDecoder().decode(encodedText);
            return objectMapper.readValue(decoded, typeReference);
        } catch (IOException e) {
            throw new JsonParseException("Failed to parse encoded content", e);
        }
    }

    public <T> T decodeAndParse(String encodedText, Class<T> clazz) {
        try {
            byte[] decoded = Base64.getDecoder().decode(encodedText);
            return objectMapper.readValue(decoded, clazz);
        } catch (IOException e) {
            throw new JsonParseException("Failed to parse encoded content", e);
        }
    }


}
