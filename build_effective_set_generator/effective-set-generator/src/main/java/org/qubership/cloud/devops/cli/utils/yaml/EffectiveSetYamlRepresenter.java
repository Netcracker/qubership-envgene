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

import org.qubership.cloud.devops.commons.utils.Parameter;
import org.yaml.snakeyaml.DumperOptions;
import org.yaml.snakeyaml.comments.CommentType;
import org.yaml.snakeyaml.nodes.MappingNode;
import org.yaml.snakeyaml.nodes.Node;
import org.yaml.snakeyaml.nodes.NodeTuple;
import org.yaml.snakeyaml.nodes.ScalarNode;
import org.yaml.snakeyaml.nodes.SequenceNode;
import org.yaml.snakeyaml.nodes.Tag;
import org.yaml.snakeyaml.representer.Represent;
import org.yaml.snakeyaml.representer.Representer;

import java.util.Map;

public class EffectiveSetYamlRepresenter extends Representer {

    private final YamlNodeCommentHelper commentHelper;

    private final ThreadLocal<Context> context = new ThreadLocal<>();

    public EffectiveSetYamlRepresenter(DumperOptions options, YamlNodeCommentHelper commentHelper) {
        super(options);
        this.commentHelper = commentHelper;

        this.multiRepresenters.put(Parameter.class, (Represent) data -> representParameter((Parameter) data));
        this.representers.put(String.class, (Represent) data -> representPlainString((String) data));
    }


    public Node representEffectiveSet(Map<String, Object> root, boolean enableTraceability, boolean deployDescriptorYaml) {
        context.set(new Context(enableTraceability, deployDescriptorYaml));
        try {
            return represent(root);
        } finally {
            context.remove();
        }
    }


    @Override
    protected Node representMapping(Tag tag, Map<?, ?> mapping, DumperOptions.FlowStyle flowStyle) {
        MappingNode node = (MappingNode) super.representMapping(tag, mapping, flowStyle);
        for (NodeTuple tuple : node.getValue()) {
            commentHelper.moveBlockCommentFromValueToKey(tuple.getValueNode(), tuple.getKeyNode());
        }
        return node;
    }

    private Context ctx() {
        Context c = context.get();
        if (c == null) {
            throw new IllegalStateException("EffectiveSetYamlRepresenter context not set");
        }
        return c;
    }

    private Node representParameter(Parameter parameter) {
        String origin = parameter.getOrigin();
        Object value = parameter.getValue();
        boolean addComment =
                commentHelper.shouldAddComment(ctx().enableTraceability, origin, ctx().deployDescriptorYaml);

        Node node = representData(value);

        CommentType commentType = commentTypeForWrappedNode(node);
        return commentHelper.attachComment(node, origin, addComment, commentType);
    }

    private static CommentType commentTypeForWrappedNode(Node node) {

        // Empty map -> inline comment
        if (node instanceof MappingNode mn && mn.getValue().isEmpty()) {
            return CommentType.IN_LINE;
        }

        // Empty list -> inline comment
        if (node instanceof SequenceNode sn && sn.getValue().isEmpty()) {
            return CommentType.IN_LINE;
        }

        // Non-empty collections -> block comment
        if (node instanceof MappingNode || node instanceof SequenceNode) {
            return CommentType.BLOCK;
        }

        // Multiline scalar -> block comment
        if (node instanceof ScalarNode scalarNode
                && scalarNode.getScalarStyle() == DumperOptions.ScalarStyle.LITERAL) {
            return CommentType.BLOCK;
        }

        // Everything else -> inline comment
        return CommentType.IN_LINE;
    }

    private Node representPlainString(String str) {
        if ("!merge".equals(str)) {
            ScalarNode mergeScalar =
                    new ScalarNode(Tag.STR, "<<", null, null, DumperOptions.ScalarStyle.PLAIN);
            mergeScalar.setTag(Tag.MERGE);
            return mergeScalar;
        }
        boolean multiline = str.contains("\n");
        boolean looksLikeBoolean = "True".equals(str) || "False".equals(str);
        DumperOptions.ScalarStyle style;
        if (multiline) {
            style = DumperOptions.ScalarStyle.LITERAL;
        } else if (looksLikeBoolean) {
            style = DumperOptions.ScalarStyle.SINGLE_QUOTED;
        } else {
            style = DumperOptions.ScalarStyle.PLAIN;
        }
        return new ScalarNode(Tag.STR, str, null, null, style);
    }

    private record Context(boolean enableTraceability, boolean deployDescriptorYaml) {
    }
}
