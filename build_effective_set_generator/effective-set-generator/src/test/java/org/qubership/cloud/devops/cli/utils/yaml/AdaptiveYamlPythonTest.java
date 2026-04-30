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
import org.mockito.Mockito;
import org.qubership.cloud.devops.cli.pojo.dto.shared.SharedData;
import org.qubership.cloud.devops.cli.utils.FileSystemUtils;
import org.qubership.cloud.devops.commons.utils.Parameter;

import java.io.File;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;

class AdaptiveYamlPythonTest {

    @Test
    void shouldExpand_emptyMap_returnsFalse() {
        assertFalse(AdaptiveYamlPython.shouldExpand(new LinkedHashMap<>()));
    }

    @Test
    void shouldExpand_smallTreeNoSharing_returnsFalse() {
        Map<String, Object> root = new LinkedHashMap<>();
        root.put("a", Map.of("k", "v"));
        assertFalse(AdaptiveYamlPython.shouldExpand(root));
    }

    @Test
    void shouldExpand_manyAliasesToSameSubtree_returnsTrue() {
        Map<String, Object> shared = new LinkedHashMap<>();
        shared.put("payload", "x");

        // List of repeated refs: few primitives vs many aliases keeps alias/decode above the ratio threshold.
        // A flat map of 2000 string keys dilutes decode_count and no longer trips the limit (Python behaves the same).
        List<Object> manyRefs = new ArrayList<>(2000);
        for (int i = 0; i < 2000; i++) {
            manyRefs.add(shared);
        }
        Map<String, Object> root = new LinkedHashMap<>();
        root.put("refs", manyRefs);
        assertTrue(AdaptiveYamlPython.shouldExpand(root));
    }

    @Test
    void shouldExpand_unwrapsParameterLikeYamlTraversal() {
        Map<String, Object> shared = new LinkedHashMap<>();
        shared.put("payload", "x");

        List<Object> manyRefs = new ArrayList<>(2000);
        for (int i = 0; i < 2000; i++) {
            manyRefs.add(shared);
        }
        Map<String, Object> inner = new LinkedHashMap<>();
        inner.put("refs", manyRefs);
        Map<String, Object> root = new LinkedHashMap<>();
        root.put("wrapped", new Parameter(inner, "origin", false));
        assertTrue(AdaptiveYamlPython.shouldExpand(root));
    }

    @Test
    void isLimitExceeded_respectsThresholds() {
        assertFalse(AdaptiveYamlPython.isLimitExceeded(50, 2000));
        assertFalse(AdaptiveYamlPython.isLimitExceeded(200, 500));
        assertTrue(AdaptiveYamlPython.isLimitExceeded(1999, 2000));
    }

    @Test
    void yamlFileWriter_dump_expandsWhenDecoderExceedsLimit() throws Exception {
        Path tempDir = Files.createTempDirectory("yaml-deref");
        File outputFile = tempDir.resolve("out.yaml").toFile();

        FileSystemUtils fs = Mockito.mock(FileSystemUtils.class);
        Mockito.when(fs.getFileFromGivenPath(Mockito.any())).thenReturn(outputFile);

        SharedData sharedData = Mockito.mock(SharedData.class);
        Mockito.when(sharedData.isEnableTraceability()).thenReturn(false);

        Map<String, Object> shared = new LinkedHashMap<>();
        shared.put("payload", "x");

        List<Object> manyRefs = new ArrayList<>(2000);
        for (int i = 0; i < 2000; i++) {
            manyRefs.add(shared);
        }
        Map<String, Object> root = new LinkedHashMap<>();
        root.put("refs", manyRefs);

        YamlFileWriter yamlFileWriter = new YamlFileWriter(
                fs, sharedData, new YamlNodeBuilder(new YamlNodeCommentHelper(), new YamlReferenceCounter()));
        yamlFileWriter.write(root, "ignored");

        String content = Files.readString(outputFile.toPath());
        assertFalse(content.contains("&id"), "Expected dereferenced dump without YAML anchor definitions");
        assertTrue(content.length() > 10_000, "Expanded structure should produce a large document");
    }
}
