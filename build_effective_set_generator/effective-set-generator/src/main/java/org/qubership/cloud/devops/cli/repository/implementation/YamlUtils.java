package org.qubership.cloud.devops.cli.repository.implementation;

import org.qubership.cloud.devops.cli.utils.FileSystemUtils;
import org.qubership.cloud.devops.commons.utils.Parameter;
import org.snakeyaml.engine.v2.api.Dump;
import org.snakeyaml.engine.v2.api.DumpSettings;
import org.snakeyaml.engine.v2.api.StreamDataWriter;
import org.snakeyaml.engine.v2.api.YamlOutputStreamWriter;
import org.snakeyaml.engine.v2.comments.CommentLine;
import org.snakeyaml.engine.v2.comments.CommentType;
import org.snakeyaml.engine.v2.common.Anchor;
import org.snakeyaml.engine.v2.common.ScalarStyle;
import org.snakeyaml.engine.v2.nodes.*;
import org.snakeyaml.engine.v2.serializer.AnchorGenerator;
import org.snakeyaml.engine.v2.serializer.Serializer;

import java.io.File;
import java.io.FileOutputStream;
import java.io.OutputStream;
import java.nio.charset.StandardCharsets;
import java.util.*;
import java.util.concurrent.atomic.AtomicInteger;

import static org.snakeyaml.engine.v2.common.FlowStyle.AUTO;

public class YamlUtils {

    private final Map<Object, Node> nodeCache = new IdentityHashMap<>();
    AtomicInteger counter = new AtomicInteger(1);

    public void dumpYaml(Object obj, String... path) throws Exception {
        String fullPath = String.join(File.separator, path);

        Node rootNode = convertToNode(obj);

        DumpSettings settings = DumpSettings.builder()
                .setDumpComments(true)
                .setAnchorGenerator(node -> new Anchor(String.format("id%03d", counter.getAndIncrement())))
                .build();

        try (OutputStream output = new FileOutputStream(fullPath);
             YamlOutputStreamWriter writer = new YamlOutputStreamWriter(output, StandardCharsets.UTF_8)) {
            Dump dumper = new Dump(settings);
            dumper.dumpNode(rootNode, writer);
        }
    }


    public Node convertToNode(Object obj) {

        // Scalars/simple immutable types never participate in anchors
        if (ignoreAliases(obj)) {
            return representData(obj);
        }

        // Existing node -> alias/anchor reuse
        Node cached = nodeCache.get(obj);
        if (cached != null) {
            return cached;
        }

        if (obj instanceof Parameter kv) {
            return representParameter(kv);
        }

        return representData(obj);
    }

    private Node representData(Object obj) {

        if (obj instanceof Map<?, ?> mapObj) {
            return convertMap(mapObj);
        }

        if (obj instanceof List<?> listObj) {
            return convertList(listObj);
        }

        return createScalarNode(obj, null);
    }

    private Node representParameter(Parameter kv) {

        Object value = kv.getValue();

        if (value instanceof Map<?, ?> mapVal) {
            return convertMap(mapVal);
        }

        if (value instanceof List<?> listVal) {
            return convertList(listVal);
        }

        if (value instanceof Parameter nested) {
            return convertToNode(nested);
        }

        return createScalarNode(value, kv.getOrigin());
    }

    private Node convertMap(Map<?, ?> mapObj) {

        // CREATE EMPTY NODE FIRST
        MappingNode mappingNode =
                new MappingNode(Tag.MAP, new ArrayList<>(), AUTO);

        // CACHE BEFORE RECURSION
        nodeCache.put(mapObj, mappingNode);

        List<NodeTuple> tuples = mappingNode.getValue();

        for (Map.Entry<?, ?> entry : mapObj.entrySet()) {

            String key = entry.getKey().toString();
            Object valueObj = entry.getValue();

            ScalarNode keyNode =
                    new ScalarNode(Tag.STR, key, ScalarStyle.PLAIN);

            Node valueNode = convertToNode(valueObj);

            if (valueObj instanceof Parameter kv) {

                String comment = kv.getOrigin();
                Object value = kv.getValue();

                if (comment != null && !comment.isEmpty()) {

                    if (isMultiline(value)
                            || value instanceof List
                            || value instanceof Map) {

                        keyNode.setBlockComments(
                                List.of(
                                        new CommentLine(
                                                Optional.empty(),
                                                Optional.empty(),
                                                comment,
                                                CommentType.BLOCK
                                        )
                                )
                        );
                    }
                }
            }

            tuples.add(new NodeTuple(keyNode, valueNode));
        }

        return mappingNode;
    }

    private Node convertList(List<?> listObj) {


        // CREATE EMPTY NODE FIRST
        SequenceNode seqNode =
                new SequenceNode(Tag.SEQ, new ArrayList<>(), AUTO);

        // CACHE BEFORE RECURSION
        nodeCache.put(listObj, seqNode);

        List<Node> items = seqNode.getValue();

        for (Object item : listObj) {

            Node itemNode = convertToNode(item);

            if (item instanceof Parameter kv
                    && isMultiline(kv.getValue())) {

                if (kv.getOrigin() != null
                        && !kv.getOrigin().isEmpty()) {

                    itemNode.setBlockComments(
                            List.of(
                                    new CommentLine(
                                            Optional.empty(),
                                            Optional.empty(),
                                            kv.getOrigin(),
                                            CommentType.BLOCK
                                    )
                            )
                    );
                }
            }

            items.add(itemNode);
        }

        return seqNode;
    }

    private static boolean isMultiline(Object value) {
        return value instanceof String s && s.contains("\n");
    }

    private static Tag detectTag(Object value) {

        if (value == null) return Tag.NULL;
        if (value instanceof Boolean) return Tag.BOOL;

        if (value instanceof Integer
                || value instanceof Long
                || value instanceof Short) {

            return Tag.INT;
        }

        if (value instanceof Float
                || value instanceof Double) {

            return Tag.FLOAT;
        }

        return Tag.STR;
    }

    private static ScalarNode createScalarNode(
            Object value,
            String comment
    ) {

        Tag tag = detectTag(value);

        String strValue =
                value == null ? "null" : value.toString();

        ScalarStyle style =
                isMultiline(value)
                        ? ScalarStyle.LITERAL
                        : ScalarStyle.PLAIN;

        ScalarNode scalar =
                new ScalarNode(tag, strValue, style);

        if (comment != null
                && !comment.isEmpty()
                && !isMultiline(value)) {

            scalar.setInLineComments(
                    List.of(
                            new CommentLine(
                                    Optional.empty(),
                                    Optional.empty(),
                                    comment,
                                    CommentType.IN_LINE
                            )
                    )
            );
        }

        return scalar;
    }

    boolean ignoreAliases(Object data) {

        return data == null
                || data instanceof String
                || data instanceof Number
                || data instanceof Boolean
                || data instanceof Character
                || data instanceof Enum;
    }
}