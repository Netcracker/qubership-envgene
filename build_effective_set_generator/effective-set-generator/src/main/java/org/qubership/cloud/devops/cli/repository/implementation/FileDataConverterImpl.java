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
import org.qubership.cloud.devops.cli.pojo.dto.shared.SharedData;
import org.qubership.cloud.devops.cli.utils.FileSystemUtils;
import org.qubership.cloud.devops.cli.utils.deserializer.BomMixin;
import org.qubership.cloud.devops.commons.exceptions.FileParseException;
import org.qubership.cloud.devops.commons.exceptions.JsonParseException;
import org.qubership.cloud.devops.commons.repository.interfaces.FileDataConverter;
import jakarta.enterprise.context.ApplicationScoped;
import jakarta.inject.Inject;
import lombok.extern.slf4j.Slf4j;
import org.qubership.cloud.devops.commons.utils.Parameter;
import org.snakeyaml.engine.v2.api.Dump;
import org.snakeyaml.engine.v2.api.DumpSettings;
import org.snakeyaml.engine.v2.api.StreamDataWriter;
import org.snakeyaml.engine.v2.comments.CommentLine;
import org.snakeyaml.engine.v2.comments.CommentType;
import org.snakeyaml.engine.v2.common.FlowStyle;
import org.snakeyaml.engine.v2.common.ScalarStyle;
import org.snakeyaml.engine.v2.nodes.MappingNode;
import org.snakeyaml.engine.v2.nodes.NodeTuple;
import org.snakeyaml.engine.v2.nodes.ScalarNode;
import org.snakeyaml.engine.v2.nodes.SequenceNode;
import org.yaml.snakeyaml.DumperOptions;
import org.yaml.snakeyaml.Yaml;
import org.yaml.snakeyaml.nodes.Node;
import org.yaml.snakeyaml.nodes.Tag;
import org.yaml.snakeyaml.representer.Representer;

import java.io.*;
import java.util.*;

import static org.qubership.cloud.devops.commons.utils.ConsoleLogger.logError;


@ApplicationScoped
@Slf4j
public class FileDataConverterImpl implements FileDataConverter {
    public static final String CLEANUPER = "cleanuper";
    private final ObjectMapper objectMapper;
    private final FileSystemUtils fileSystemUtils;
    private final SharedData sharedData;
    private static final Set<String> EXCLUDED_FILES = Set.of("mapping.yaml");

    @Inject
    public FileDataConverterImpl(FileSystemUtils fileSystemUtils, SharedData sharedData) {
        this.fileSystemUtils = fileSystemUtils;
        this.sharedData = sharedData;
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
        boolean enableTraceability = sharedData != null && sharedData.isEnableTraceability() && !EXCLUDED_FILES.contains(file.getName());
        try (BufferedWriter writer = new BufferedWriter(new FileWriter(file))) {
            if (params != null && !params.isEmpty()) {
               String yamlContent = dump(params,enableTraceability);
               writer.write(yamlContent);
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

    public String dump(Map<String, Object> data,boolean enableTraceability) {
        org.snakeyaml.engine.v2.nodes.Node rootNode = toNode(data,enableTraceability);
        DumpSettings settings = DumpSettings.builder()
                .setDumpComments(true)
                .setDefaultFlowStyle(FlowStyle.BLOCK)
                .build();
        Dump dump = new Dump(settings);
        StringStreamWriter writer = new StringStreamWriter();
        dump.dumpNode(rootNode, writer);
        return writer.toString();
    }

    /** Collects emitted YAML into a string. */
    private static final class StringStreamWriter extends StringWriter implements StreamDataWriter {
    }

    // ============================================================
    // Core Recursive Builder
    // ============================================================

    private org.snakeyaml.engine.v2.nodes.Node toNode(Object input,boolean enableTraceability) {

        String origin = null;
        Object value = input;

        if (input instanceof Parameter commonsParam) {
            origin = commonsParam.getOrigin();
            value = commonsParam.getValue();
        }

        // ---------------- NULL ----------------
        if (value == null) {
            ScalarNode node = new ScalarNode(org.snakeyaml.engine.v2.nodes.Tag.NULL, "null", ScalarStyle.PLAIN);
            return shouldAddComment(enableTraceability, origin) ? attachInline(node, origin) : node;
        }

        // ---------------- STRING ----------------
        if (value instanceof String str) {

            // Merge key: emit as plain "<<" so output is "mergeExample: <<" (not !!merge '<<')
            if ("!merge".equals(str)) {
                return new ScalarNode(org.snakeyaml.engine.v2.nodes.Tag.STR, "<<", ScalarStyle.PLAIN);
            }

            boolean multiline = str.contains("\n");

            ScalarStyle style = multiline
                    ? ScalarStyle.LITERAL
                    : ScalarStyle.PLAIN;

            ScalarNode node = new ScalarNode(org.snakeyaml.engine.v2.nodes.Tag.STR, str, style);

            if (!shouldAddComment(enableTraceability, origin)) return node;

            if (multiline) {
                return attachBlock(node, origin);
            } else {
                return attachInline(node, origin);
            }
        }

        // ---------------- INTEGER / LONG ----------------
        if (value instanceof Integer || value instanceof Long) {
            ScalarNode node = new ScalarNode(
                    org.snakeyaml.engine.v2.nodes.Tag.INT,
                    value.toString(),
                    ScalarStyle.PLAIN
            );
            return shouldAddComment(enableTraceability, origin) ? attachInline(node, origin) : node;
        }

        // ---------------- FLOAT / DOUBLE ----------------
        if (value instanceof Float || value instanceof Double) {
            ScalarNode node = new ScalarNode(
                    org.snakeyaml.engine.v2.nodes.Tag.FLOAT,
                    value.toString(),
                    ScalarStyle.PLAIN
            );
            return shouldAddComment(enableTraceability, origin) ? attachInline(node, origin) : node;
        }

        // ---------------- BOOLEAN ----------------
        if (value instanceof Boolean) {
            ScalarNode node = new ScalarNode(
                    org.snakeyaml.engine.v2.nodes.Tag.BOOL,
                    value.toString(),
                    ScalarStyle.PLAIN
            );
            return shouldAddComment(enableTraceability, origin) ? attachInline(node, origin) : node;
        }

        // ---------------- LIST ----------------
        if (value instanceof List<?> list) {
            List<org.snakeyaml.engine.v2.nodes.Node> nodes = new ArrayList<>();
            for (Object elem : list) {
                nodes.add(toNode(elem,enableTraceability));
            }
            return new SequenceNode(org.snakeyaml.engine.v2.nodes.Tag.SEQ, nodes, FlowStyle.BLOCK);
        }

        // ---------------- MAP ----------------
        if (value instanceof Map<?, ?> map) {

            List<NodeTuple> tuples = new ArrayList<>();

            for (Map.Entry<?, ?> entry : map.entrySet()) {

                org.snakeyaml.engine.v2.nodes.Node keyNode = toNode(entry.getKey(),enableTraceability);
                org.snakeyaml.engine.v2.nodes.Node valueNode = toNode(entry.getValue(),enableTraceability);

                // For multiline scalars: put block comment on the key so it appears above "KEY: |"
                moveBlockCommentFromValueToKey(valueNode, keyNode);

                tuples.add(new NodeTuple(keyNode, valueNode));
            }

            MappingNode mapping = new MappingNode(
                    org.snakeyaml.engine.v2.nodes.Tag.MAP,
                    tuples,
                    FlowStyle.BLOCK
            );

            return shouldAddComment(enableTraceability, origin) ? attachBlock(mapping, origin) : mapping;
        }

        // ---------------- FALLBACK ----------------
        String strValue = value.toString();
        if ("!merge".equals(strValue)) {
            return new ScalarNode(org.snakeyaml.engine.v2.nodes.Tag.STR, "<<", ScalarStyle.PLAIN);
        }
        ScalarNode node = new ScalarNode(org.snakeyaml.engine.v2.nodes.Tag.STR, strValue, ScalarStyle.PLAIN);
        return shouldAddComment(enableTraceability, origin) ? attachInline(node, origin) : node;
    }

    private static boolean shouldAddComment(boolean enableTraceability, String origin) {
        return enableTraceability && origin != null && !origin.isBlank();
    }

    // ============================================================
    // Comment Helpers (SnakeYAML Engine: setBlockComments / setInLineComments with CommentLine)
    // ============================================================

    /**
     * When value is a scalar with block comments (multiline origin), move them to the key node
     * so the comment appears on the previous line above "KEY: |" instead of between key and content.
     */
    private void moveBlockCommentFromValueToKey(org.snakeyaml.engine.v2.nodes.Node valueNode, org.snakeyaml.engine.v2.nodes.Node keyNode) {

        if (!(valueNode instanceof ScalarNode scalar)) {
            return;
        }

        List<CommentLine> valueComments = scalar.getBlockComments();
        if (valueComments == null || valueComments.isEmpty()) {
            return;
        }

        // Overwrite key comments completely
        keyNode.setBlockComments(valueComments);

        // Remove from value
        scalar.setBlockComments(null);
    }

    private ScalarNode attachInline(ScalarNode node, String origin) {
        node.setInLineComments(List.of(new CommentLine(Optional.empty(), Optional.empty(), origin, CommentType.IN_LINE)));
        return node;
    }

    private <T extends org.snakeyaml.engine.v2.nodes.Node> T attachBlock(T node, String origin) {
        node.setBlockComments(List.of(new CommentLine(Optional.empty(), Optional.empty(), origin, CommentType.BLOCK)));
        return node;
    }

}
