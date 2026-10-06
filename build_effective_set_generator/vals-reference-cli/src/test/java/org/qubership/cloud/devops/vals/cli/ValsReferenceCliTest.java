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
import io.quarkus.picocli.runtime.annotations.TopCommand;
import io.quarkus.test.junit.QuarkusTest;
import jakarta.inject.Inject;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.qubership.cloud.devops.vals.cli.dto.ValsUriRequest;
import picocli.CommandLine;

import java.io.ByteArrayInputStream;
import java.io.InputStream;

import static org.junit.jupiter.api.Assertions.assertEquals;

@QuarkusTest
class ValsReferenceCliTest {

    @Inject
    @TopCommand
    ValsReferenceCli valsReferenceCli;

    @Inject
    ObjectMapper objectMapper;

    private InputStream originalSystemIn;

    @BeforeEach
    void setUp() {
        originalSystemIn = System.in;
    }

    @AfterEach
    void tearDown() {
        System.setIn(originalSystemIn);
    }

    @Test
    void jsonInputTest() throws Exception {
        ValsUriRequest mockRequest = TestDataFactory.createValidRequest().build();
        String inputJson = objectMapper.writeValueAsString(mockRequest);
        System.setIn(new ByteArrayInputStream(inputJson.getBytes()));

        CommandLine cmd = new CommandLine(valsReferenceCli);
        int exitCode = cmd.execute();
        assertEquals(CommandLine.ExitCode.OK, exitCode);
    }


    @Test
    void validationExceptionTest() {
        String inputJson = "{\"username\":\"\",\"password\":\"\"}";
        System.setIn(new ByteArrayInputStream(inputJson.getBytes()));

        CommandLine cmd = new CommandLine(valsReferenceCli);
        int exitCode = cmd.execute();

        assertEquals(CommandLine.ExitCode.USAGE, exitCode);
    }

}
