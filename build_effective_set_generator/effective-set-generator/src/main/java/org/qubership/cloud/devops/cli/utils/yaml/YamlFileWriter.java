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
import lombok.extern.slf4j.Slf4j;
import org.qubership.cloud.devops.cli.pojo.dto.shared.SharedData;
import org.qubership.cloud.devops.cli.utils.FileSystemUtils;
import org.snakeyaml.engine.v2.api.Dump;
import org.snakeyaml.engine.v2.api.DumpSettings;
import org.snakeyaml.engine.v2.api.StreamDataWriter;
import org.snakeyaml.engine.v2.common.FlowStyle;
import org.snakeyaml.engine.v2.nodes.Node;

import java.io.BufferedWriter;
import java.io.File;
import java.io.FileWriter;
import java.io.IOException;
import java.io.StringWriter;
import java.util.Map;
import java.util.Set;

@ApplicationScoped
@Slf4j
public class YamlFileWriter {

    private static final Set<String> EXCLUDED_FILES = Set.of("mapping.yaml");
    private static final String DEPLOY_DESCRIPTOR_FILE_NAME = "deploy-descriptor.yaml";
    private static final String SBOM_HEADER = "#Source of parameters not marked inline: `#sbom`\n";

    private final FileSystemUtils fileSystemUtils;
    private final SharedData sharedData;
    private final YamlNodeBuilder yamlNodeBuilder;

    @Inject
    public YamlFileWriter(FileSystemUtils fileSystemUtils, SharedData sharedData, YamlNodeBuilder yamlNodeBuilder) {
        this.fileSystemUtils = fileSystemUtils;
        this.sharedData = sharedData;
        this.yamlNodeBuilder = yamlNodeBuilder;
    }

    public void write(Map<String, Object> params, String... path) throws IOException {
        File file = fileSystemUtils.getFileFromGivenPath(path);

        boolean enableTraceability =
                sharedData != null
                        && sharedData.isEnableTraceability()
                        && !EXCLUDED_FILES.contains(file.getName());
        boolean isDeployDescriptor = DEPLOY_DESCRIPTOR_FILE_NAME.equals(file.getName());

        try (BufferedWriter writer = new BufferedWriter(new FileWriter(file))) {
            if (params == null || params.isEmpty()) {
                return;
            }

            if (isDeployDescriptor && enableTraceability) {
                writer.write(SBOM_HEADER);
            }

            writer.write(dump(params, enableTraceability, isDeployDescriptor));
        }
    }

    public String dump(Map<String, Object> data, boolean enableTraceability, boolean deployDescriptorYaml) {
        Node root = yamlNodeBuilder.build(data, enableTraceability, deployDescriptorYaml);

        DumpSettings settings = DumpSettings.builder()
                .setDumpComments(true)
                .setDefaultFlowStyle(FlowStyle.BLOCK)
                .setDereferenceAliases(AdaptiveYamlPython.shouldExpand(data))
                .build();

        Dump dump = new Dump(settings);
        StringStreamWriter writer = new StringStreamWriter();
        dump.dumpNode(root, writer);
        return writer.toString();
    }

    private static final class StringStreamWriter extends StringWriter implements StreamDataWriter {
    }
}
