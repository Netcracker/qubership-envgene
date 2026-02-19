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

import org.qubership.cloud.devops.commons.utils.Parameter;
import org.snakeyaml.engine.v2.api.Dump;
import org.snakeyaml.engine.v2.api.DumpSettings;
import org.snakeyaml.engine.v2.api.StreamDataWriter;
import org.snakeyaml.engine.v2.comments.CommentLine;
import org.snakeyaml.engine.v2.comments.CommentType;
import org.snakeyaml.engine.v2.common.FlowStyle;
import org.snakeyaml.engine.v2.common.ScalarStyle;
import org.snakeyaml.engine.v2.nodes.*;

import java.io.StringWriter;
import java.util.*;

public class TraceableYamlDumper {

    private final boolean enableTraceability;
    private final String fileName;

    public TraceableYamlDumper(boolean enableTraceability, String fileName) {
        this.enableTraceability = enableTraceability;
        this.fileName = fileName;
    }

    public String dump(Map<String, Object> data) {
        Node rootNode = toNode(data);
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

    private Node toNode(Object input) {

        String origin = null;
        Object value = input;

        if (input instanceof Parameter commonsParam) {
            origin = commonsParam.getOrigin();
            value = commonsParam.getValue();
        }

        boolean shouldAddComment =
                enableTraceability
                        && !"mapping.yaml".equalsIgnoreCase(fileName)
                        && origin != null
                        && !origin.isBlank();

        // ---------------- NULL ----------------
        if (value == null) {
            ScalarNode node = new ScalarNode(Tag.NULL, "null", ScalarStyle.PLAIN);
            return shouldAddComment ? attachInline(node, origin) : node;
        }

        // ---------------- STRING ----------------
        if (value instanceof String str) {

            // Merge key: emit as plain "<<" so output is "mergeExample: <<" (not !!merge '<<')
            if ("!merge".equals(str)) {
                return new ScalarNode(Tag.STR, "<<", ScalarStyle.PLAIN);
            }

            boolean multiline = str.contains("\n");

            ScalarStyle style = multiline
                    ? ScalarStyle.LITERAL
                    : ScalarStyle.PLAIN;

            ScalarNode node = new ScalarNode(Tag.STR, str, style);

            if (!shouldAddComment) return node;

            if (multiline) {
                return attachBlock(node, origin);
            } else {
                return attachInline(node, origin);
            }
        }

        // ---------------- INTEGER / LONG ----------------
        if (value instanceof Integer || value instanceof Long) {
            ScalarNode node = new ScalarNode(
                    Tag.INT,
                    value.toString(),
                    ScalarStyle.PLAIN
            );
            return shouldAddComment ? attachInline(node, origin) : node;
        }

        // ---------------- FLOAT / DOUBLE ----------------
        if (value instanceof Float || value instanceof Double) {
            ScalarNode node = new ScalarNode(
                    Tag.FLOAT,
                    value.toString(),
                    ScalarStyle.PLAIN
            );
            return shouldAddComment ? attachInline(node, origin) : node;
        }

        // ---------------- BOOLEAN ----------------
        if (value instanceof Boolean) {
            ScalarNode node = new ScalarNode(
                    Tag.BOOL,
                    value.toString(),
                    ScalarStyle.PLAIN
            );
            return shouldAddComment ? attachInline(node, origin) : node;
        }

        // ---------------- LIST ----------------
        if (value instanceof List<?> list) {
            List<Node> nodes = new ArrayList<>();
            for (Object elem : list) {
                nodes.add(toNode(elem));
            }
            return new SequenceNode(Tag.SEQ, nodes, FlowStyle.BLOCK);
        }

        // ---------------- MAP ----------------
        if (value instanceof Map<?, ?> map) {

            List<NodeTuple> tuples = new ArrayList<>();

            for (Map.Entry<?, ?> entry : map.entrySet()) {

                Node keyNode = toNode(entry.getKey());
                Node valueNode = toNode(entry.getValue());

                // For multiline scalars: put block comment on the key so it appears above "KEY: |"
                moveBlockCommentFromValueToKey(valueNode, keyNode);

                tuples.add(new NodeTuple(keyNode, valueNode));
            }

            MappingNode mapping = new MappingNode(
                    Tag.MAP,
                    tuples,
                    FlowStyle.BLOCK
            );

            return shouldAddComment ? attachBlock(mapping, origin) : mapping;
        }

        // ---------------- FALLBACK ----------------
        String strValue = value.toString();
        if ("!merge".equals(strValue)) {
            return new ScalarNode(Tag.STR, "<<", ScalarStyle.PLAIN);
        }
        ScalarNode node = new ScalarNode(Tag.STR, strValue, ScalarStyle.PLAIN);
        return shouldAddComment ? attachInline(node, origin) : node;
    }

    // ============================================================
    // Comment Helpers (SnakeYAML Engine: setBlockComments / setInLineComments with CommentLine)
    // ============================================================

    /**
     * When value is a scalar with block comments (multiline origin), move them to the key node
     * so the comment appears on the previous line above "KEY: |" instead of between key and content.
     */
    private void moveBlockCommentFromValueToKey(Node valueNode, Node keyNode) {

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

    private <T extends Node> T attachBlock(T node, String origin) {
        node.setBlockComments(List.of(new CommentLine(Optional.empty(), Optional.empty(), origin, CommentType.BLOCK)));
        return node;
    }
}
