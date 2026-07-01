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

package org.qubership.cloud.extcreds.valsref.cli;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.SerializationFeature;
import jakarta.inject.Inject;
import picocli.CommandLine;

import java.nio.file.Path;
import java.util.concurrent.Callable;

@CommandLine.Command(
        name = "extcreds-vals-ref",
        mixinStandardHelpOptions = true,
        description = "Build normalized secret names and VALS references for external credentials"
)
public class ExtCredsValsRefCli implements Callable<Integer> {

    @CommandLine.Option(
            names = {"-c", "--credentials"},
            description = "Path to credentials YAML file",
            required = true
    )
    Path credentialsPath;

    @CommandLine.Option(
            names = {"-s", "--secret-stores"},
            description = "Path to secret-stores YAML file",
            required = true
    )
    Path secretStoresPath;

    @CommandLine.Option(
            names = {"-r", "--requests"},
            description = "Optional path to batch requests YAML or JSON file"
    )
    Path requestsPath;

    @CommandLine.Option(
            names = {"-f", "--fields"},
            description = "Comma-separated output fields: normalized, vals, or both",
            defaultValue = "both"
    )
    String fields;

    @Inject
    ValsRefBatchProcessor processor;

    private final ObjectMapper objectMapper = new ObjectMapper()
            .enable(SerializationFeature.INDENT_OUTPUT);

    @Override
    public Integer call() throws Exception {
        ValsRefBatchProcessor.OutputFields outputFields = parseFields(fields);
        CliOutput output = processor.process(credentialsPath, secretStoresPath, requestsPath, outputFields);
        System.out.println(objectMapper.writeValueAsString(output));
        return output.getErrors().isEmpty() ? 0 : 1;
    }

    private ValsRefBatchProcessor.OutputFields parseFields(String value) {
        return switch (value.trim().toLowerCase()) {
            case "normalized" -> ValsRefBatchProcessor.OutputFields.NORMALIZED;
            case "vals" -> ValsRefBatchProcessor.OutputFields.VALS;
            case "both" -> ValsRefBatchProcessor.OutputFields.BOTH;
            default -> throw new CommandLine.ParameterException(
                    new CommandLine(this),
                    "Invalid --fields value: " + value + ". Allowed: normalized, vals, both"
            );
        };
    }
}
