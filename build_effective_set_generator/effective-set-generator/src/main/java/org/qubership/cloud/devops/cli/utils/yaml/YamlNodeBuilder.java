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

package org.qubership.cloud.devops.cli.utils.yaml;

import jakarta.enterprise.context.ApplicationScoped;
import org.apache.commons.lang3.StringUtils;
import org.qubership.cloud.devops.commons.utils.Parameter;
import org.snakeyaml.engine.v2.comments.CommentLine;
import org.snakeyaml.engine.v2.comments.CommentType;
import org.snakeyaml.engine.v2.common.Anchor;
import org.snakeyaml.engine.v2.common.FlowStyle;
import org.snakeyaml.engine.v2.common.ScalarStyle;
import org.snakeyaml.engine.v2.nodes.AnchorNode;
import org.snakeyaml.engine.v2.nodes.MappingNode;
import org.snakeyaml.engine.v2.nodes.Node;
import org.snakeyaml.engine.v2.nodes.NodeTuple;
import org.snakeyaml.engine.v2.nodes.ScalarNode;
import org.snakeyaml.engine.v2.nodes.SequenceNode;
import org.snakeyaml.engine.v2.nodes.Tag;

import java.util.ArrayList;
import java.util.Collection;
import java.util.Collections;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.Optional;
import java.util.concurrent.atomic.AtomicInteger;

import static org.qubership.cloud.devops.commons.utils.constant.ParametersConstants.SBOM_ORIGIN;

@ApplicationScoped
public class YamlNodeBuilder {

    public Node build(Object input, boolean enableTraceability, boolean deployDescriptorYaml,
                      Map<Object, Integer> refCount, Map<Object, Node> builtNodes, AtomicInteger nextAnchorId) {

        String origin = null;
        Object value = input;

        if (input instanceof Parameter p) {
            origin = p.getOrigin();
            value = p.getValue();
        }

        boolean addComment = shouldAddComment(enableTraceability, origin, deployDescriptorYaml);

        if (value == null) {
            return scalarNode("null", Tag.NULL, origin, addComment);
        }

        if (value instanceof String str) {
            return handleString(str, origin, addComment);
        }

        if (value instanceof Number num) {
            return handleNumber(num, origin, addComment);
        }

        if (value instanceof Boolean bool) {
            return scalarNode(bool.toString(), Tag.BOOL, origin, addComment);
        }

        if (value instanceof List<?> list) {
            return handleList(list, origin, addComment, enableTraceability, deployDescriptorYaml, refCount, builtNodes, nextAnchorId);
        }

        if (value instanceof Map<?, ?> map) {
            return handleMap(map, origin, addComment, enableTraceability, deployDescriptorYaml, refCount, builtNodes, nextAnchorId);
        }

        return scalarNode(value.toString(), Tag.STR, origin, addComment);
    }

    private Node handleString(String str, String origin, boolean addComment) {
        if ("!merge".equals(str)) {
            return new ScalarNode(Tag.STR, "<<", ScalarStyle.PLAIN);
        }
        boolean multiline = str.contains("\n");
        boolean looksLikeBoolean = "True".equals(str) || "False".equals(str);
        ScalarStyle scalarStyle;
        CommentType commentType;

        if (multiline) {
            scalarStyle = ScalarStyle.LITERAL;
            commentType = CommentType.BLOCK;
        } else if (looksLikeBoolean) {
            scalarStyle = ScalarStyle.SINGLE_QUOTED;
            commentType = CommentType.IN_LINE;
        } else {
            scalarStyle = ScalarStyle.PLAIN;
            commentType = CommentType.IN_LINE;
        }
        return attachComment(new ScalarNode(Tag.STR, str, scalarStyle), origin, addComment, commentType);
    }

    private Node handleNumber(Number num, String origin, boolean addComment) {
        Tag tag = (num instanceof Float || num instanceof Double) ? Tag.FLOAT : Tag.INT;
        return scalarNode(num.toString(), tag, origin, addComment);
    }

    private Node handleList(List<?> list, String origin, boolean addComment, boolean enableTraceability,
                            boolean deployDescriptorYaml, Map<Object, Integer> refCount, Map<Object, Node> builtNodes,
                            AtomicInteger nextAnchorId) {

        if (list.isEmpty()) {
            return createEmptyListNode(origin, addComment);
        }

        return buildSequenceNode(list, origin, addComment, enableTraceability, deployDescriptorYaml, refCount, builtNodes, nextAnchorId);
    }

    private Node handleMap(Map<?, ?> map, String origin, boolean addComment, boolean enableTraceability,
                           boolean deployDescriptorYaml, Map<Object, Integer> refCount, Map<Object, Node> builtNodes,
                           AtomicInteger nextAnchorId) {

        if (map.isEmpty()) {
            return createEmptyMapNode(origin, addComment);
        }

        return buildMappingNode(map, origin, addComment, enableTraceability, deployDescriptorYaml, refCount, builtNodes, nextAnchorId);
    }

    private Node scalarNode(String value, Tag tag, String origin, boolean addComment) {
        return attachComment(new ScalarNode(tag, value, ScalarStyle.PLAIN), origin, addComment, CommentType.IN_LINE);
    }

    private Node buildSequenceNode(List<?> list, String origin, boolean addComment, boolean enableTraceability,
                                   boolean deployDescriptorYaml, Map<Object, Integer> refCount, Map<Object, Node> builtNodes,
                                   AtomicInteger nextAnchorId) {

        boolean anchorable = shouldAnchor(list, refCount);
        if (anchorable && builtNodes.containsKey(list)) {
            return new AnchorNode(builtNodes.get(list));
        }

        List<Node> children = new ArrayList<>();
        SequenceNode seqNode = new SequenceNode(Tag.SEQ, children, FlowStyle.BLOCK);

        if (anchorable) {
            builtNodes.put(list, seqNode);
            seqNode.setAnchor(Optional.of(new Anchor(nextAnchorId(nextAnchorId))));
        }

        for (Object elem : list) {
            children.add(this.build(elem, enableTraceability, deployDescriptorYaml, refCount, builtNodes, nextAnchorId));
        }

        return attachComment(seqNode, origin, addComment, CommentType.BLOCK);
    }

    private Node buildMappingNode(Map<?, ?> map, String origin, boolean addComment, boolean enableTraceability,
                                  boolean deployDescriptorYaml, Map<Object, Integer> refCount, Map<Object, Node> builtNodes,
                                  AtomicInteger nextAnchorId) {

        boolean anchorable = shouldAnchor(map, refCount);
        Node existing = anchorable ? builtNodes.get(map) : null;
        if (existing != null) {
            return new AnchorNode(existing);
        }

        List<NodeTuple> tuples = new ArrayList<>();
        MappingNode mapping = new MappingNode(Tag.MAP, tuples, FlowStyle.BLOCK);

        if (anchorable) {
            builtNodes.put(map, mapping);
            mapping.setAnchor(Optional.of(new Anchor(nextAnchorId(nextAnchorId))));
        }

        for (Map.Entry<?, ?> entry : map.entrySet()) {
            Node keyNode = this.build(entry.getKey(), enableTraceability, deployDescriptorYaml, refCount, builtNodes, nextAnchorId);
            Node valueNode = this.build(entry.getValue(), enableTraceability, deployDescriptorYaml, refCount, builtNodes, nextAnchorId);
            moveBlockCommentFromValueToKey(valueNode, keyNode);
            tuples.add(new NodeTuple(keyNode, valueNode));
        }

        return attachComment(mapping, origin, addComment, CommentType.BLOCK);
    }

    private boolean shouldAnchor(Object obj, Map<Object, Integer> refCount) {
        if ((obj instanceof Collection<?> c && c.isEmpty()) || (obj instanceof Map<?, ?> m && m.isEmpty())) {
            return false;
        }
        return refCount.getOrDefault(obj, 0) > 1;
    }

    private String nextAnchorId(AtomicInteger counter) {
        return String.format("id%03d", counter.getAndIncrement());
    }

    private static boolean shouldAddComment(boolean enableTraceability, String origin, boolean deployDescriptorYaml) {
        if (!enableTraceability || StringUtils.isBlank(origin)) {
            return false;
        }
        return !deployDescriptorYaml || !origin.toLowerCase(Locale.ROOT).contains(SBOM_ORIGIN);
    }

    private void moveBlockCommentFromValueToKey(Node valueNode, Node keyNode) {
        List<CommentLine> valueComments = valueNode.getBlockComments();
        if (valueComments == null || valueComments.isEmpty()) {
            return;
        }
        keyNode.setBlockComments(valueComments);
        valueNode.setBlockComments(null);
    }

    private Node createEmptyMapNode(String origin, boolean addComment) {
        MappingNode node = new MappingNode(Tag.MAP, Collections.emptyList(), FlowStyle.FLOW);
        return attachComment(node, origin, addComment, CommentType.IN_LINE);
    }

    private Node createEmptyListNode(String origin, boolean addComment) {
        SequenceNode node = new SequenceNode(Tag.SEQ, Collections.emptyList(), FlowStyle.FLOW);
        return attachComment(node, origin, addComment, CommentType.IN_LINE);
    }

    private <T extends Node> T attachComment(T node, String origin, boolean addComment, CommentType commentType) {
        if (!addComment) {
            return node;
        }
        CommentLine comment = new CommentLine(Optional.empty(), Optional.empty(), origin, commentType);
        List<CommentLine> comments = List.of(comment);
        if (commentType == CommentType.BLOCK) {
            node.setBlockComments(comments);
        } else {
            node.setInLineComments(comments);
        }
        return node;
    }
}
