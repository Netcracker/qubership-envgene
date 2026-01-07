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
import jakarta.enterprise.context.ApplicationScoped;
import jakarta.inject.Inject;
import lombok.extern.slf4j.Slf4j;
import org.cyclonedx.model.Bom;
import org.qubership.cloud.devops.cli.exceptions.constants.ExceptionMessage;
import org.qubership.cloud.devops.cli.pojo.dto.shared.SharedData;
import org.qubership.cloud.devops.cli.utils.FileSystemUtils;
import org.qubership.cloud.devops.commons.exceptions.FileParseException;
import org.qubership.cloud.devops.commons.exceptions.JsonParseException;
import org.qubership.cloud.devops.commons.repository.interfaces.FileDataConverter;
import org.qubership.cloud.devops.commons.utils.Parameter;
import org.yaml.snakeyaml.DumperOptions;
import org.yaml.snakeyaml.Yaml;
import org.yaml.snakeyaml.comments.CommentLine;
import org.yaml.snakeyaml.comments.CommentType;
import org.yaml.snakeyaml.nodes.*;
import org.yaml.snakeyaml.representer.Represent;
import org.yaml.snakeyaml.representer.Representer;

import java.io.*;
import java.util.*;

import static org.qubership.cloud.devops.commons.utils.ConsoleLogger.logError;

/*@ApplicationScoped*/
@Slf4j
public class FileDataConverterNewImpl implements FileDataConverter {

    private static final Set<String> EXCLUDED_FILES = Set.of("mapping.yaml");

    private final ObjectMapper objectMapper;
    private final FileSystemUtils fileSystemUtils;
    private final SharedData sharedData;

    @Inject
    public FileDataConverterNewImpl(FileSystemUtils fileSystemUtils, SharedData sharedData) {
        this.fileSystemUtils = fileSystemUtils;
        this.sharedData = sharedData;
        this.objectMapper = new ObjectMapper(new YAMLFactory());
    }

    // ================= WRITE =================

    @Override
    public void writeToFile(Map<String, Object> params, String... args) throws IOException {
        boolean enableTraceability =
                sharedData != null && sharedData.isEnableTraceability();
        writeToFileInternal(params, enableTraceability, args);
    }

    @Override
    public void writeToFile(Map<String, Object> params,
                            boolean enableTraceability,
                            String... args) throws IOException {
        writeToFileInternal(params, enableTraceability, args);
    }

    private void writeToFileInternal(Map<String, Object> params,
                                     boolean enableTraceability,
                                     String... args) throws IOException {

        if (params == null || params.isEmpty()) {
            return;
        }

        File file = fileSystemUtils.getFileFromGivenPath(args);
        boolean skipComments = EXCLUDED_FILES.contains(file.getName());

        DumperOptions options = new DumperOptions();
        options.setDefaultFlowStyle(DumperOptions.FlowStyle.BLOCK);
        options.setPrettyFlow(true);

        CommentRepresenter representer =
                new CommentRepresenter(options, enableTraceability && !skipComments);

        Yaml yaml = new Yaml(representer, options);

        try (BufferedWriter writer = new BufferedWriter(new FileWriter(file, false))) {
            yaml.dump(params, writer);
        }
    }

    // ================= CUSTOM REPRESENTER =================

    private static final class CommentRepresenter extends Representer {

        private final boolean enableComments;

        CommentRepresenter(DumperOptions options, boolean enableComments) {
            super(options);
            this.enableComments = enableComments;

            // Custom representers (SnakeYAML 2.x compliant)
            this.representers.put(Parameter.class, new RepresentParameter());
            this.representers.put(String.class, new RepresentString());

            // multiRepresenters handle subclasses (LinkedHashMap, ArrayList, etc.)
            this.multiRepresenters.put(Map.class, new RepresentMap());
            this.multiRepresenters.put(List.class, new RepresentList());
        }

        @Override
        protected Node representMapping(Tag tag,
                                        Map<?, ?> mapping,
                                        DumperOptions.FlowStyle flowStyle) {

            MappingNode node =
                    (MappingNode) super.representMapping(tag, mapping, flowStyle);

            if (!enableComments) {
                return node;
            }

            List<NodeTuple> newTuples = new ArrayList<>();

            for (NodeTuple tuple : node.getValue()) {

                Node keyNode = tuple.getKeyNode();
                Node valueNode = tuple.getValueNode();

                if (keyNode instanceof ScalarNode keyScalar) {

                    Object originalValue = mapping.get(keyScalar.getValue());

                    if (originalValue instanceof Parameter param) {

                        valueNode = representData(param.getValue());

                        String origin = param.getOrigin();
                        if (origin != null && !origin.isBlank()) {

                            boolean multiline =
                                    valueNode instanceof ScalarNode scalar &&
                                            scalar.getValue() != null &&
                                            scalar.getValue().contains("\n");

                            CommentLine comment = new CommentLine(
                                    null,
                                    null,
                                    origin,
                                    multiline
                                            ? CommentType.BLOCK
                                            : CommentType.IN_LINE
                            );

                            if (multiline) {
                                keyNode.setBlockComments(
                                        new ArrayList<>(List.of(comment)));
                            } else if (valueNode instanceof ScalarNode scalar) {
                                scalar.setInLineComments(
                                        new ArrayList<>(List.of(comment)));
                            }
                        }

                        newTuples.add(new NodeTuple(keyNode, valueNode));
                        continue;
                    }
                }

                newTuples.add(tuple);
            }

            return new MappingNode(tag, newTuples, flowStyle);
        }

        // ================= REPRESENT IMPLEMENTATIONS =================

        private final class RepresentParameter implements Represent {
            @Override
            public Node representData(Object data) {
                Parameter p = (Parameter) data;
                return representData(p.getValue());
            }
        }

        private final class RepresentString implements Represent {
            @Override
            public Node representData(Object data) {
                String value = (String) data;
                boolean multiline = value.contains("\n");

                return new ScalarNode(
                        Tag.STR,
                        value,
                        null,
                        null,
                        multiline
                                ? DumperOptions.ScalarStyle.LITERAL
                                : DumperOptions.ScalarStyle.PLAIN
                );
            }
        }

        private final class RepresentList implements Represent {
            @Override
            public Node representData(Object data) {
                List<?> list = (List<?>) data;
                List<Node> nodes = new ArrayList<>(list.size());
                for (Object item : list) {
                    nodes.add(representData(item));
                }
                return new SequenceNode(
                        Tag.SEQ,
                        nodes,
                        DumperOptions.FlowStyle.BLOCK
                );
            }
        }

        private final class RepresentMap implements Represent {
            @Override
            public Node representData(Object data) {
                return representMapping(
                        Tag.MAP,
                        (Map<?, ?>) data,
                        DumperOptions.FlowStyle.BLOCK
                );
            }
        }
    }

    // ================= READ =================

    @Override
    public <T> T parseInputFile(Class<T> type, File file) {
        try (InputStream inputStream = new FileInputStream(file)) {
            return objectMapper.readValue(inputStream, type);
        } catch (IOException | IllegalArgumentException e) {
            logError(String.format(
                    ExceptionMessage.FILE_READ_ERROR,
                    file.getAbsolutePath(),
                    e.getMessage()
            ));
            return null;
        }
    }

    @Override
    public <T> T parseInputFile(TypeReference<T> typeReference, File file) {
        try (InputStream inputStream = new FileInputStream(file)) {
            return objectMapper.readValue(inputStream, typeReference);
        } catch (IOException | IllegalArgumentException e) {
            logError(String.format(
                    ExceptionMessage.FILE_READ_ERROR,
                    file.getAbsolutePath(),
                    e.getMessage()
            ));
            return null;
        }
    }

    @Override
    public Bom parseSbomFile(File file) {
        try {
            return new ObjectMapper().readValue(file, Bom.class);
        } catch (IOException | IllegalArgumentException e) {
            throw new FileParseException(
                    String.format(
                            ExceptionMessage.FILE_READ_ERROR,
                            file.getAbsolutePath(),
                            e.getMessage()
                    )
            );
        }
    }

    @Override
    public <T> Map<String, Object> getObjectMap(T inputObject) {
        return objectMapper.convertValue(
                inputObject,
                new TypeReference<Map<String, Object>>() {});
    }

    public <T> T decodeAndParse(String encodedText,
                                TypeReference<T> typeReference) {
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
