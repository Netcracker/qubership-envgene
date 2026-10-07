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

package org.qubership.cloud.devops.vals.cli;

import com.fasterxml.jackson.databind.ObjectMapper;
import jakarta.inject.Inject;
import lombok.extern.slf4j.Slf4j;
import org.qubership.cloud.devops.vals.cli.dto.ValsUriRequest;
import org.qubership.cloud.devops.vals.cli.service.ValsReferenceService;
import org.qubership.cloud.devops.vals.core.exceptions.SecretReferenceException;
import picocli.CommandLine;

import java.io.File;
import java.io.IOException;
import java.util.Map;
import java.util.concurrent.Callable;

@Slf4j
@CommandLine.Command(name = "vals-reference-cli", mixinStandardHelpOptions = true, description = "generate vals reference for the given credentials")
public class ValsReferenceCli implements Callable<Integer> {

    @Inject
    ValsReferenceService valsReferenceService;

    @Inject
    ObjectMapper mapper;

    @CommandLine.Option(names = {"-f", "--file"}, description = "input json file. If omitted, JSON is read from stdin")
    File jsonFile;

    @Override
    public Integer call() {
        try {
            ValsUriRequest request = (jsonFile != null)
                    ? mapper.readValue(jsonFile, ValsUriRequest.class)
                    : mapper.readValue(System.in, ValsUriRequest.class);

            Map<String, String> result = valsReferenceService.buildValsReferenceMap(request);

            mapper.writeValue(System.out, result);
            System.out.println();
            return CommandLine.ExitCode.OK;
        } catch (jakarta.validation.ConstraintViolationException e) {
            System.err.println("Validation Error(s):");
            e.getConstraintViolations().forEach(v ->
                    System.err.println("  - " + v.getPropertyPath() + " " + v.getMessage())
            );
            return CommandLine.ExitCode.USAGE;
        } catch (SecretReferenceException e) {
            System.err.println("Unable to construct VALS URI:: " + e.getMessage());
            return CommandLine.ExitCode.SOFTWARE;
        } catch (IOException e) {
            System.err.println("Failed to read request: " + e.getMessage());
            return CommandLine.ExitCode.USAGE;
        } catch (Exception e) {
            System.err.println("Unexpected internal error: " + e.getMessage());
            log.error("Unexpected error while generating VALS reference", e);
            return CommandLine.ExitCode.SOFTWARE;
        }
    }

}
