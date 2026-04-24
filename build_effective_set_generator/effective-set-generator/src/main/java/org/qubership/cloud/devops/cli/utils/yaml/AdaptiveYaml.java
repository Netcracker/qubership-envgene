package org.qubership.cloud.devops.cli.utils.yaml;

import java.util.IdentityHashMap;
import java.util.List;
import java.util.Map;
import static org.qubership.cloud.devops.commons.utils.ConsoleLogger.*;

public class AdaptiveYamlPython {
    private static final int ALIAS_RATIO_RANGE_LOW = 400000;
    private static final int ALIAS_RATIO_RANGE_HIGH = 4000000;
    private static final double ALIAS_RATIO_RANGE =
            (double) ALIAS_RATIO_RANGE_HIGH - ALIAS_RATIO_RANGE_LOW;

    static class Statistic {
        int repeats = 0;
        int complexity = 0;
    }

    static class Decoder {
        private final IdentityHashMap<Object, Statistic> unique = new IdentityHashMap<>();
        private int decodeCount = 0;
        private int aliasCount = 0;

        public int unmarshal(Object node) {
            if (!(node instanceof Map || node instanceof List)) {
                decodeCount++;
                return 1;
            }


            if (unique.containsKey(node)) {
                logInfo("inside unique="+System.identityHashCode(node));
                return alias(node);
            }

            decodeCount++;
            Statistic stat = new Statistic();
            stat.complexity = 1;
            unique.put(node, stat);

            int childComplexity = 0;

            if (node instanceof Map<?, ?> map) {
                for (Map.Entry<?, ?> e : map.entrySet()) {                    
                    childComplexity += unmarshal(e.getKey());
                    childComplexity += unmarshal(e.getValue());
                }
            } else if (node instanceof List<?> list) {
                for (Object item : list) {
                    childComplexity += unmarshal(item);
                }
            }

            stat.complexity += childComplexity;

            if (isLimitExceeded(aliasCount, decodeCount, node)) {
                throw new RuntimeException("Excessive aliasing");
            }

            return stat.complexity;
        }

        private int alias(Object node) {
            Statistic stat = unique.get(node);
            stat.repeats++;
            decodeCount += stat.complexity;
            aliasCount += stat.complexity;
            return stat.complexity;
        }

        private boolean isLimitExceeded(int alias, int decode, Object node ) {
            double rt = allowedAliasRatio(decode);
            double ad = ((double) alias / decode);
            logInfo("alias="+alias+" decode="+decode+" allowedAliasRatio="+rt + " alias/decode="+ad + " node="+System.identityHashCode(node));

            return alias > 100 &&
                    decode > 1000 &&
                    ((double) alias / decode) > allowedAliasRatio(decode);
        }

        private double allowedAliasRatio(int count) {
            if (count <= ALIAS_RATIO_RANGE_LOW) return 0.99;
            if (count >= ALIAS_RATIO_RANGE_HIGH) return 0.1;

            return 0.99 - 0.89 * ((double)(count - ALIAS_RATIO_RANGE_LOW) / ALIAS_RATIO_RANGE);
        }
    }

    public static boolean shouldExpand(Object data) {
        Decoder decoder = new Decoder();
        try {
            decoder.unmarshal(data);
        } catch (RuntimeException e) {
            return true;
        }
        return false;
    }

}
