package org.qubership.cloud.devops.cli.utils.yaml;

import org.junit.jupiter.api.Test;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;

public class AdaptiveYamlTest {
    @Test
    void testNoAliasing() {
        Map<String, Object> root = new HashMap<>();
        root.put("a", Map.of("x", 1));
        root.put("b", Map.of("y", 2));

        boolean result = AdaptiveYaml.shouldExpand(root);

        assertFalse(result);
    }

    @Test
    void testSimpleAlias() {
        Map<String, Object> shared = new HashMap<>();
        shared.put("x", 1);

        Map<String, Object> root = new HashMap<>();
        root.put("a", shared);
        root.put("b", shared);

        boolean result = AdaptiveYaml.shouldExpand(root);

        assertFalse(result);
    }

    @Test
    void testExcessiveAliasing() {
        Map<String, Object> shared = new HashMap<>();
        shared.put("x", 1);

        List<Object> list = new ArrayList<>();

        for (int i = 0; i < 2000; i++) {
            list.add(shared);
        }

        boolean result = AdaptiveYaml.shouldExpand(list);

        assertTrue(result);
    }
}
