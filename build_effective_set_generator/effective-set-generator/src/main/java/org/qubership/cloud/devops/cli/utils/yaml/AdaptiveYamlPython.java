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

import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 * Mirrors the Python {@code Decoder} / {@code should_expand} logic (aligned with go-yaml decode counting)
 * to decide whether YAML output should expand (dereference) aliases.
 *
 * @see <a href="https://github.com/go-yaml/yaml/blob/v3/decode.go">go-yaml decode</a>
 */
public final class AdaptiveYamlPython {

    /**
     * ~500kb of dense object declarations, or ~5kb with 10000% alias expansion (Python comment).
     */
    private static final int ALIAS_RATIO_RANGE_LOW = 400_000;
    /**
     * ~5MB of dense object declarations, or ~4.5MB with 10% alias expansion (Python comment).
     */
    private static final int ALIAS_RATIO_RANGE_HIGH = 4_000_000;
    /**
     * Scale {@link #allowedAliasRatio(int)} between low and high decode counts (subtraction, same as historical Java).
     */
    private static final double ALIAS_RATIO_RANGE =
            (double) ALIAS_RATIO_RANGE_HIGH - ALIAS_RATIO_RANGE_LOW;

    private AdaptiveYamlPython() {
    }

    /**
     * @return {@code true} if anchors/aliases should be expanded (alias budget exceeded).
     */
    public static boolean shouldExpand(Object data) {
        Decoder decoder = new Decoder();
        try {
            decoder.unmarshal(data);
        } catch (ExcessiveAliasingException e) {
            return true;
        }
        return false;
    }

    static boolean isLimitExceeded(int alias, int decode) {
        if (decode <= 0) {
            return false;
        }
        return alias > 100
                && decode > 1000
                && ((double) alias / decode) > allowedAliasRatio(decode);
    }

    static double allowedAliasRatio(int count) {
        if (count <= ALIAS_RATIO_RANGE_LOW) {
            return 0.99;
        }
        if (count >= ALIAS_RATIO_RANGE_HIGH) {
            return 0.1;
        }
        return 0.99 - 0.89 * (count - ALIAS_RATIO_RANGE_LOW) / ALIAS_RATIO_RANGE;
    }

    private static final class Statistic {
        int complexity = 1;
    }

    static final class ExcessiveAliasingException extends RuntimeException {
        private static final long serialVersionUID = 1L;
    }

    /**
     * Replicates go-yaml-style decode/alias mass accounting (same structure as the Python {@code Decoder}).
     * Uses {@link HashMap} for seen collections, keyed by {@link Map#equals(Object)} / {@link List#equals(Object)}
     * the same way as {@link YamlFileWriter}'s ref-count map.
     */
    private static final class Decoder {
        private final HashMap<Object, Statistic> unique = new HashMap<>();
        private int decodeCount;
        private int aliasCount;

        int unmarshal(Object node) {
            Object n = unwrapParameter(node);
            if (n == null) {
                decodeCount++;
                return 1;
            }
            if (!(n instanceof Map<?, ?> || n instanceof List<?>)) {
                decodeCount++;
                return 1;
            }

            if (unique.containsKey(n)) {
                return alias(n);
            }

            decodeCount++;
            Statistic stat = new Statistic();
            unique.put(n, stat);

            int childComplexity = 0;
            if (n instanceof Map<?, ?> map) {
                childComplexity += mapping(map);
            } else {
                childComplexity += sequence((List<?>) n);
            }

            stat.complexity += childComplexity;

            if (isLimitExceeded(aliasCount, decodeCount)) {
                throw new ExcessiveAliasingException();
            }
            return stat.complexity;
        }

        private int alias(Object n) {
            Statistic stat = unique.get(n);
            decodeCount += stat.complexity;
            aliasCount += stat.complexity;
            return stat.complexity;
        }

        private static Object unwrapParameter(Object node) {
            if (node instanceof Parameter p) {
                return p.getValue();
            }
            return node;
        }

        private int mapping(Map<?, ?> node) {
            int complexity = 0;
            for (Map.Entry<?, ?> e : node.entrySet()) {
                complexity += unmarshal(e.getKey());
                complexity += unmarshal(e.getValue());
            }
            return complexity;
        }

        private int sequence(List<?> node) {
            int complexity = 0;
            for (Object item : node) {
                complexity += unmarshal(item);
            }
            return complexity;
        }
    }
}
