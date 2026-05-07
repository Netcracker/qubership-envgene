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
import jakarta.inject.Inject;
import org.qubership.cloud.devops.commons.utils.Parameter;
import org.snakeyaml.engine.v2.comments.CommentType;
import org.snakeyaml.engine.v2.common.FlowStyle;
import org.snakeyaml.engine.v2.common.ScalarStyle;
import org.snakeyaml.engine.v2.nodes.MappingNode;
import org.snakeyaml.engine.v2.nodes.Node;
import org.snakeyaml.engine.v2.nodes.NodeTuple;
import org.snakeyaml.engine.v2.nodes.ScalarNode;
import org.snakeyaml.engine.v2.nodes.SequenceNode;
import org.snakeyaml.engine.v2.nodes.Tag;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.Map;

@ApplicationScoped
public class YamlNodeBuilder {
    private final YamlNodeCommentHelper commentHelper;
    private final YamlReferenceCounter referenceCounter;

    @Inject
    public YamlNodeBuilder(YamlNodeCommentHelper commentHelper, YamlReferenceCounter referenceCounter) {
        this.commentHelper = commentHelper;
        this.referenceCounter = referenceCounter;
    }

    public Node build(Object input, boolean enableTraceability, boolean deployDescriptorYaml) {
        YamlAnchorRegistry anchorRegistry = new YamlAnchorRegistry(referenceCounter.countReferences(input));
        return build(input, enableTraceability, deployDescriptorYaml, anchorRegistry);
    }

    private Node build(Object input, boolean enableTraceability, boolean deployDescriptorYaml,
                       YamlAnchorRegistry anchorRegistry) {

        String origin = null;
        Object value = input;

        if (input instanceof Parameter p) {
            origin = p.getOrigin();
            value = p.getValue();
        }

        boolean addComment = commentHelper.shouldAddComment(enableTraceability, origin, deployDescriptorYaml);

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
            return handleList(list, origin, addComment, enableTraceability, deployDescriptorYaml, anchorRegistry);
        }

        if (value instanceof Map<?, ?> map) {
            return handleMap(map, origin, addComment, enableTraceability, deployDescriptorYaml, anchorRegistry);
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
        return commentHelper.attachComment(new ScalarNode(Tag.STR, str, scalarStyle), origin, addComment, commentType);
    }

    private Node handleNumber(Number num, String origin, boolean addComment) {
        Tag tag = (num instanceof Float || num instanceof Double) ? Tag.FLOAT : Tag.INT;
        return scalarNode(num.toString(), tag, origin, addComment);
    }

    private Node handleList(List<?> list, String origin, boolean addComment, boolean enableTraceability,
                            boolean deployDescriptorYaml, YamlAnchorRegistry anchorRegistry) {

        if (list.isEmpty()) {
            return createEmptyListNode(origin, addComment);
        }

        return buildSequenceNode(list, origin, addComment, enableTraceability, deployDescriptorYaml, anchorRegistry);
    }

    private Node handleMap(Map<?, ?> map, String origin, boolean addComment, boolean enableTraceability,
                           boolean deployDescriptorYaml, YamlAnchorRegistry anchorRegistry) {

        if (map.isEmpty()) {
            return createEmptyMapNode(origin, addComment);
        }

        return buildMappingNode(map, origin, addComment, enableTraceability, deployDescriptorYaml, anchorRegistry);
    }

    private Node scalarNode(String value, Tag tag, String origin, boolean addComment) {
        return commentHelper.attachComment(new ScalarNode(tag, value, ScalarStyle.PLAIN), origin, addComment, CommentType.IN_LINE);
    }

    private Node buildSequenceNode(List<?> list, String origin, boolean addComment, boolean enableTraceability,
                                   boolean deployDescriptorYaml, YamlAnchorRegistry anchorRegistry) {
        Node aliasNode = anchorRegistry.getAliasNodeIfExists(list);
        if (aliasNode != null) {
            return aliasNode;
        }

        List<Node> children = new ArrayList<>();
        SequenceNode seqNode = new SequenceNode(Tag.SEQ, children, FlowStyle.BLOCK);

        anchorRegistry.registerAnchorIfNeeded(list, seqNode);

        for (Object elem : list) {
            children.add(this.build(elem, enableTraceability, deployDescriptorYaml, anchorRegistry));
        }

        return commentHelper.attachComment(seqNode, origin, addComment, CommentType.BLOCK);
    }

    private Node buildMappingNode(Map<?, ?> map, String origin, boolean addComment, boolean enableTraceability,
                                  boolean deployDescriptorYaml, YamlAnchorRegistry anchorRegistry) {
        Node aliasNode = anchorRegistry.getAliasNodeIfExists(map);
        if (aliasNode != null) {
            return aliasNode;
        }

        List<NodeTuple> tuples = new ArrayList<>();
        MappingNode mapping = new MappingNode(Tag.MAP, tuples, FlowStyle.BLOCK);

        anchorRegistry.registerAnchorIfNeeded(map, mapping);

        for (Map.Entry<?, ?> entry : map.entrySet()) {
            Node keyNode = this.build(entry.getKey(), enableTraceability, deployDescriptorYaml, anchorRegistry);
            Node valueNode = this.build(entry.getValue(), enableTraceability, deployDescriptorYaml, anchorRegistry);
            commentHelper.moveBlockCommentFromValueToKey(valueNode, keyNode);
            tuples.add(new NodeTuple(keyNode, valueNode));
        }

        return commentHelper.attachComment(mapping, origin, addComment, CommentType.BLOCK);
    }

    private Node createEmptyMapNode(String origin, boolean addComment) {
        MappingNode node = new MappingNode(Tag.MAP, Collections.emptyList(), FlowStyle.FLOW);
        return commentHelper.attachComment(node, origin, addComment, CommentType.IN_LINE);
    }

    private Node createEmptyListNode(String origin, boolean addComment) {
        SequenceNode node = new SequenceNode(Tag.SEQ, Collections.emptyList(), FlowStyle.FLOW);
        return commentHelper.attachComment(node, origin, addComment, CommentType.IN_LINE);
    }
}
