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

        assertFalse(AdaptiveYaml.shouldExpand(root));
    }

    @Test
    void testSimpleAlias() {
        Map<String, Object> shared = new HashMap<>();
        shared.put("x", 1);

        Map<String, Object> root = new HashMap<>();
        root.put("a", shared);
        root.put("b", shared);

        assertFalse(AdaptiveYaml.shouldExpand(root));
    }

    @Test
    void testExcessiveAliasing() {
        Map<String, Object> shared = new HashMap<>();
        shared.put("x", 1);

        List<Object> list = new ArrayList<>();

        for (int i = 0; i < 2000; i++) {
            list.add(shared);
        }

        assertTrue(AdaptiveYaml.shouldExpand(list));
    }
}
