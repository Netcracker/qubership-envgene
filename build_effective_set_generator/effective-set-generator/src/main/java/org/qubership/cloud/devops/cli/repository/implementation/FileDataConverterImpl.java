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
import org.qubership.cloud.devops.cli.utils.deserializer.BomMixin;
import org.qubership.cloud.devops.commons.exceptions.FileParseException;
import org.qubership.cloud.devops.commons.exceptions.JsonParseException;
import org.qubership.cloud.devops.commons.repository.interfaces.FileDataConverter;
import org.qubership.cloud.devops.commons.utils.Parameter;
import org.snakeyaml.engine.v2.api.Dump;
import org.snakeyaml.engine.v2.api.DumpSettings;
import org.snakeyaml.engine.v2.api.StreamDataWriter;
import org.snakeyaml.engine.v2.comments.CommentLine;
import org.snakeyaml.engine.v2.comments.CommentType;
import org.snakeyaml.engine.v2.common.Anchor;
import org.snakeyaml.engine.v2.common.FlowStyle;
import org.snakeyaml.engine.v2.common.ScalarStyle;
import org.snakeyaml.engine.v2.nodes.*;
import org.snakeyaml.engine.v2.nodes.Tag;

import java.io.*;
import java.util.*;
import java.util.concurrent.atomic.AtomicInteger;

import static org.qubership.cloud.devops.commons.utils.ConsoleLogger.logError;

@ApplicationScoped
@Slf4j
public class FileDataConverterImpl implements FileDataConverter {

    public static final String CLEANUPER = "cleanuper";

    private final ObjectMapper objectMapper;
    private final FileSystemUtils fileSystemUtils;
    private final SharedData sharedData;

    private static final Set<String> EXCLUDED_FILES = Set.of("mapping.yaml");

    private static final String DEPLOY_DESCRIPTOR_FILE_NAME = "deploy-descriptor.yaml";

    private static final String DEPLOY_DESCRIPTOR_FILE_HEADER_LINE =
            "#Source of parameters not marked inline: `#sbom`\n";

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
            if (file.getName().startsWith(CLEANUPER) && e instanceof FileNotFoundException) {
                logError("Issue while reading the file " + e.getMessage());
                return null;
            }
            throw new FileParseException(
                    String.format(ExceptionMessage.FILE_READ_ERROR, file.getAbsolutePath(), e.getMessage()));
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

        boolean enableTraceability =
                sharedData != null
                        && sharedData.isEnableTraceability()
                        && !EXCLUDED_FILES.contains(file.getName());

        boolean deployDescriptorYaml = DEPLOY_DESCRIPTOR_FILE_NAME.equals(file.getName());

        try (BufferedWriter writer = new BufferedWriter(new FileWriter(file))) {
            if (params != null && !params.isEmpty()) {
                if (deployDescriptorYaml && enableTraceability) {
                    writer.write(DEPLOY_DESCRIPTOR_FILE_HEADER_LINE);
                }
                writer.write(dump(params, enableTraceability, deployDescriptorYaml));
            }
        }
    }

    @Override
    public <T> Map<String, Object> getObjectMap(T inputObject) {
        ObjectMapper mapper = new ObjectMapper();
        return mapper.convertValue(inputObject, new TypeReference<Map<String, Object>>() {});
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

    public String dump(Map<String, Object> data, boolean enableTraceability, boolean deployDescriptorYaml) {

        // Use structural equality so equal-but-distinct map/list subtrees can share anchors.
        Map<Object, Integer> refCount = new HashMap<>();
        countReferences(data, refCount);

        Map<Object, org.snakeyaml.engine.v2.nodes.Node> builtNodes = new HashMap<>();
        AtomicInteger nextAnchorId = new AtomicInteger(1);

        org.snakeyaml.engine.v2.nodes.Node rootNode =
                toNode(data, enableTraceability, deployDescriptorYaml, refCount, builtNodes, nextAnchorId);

        DumpSettings settings = DumpSettings.builder()
                .setDumpComments(true)
                .setDefaultFlowStyle(FlowStyle.BLOCK)
                .build();

        Dump dump = new Dump(settings);
        StringStreamWriter writer = new StringStreamWriter();
        dump.dumpNode(rootNode, writer);

        return writer.toString();
    }

    private static final class StringStreamWriter extends StringWriter implements StreamDataWriter {}

    // ================= FIRST PASS: count references =================

    private void countReferences(Object obj, Map<Object, Integer> refCount) {

        if (obj == null) return;

        Object value = obj;

        if (obj instanceof Parameter p) {
            value = p.getValue();
        }

        if (value instanceof Map<?, ?> map) {

            int count = refCount.getOrDefault(map, 0);
            refCount.put(map, count + 1);

            // IMPORTANT: stop recursion if already seen
            if (count > 0) return;

            for (Map.Entry<?, ?> e : map.entrySet()) {
                countReferences(e.getValue(), refCount);
            }
        }

        if (value instanceof List<?> list) {

            int count = refCount.getOrDefault(list, 0);
            refCount.put(list, count + 1);

            // IMPORTANT: stop recursion if already seen
            if (count > 0) return;

            for (Object item : list) {
                countReferences(item, refCount);
            }
        }
    }

    // ================= SECOND PASS: build nodes =================

    private org.snakeyaml.engine.v2.nodes.Node toNode(
            Object input,
            boolean enableTraceability,
            boolean deployDescriptorYaml,
            Map<Object, Integer> refCount,
            Map<Object, org.snakeyaml.engine.v2.nodes.Node> builtNodes,
            AtomicInteger nextAnchorId) {

        String origin = null;
        Object value = input;

        if (input instanceof Parameter p) {
            origin = p.getOrigin();
            value = p.getValue();
        }

        boolean addComment = shouldAddComment(enableTraceability, origin, deployDescriptorYaml);

        if (value == null) {
            return attachScalar(new ScalarNode(Tag.NULL, "null", ScalarStyle.PLAIN), origin, addComment, false);
        }

        if (value instanceof String str) {
            if ("!merge".equals(str)) {
                return new ScalarNode(Tag.STR, "<<", ScalarStyle.PLAIN);
            }

            boolean multiline = str.contains("\n");
            ScalarNode node = new ScalarNode(
                    Tag.STR,
                    str,
                    multiline ? ScalarStyle.LITERAL : ScalarStyle.PLAIN
            );

            return attachScalar(node, origin, addComment, multiline);
        }

        if (value instanceof Number num) {
            Tag tag = (num instanceof Float || num instanceof Double) ? Tag.FLOAT : Tag.INT;
            return attachScalar(
                    new ScalarNode(tag, num.toString(), ScalarStyle.PLAIN),
                    origin,
                    addComment,
                    false
            );
        }

        if (value instanceof Boolean bool) {
            return attachScalar(
                    new ScalarNode(Tag.BOOL, bool.toString(), ScalarStyle.PLAIN),
                    origin,
                    addComment,
                    false
            );
        }

        if (value instanceof List<?> list) {
            return buildSequenceNode(
                    list, origin, addComment, enableTraceability, deployDescriptorYaml, refCount, builtNodes, nextAnchorId);
        }

        if (value instanceof Map<?, ?> map) {
            return buildMappingNode(
                    map, origin, addComment, enableTraceability, deployDescriptorYaml, refCount, builtNodes, nextAnchorId);
        }

        return attachScalar(
                new ScalarNode(Tag.STR, value.toString(), ScalarStyle.PLAIN),
                origin,
                addComment,
                false
        );
    }

    private Node buildSequenceNode(
            List<?> list,
            String origin,
            boolean addComment,
            boolean enableTraceability,
            boolean deployDescriptorYaml,
            Map<Object, Integer> refCount,
            Map<Object, Node> builtNodes,
            AtomicInteger nextAnchorId) {

        boolean anchorable = shouldAnchor(list, refCount);
        if (anchorable && builtNodes.containsKey(list)) {
            return new AnchorNode(builtNodes.get(list));
        }

        List<Node> children = new ArrayList<>();
        SequenceNode seqNode = new SequenceNode(Tag.SEQ, children, FlowStyle.BLOCK);

        // Store only anchorable collections for alias reuse; empties stay inline and unanchored.
        if (anchorable) {
            builtNodes.put(list, seqNode);
            seqNode.setAnchor(Optional.of(new Anchor(nextAnchorId(nextAnchorId))));
        }

        for (Object elem : list) {
            children.add(toNode(elem, enableTraceability, deployDescriptorYaml, refCount, builtNodes, nextAnchorId));
        }

        return addComment ? attachBlock(seqNode, origin) : seqNode;
    }

    private Node buildMappingNode(
            Map<?, ?> map,
            String origin,
            boolean addComment,
            boolean enableTraceability,
            boolean deployDescriptorYaml,
            Map<Object, Integer> refCount,
            Map<Object, Node> builtNodes,
            AtomicInteger nextAnchorId) {

        boolean anchorable = shouldAnchor(map, refCount);
        Node existing = anchorable ? builtNodes.get(map) : null;
        if (existing != null) {
            return new AnchorNode(existing);
        }

        List<NodeTuple> tuples = new ArrayList<>();
        MappingNode mapping = new MappingNode(Tag.MAP, tuples, FlowStyle.BLOCK);

        // Store only anchorable maps for alias reuse; empties stay inline and unanchored.
        if (anchorable) {
            builtNodes.put(map, mapping);
            mapping.setAnchor(Optional.of(new Anchor(nextAnchorId(nextAnchorId))));
        }

        for (Map.Entry<?, ?> entry : map.entrySet()) {

            Node keyNode = toNode(entry.getKey(), enableTraceability, deployDescriptorYaml, refCount, builtNodes, nextAnchorId);
            Node valueNode = toNode(entry.getValue(), enableTraceability, deployDescriptorYaml, refCount, builtNodes, nextAnchorId);

            moveBlockCommentFromValueToKey(valueNode, keyNode);

            tuples.add(new NodeTuple(keyNode, valueNode));
        }

        return addComment ? attachBlock(mapping, origin) : mapping;
    }

    private boolean shouldAnchor(Object obj, Map<Object, Integer> refCount) {
        if (obj instanceof Collection<?> c && c.isEmpty()) return false;
        if (obj instanceof Map<?, ?> m && m.isEmpty()) return false;
        return refCount.getOrDefault(obj, 0) > 1;
    }

    private String nextAnchorId(AtomicInteger counter) {
        return String.format("id%03d", counter.getAndIncrement());
    }

    private ScalarNode attachScalar(
            ScalarNode node,
            String origin,
            boolean enabled,
            boolean block) {

        if (!enabled) return node;
        return block ? attachBlock(node, origin) : attachInline(node, origin);
    }

    private static boolean shouldAddComment(
            boolean enableTraceability, String origin, boolean deployDescriptorYaml) {
        if (!enableTraceability || origin == null || origin.isBlank()) {
            return false;
        }
        if (deployDescriptorYaml && origin.toLowerCase(Locale.ROOT).contains("sbom")) {
            return false;
        }
        return true;
    }

    private void moveBlockCommentFromValueToKey(
            org.snakeyaml.engine.v2.nodes.Node valueNode,
            org.snakeyaml.engine.v2.nodes.Node keyNode) {

        if (!(valueNode instanceof ScalarNode scalar)) {
            return;
        }

        List<CommentLine> valueComments = scalar.getBlockComments();

        if (valueComments == null || valueComments.isEmpty()) {
            return;
        }

        keyNode.setBlockComments(valueComments);
        scalar.setBlockComments(null);
    }

    private String extractLastOrigin(String origin) {
        if (origin == null || origin.isEmpty()) {
            return origin;
        }
        String lower = origin.toLowerCase();
        if (lower.contains("rp-")) {
            return lower;
        }
        int colon = origin.indexOf(':');
        if (colon < 0) {
            return lower;
        }
        int slash = origin.lastIndexOf('/', colon - 1);
        return origin.substring(slash + 1, colon).trim().toLowerCase();
    }

    private ScalarNode attachInline(ScalarNode node, String origin) {
        origin = extractLastOrigin(origin);
        node.setInLineComments(
                List.of(new CommentLine(Optional.empty(), Optional.empty(), origin, CommentType.IN_LINE)));
        return node;
    }

    private <T extends org.snakeyaml.engine.v2.nodes.Node> T attachBlock(T node, String origin) {
        origin = extractLastOrigin(origin);
        node.setBlockComments(
                List.of(new CommentLine(Optional.empty(), Optional.empty(), origin, CommentType.BLOCK)));
        return node;
    }
}
