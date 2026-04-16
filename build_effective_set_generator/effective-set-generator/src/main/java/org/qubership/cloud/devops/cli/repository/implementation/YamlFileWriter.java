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

import jakarta.enterprise.context.ApplicationScoped;
import jakarta.inject.Inject;
import lombok.extern.slf4j.Slf4j;
import org.qubership.cloud.devops.cli.pojo.dto.shared.SharedData;
import org.qubership.cloud.devops.cli.utils.FileSystemUtils;
import org.qubership.cloud.devops.commons.utils.Parameter;
import org.snakeyaml.engine.v2.api.*;
import org.snakeyaml.engine.v2.comments.*;
import org.snakeyaml.engine.v2.common.*;
import org.snakeyaml.engine.v2.nodes.*;

import java.io.*;
import java.util.*;
import java.util.concurrent.atomic.AtomicInteger;

@ApplicationScoped
@Slf4j
public class YamlFileWriter {

    private static final Set<String> EXCLUDED_FILES = Set.of("mapping.yaml");
    private static final String DEPLOY_DESCRIPTOR_FILE_NAME = "deploy-descriptor.yaml";

    private static final String HEADER =
            "#Source of parameters not marked inline: `#sbom`\n";

    private final FileSystemUtils fileSystemUtils;
    private final SharedData sharedData;

    @Inject
    public YamlFileWriter(FileSystemUtils fileSystemUtils, SharedData sharedData) {
        this.fileSystemUtils = fileSystemUtils;
        this.sharedData = sharedData;
    }

    public void write(Map<String, Object> params, String... path) throws IOException {

        File file = fileSystemUtils.getFileFromGivenPath(path);

        boolean enableTraceability =
                sharedData != null
                        && sharedData.isEnableTraceability()
                        && !EXCLUDED_FILES.contains(file.getName());

        boolean isDeployDescriptor =
                DEPLOY_DESCRIPTOR_FILE_NAME.equals(file.getName());

        try (BufferedWriter writer = new BufferedWriter(new FileWriter(file))) {

            if (params == null || params.isEmpty()) {
                return;
            }

            if (isDeployDescriptor && enableTraceability) {
                writer.write(HEADER);
            }

            writer.write(dump(params, enableTraceability, isDeployDescriptor));
        }
    }

    public String dump(Map<String, Object> data,
                       boolean enableTraceability,
                       boolean deployDescriptorYaml) {

        Map<Object, Integer> refCount = new HashMap<>();
        countReferences(data, refCount);

        Map<Object, Node> builtNodes = new HashMap<>();
        AtomicInteger nextAnchorId = new AtomicInteger(1);

        Node root = toNode(
                data,
                enableTraceability,
                deployDescriptorYaml,
                refCount,
                builtNodes,
                nextAnchorId
        );

        DumpSettings settings = DumpSettings.builder()
                .setDumpComments(true)
                .setDefaultFlowStyle(FlowStyle.BLOCK)
                .build();

        Dump dump = new Dump(settings);
        StringStreamWriter writer = new StringStreamWriter();
        dump.dumpNode(root, writer);

        return writer.toString();
    }


    private static final class StringStreamWriter extends StringWriter implements StreamDataWriter {}

    // ================= FIRST PASS: count references =================

    private void countReferences(Object obj, Map<Object, Integer> refCount) {
        if (obj == null) return;

        // Unwrap Parameter once
        Object value = (obj instanceof Parameter p) ? p.getValue() : obj;

        if (value instanceof Map<?, ?> map) {
            if (incrementAndCheckVisited(map, refCount)) {
                return;
            }
            for (Object v : map.values()) {
                countReferences(v, refCount);
            }
        } else if (value instanceof List<?> list) {
            if (incrementAndCheckVisited(list, refCount)) {
                return;
            }
            for (Object item : list) {
                countReferences(item, refCount);
            }
        }
    }

    boolean incrementAndCheckVisited(Object obj, Map<Object, Integer> refCount) {
        int count = refCount.getOrDefault(obj, 0);
        refCount.put(obj, count + 1);
        return count > 0;
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
            return scalarNode("null", Tag.NULL, origin, addComment, false);
        }

        if (value instanceof String str) {
            return handleString(str, origin, addComment);
        }

        if (value instanceof Number num) {
            return handleNumber(num, origin, addComment);
        }

        if (value instanceof Boolean bool) {
            return scalarNode(bool.toString(), Tag.BOOL, origin, addComment, false);
        }

        if (value instanceof List<?> list) {
            return handleList(list, origin, addComment,
                    enableTraceability, deployDescriptorYaml, refCount, builtNodes, nextAnchorId);
        }

        if (value instanceof Map<?, ?> map) {
            return handleMap(map, origin, addComment,
                    enableTraceability, deployDescriptorYaml, refCount, builtNodes, nextAnchorId);
        }

        return scalarNode(value.toString(), Tag.STR, origin, addComment, false);
    }

    private Node handleString(String str, String origin, boolean addComment) {
        if ("!merge".equals(str)) {
            return new ScalarNode(Tag.STR, "<<", ScalarStyle.PLAIN);
        }
        boolean multiline = str.contains("\n");
        return attachComment(
                new ScalarNode(Tag.STR, str,
                        multiline ? ScalarStyle.LITERAL : ScalarStyle.PLAIN),
                origin,
                addComment,
                multiline
        );
    }

    private Node handleNumber(Number num, String origin, boolean addComment) {
        Tag tag = (num instanceof Float || num instanceof Double)
                ? Tag.FLOAT
                : Tag.INT;

        return scalarNode(num.toString(), tag, origin, addComment, false);
    }

    private Node handleList(List<?> list, String origin, boolean addComment, boolean enableTraceability, boolean deployDescriptorYaml,
                            Map<Object, Integer> refCount, Map<Object, Node> builtNodes, AtomicInteger nextAnchorId) {

        if (list.isEmpty()) {
            return createEmptyListNode(origin, addComment);
        }

        return buildSequenceNode(list, origin, addComment, enableTraceability, deployDescriptorYaml, refCount, builtNodes, nextAnchorId
        );
    }

    private Node handleMap(Map<?, ?> map, String origin, boolean addComment, boolean enableTraceability,
                           boolean deployDescriptorYaml, Map<Object, Integer> refCount, Map<Object, Node> builtNodes, AtomicInteger nextAnchorId) {

        if (map.isEmpty()) {
            return createEmptyMapNode(origin, addComment);
        }

        return buildMappingNode(map, origin, addComment, enableTraceability, deployDescriptorYaml, refCount, builtNodes, nextAnchorId);
    }

    private Node scalarNode(String value, Tag tag, String origin, boolean addComment, boolean multiline) {

        return attachComment(
                new ScalarNode(tag, value, ScalarStyle.PLAIN), origin, addComment, multiline
        );
    }

    private Node buildSequenceNode(List<?> list,
                                   String origin, boolean addComment, boolean enableTraceability, boolean deployDescriptorYaml, Map<Object, Integer> refCount,
                                   Map<Object, Node> builtNodes, AtomicInteger nextAnchorId) {

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

        return attachComment(seqNode, origin, addComment, true);
    }

    private Node buildMappingNode(Map<?, ?> map, String origin, boolean addComment, boolean enableTraceability,
                                  boolean deployDescriptorYaml, Map<Object, Integer> refCount, Map<Object, Node> builtNodes, AtomicInteger nextAnchorId) {

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

        return attachComment(mapping, origin, addComment, true);
    }

    private boolean shouldAnchor(Object obj, Map<Object, Integer> refCount) {
        if (obj instanceof Collection<?> c && c.isEmpty()) return false;
        if (obj instanceof Map<?, ?> m && m.isEmpty()) return false;
        return refCount.getOrDefault(obj, 0) > 1;
    }

    private String nextAnchorId(AtomicInteger counter) {
        return String.format("id%03d", counter.getAndIncrement());
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

        List<CommentLine> valueComments = valueNode.getBlockComments();
        if (valueComments == null || valueComments.isEmpty()) {
            return;
        }
        keyNode.setBlockComments(valueComments);
        valueNode.setBlockComments(null);
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

    private Node createEmptyMapNode(String origin, boolean addComment) {
        MappingNode node = new MappingNode(
                Tag.MAP,
                Collections.emptyList(),
                FlowStyle.FLOW
        );
        return attachComment(node, origin, addComment, false);
    }

    private Node createEmptyListNode(String origin, boolean addComment) {
        SequenceNode node = new SequenceNode(
                Tag.SEQ,
                Collections.emptyList(),
                FlowStyle.FLOW
        );
        return attachComment(node, origin, addComment, false);
    }

    private <T extends Node> T attachComment(T node, String origin, boolean enabled, boolean blockStyle) {
        if (!enabled) return node;
        origin = extractLastOrigin(origin);
        CommentLine comment = new CommentLine(Optional.empty(), Optional.empty(), origin, blockStyle ? CommentType.BLOCK : CommentType.IN_LINE);
        if (blockStyle) {
            node.setBlockComments(List.of(comment));
        } else {
            node.setInLineComments(List.of(comment));
        }
        return node;
    }
}
