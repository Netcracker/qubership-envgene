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

package org.qubership.cloud.devops.cli.warmup;

import io.quarkus.test.junit.QuarkusTest;
import jakarta.inject.Inject;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.Test;
import org.qubership.cloud.devops.cli.parser.CliParameterParser;
import org.qubership.cloud.devops.cli.pojo.dto.input.InputData;
import org.qubership.cloud.devops.cli.pojo.dto.shared.SharedData;
import org.qubership.cloud.devops.cli.repository.implementation.FileDataRepositoryImpl;

import java.nio.file.Files;
import java.nio.file.Path;
import java.util.HashMap;
import java.util.Optional;

import static org.junit.jupiter.api.Assertions.assertFalse;

@QuarkusTest
class AppCdsWarmupTest {

    @Inject
    SharedData sharedData;

    @Inject
    InputData inputData;

    @Inject
    FileDataRepositoryImpl fileDataRepository;

    @Inject
    CliParameterParser parser;

    @AfterEach
    void reset() {
        sharedData.setEnvId(null);
        sharedData.setEnvsPath(null);
        sharedData.setSbomsPath(Optional.empty());
        sharedData.setDeployPlanPath(Optional.empty());
        sharedData.setRegistryPath(Optional.empty());
        sharedData.setOutputDir(null);
        sharedData.setCredsOutput(null);
        sharedData.setDeploymentSessionId(null);
        sharedData.setGenerateCleanupContext(false);
        inputData.setNamespaceDTOMap(new HashMap<>());
        inputData.setCredentialDTOMap(new HashMap<>());
        inputData.setProfileFullDtoMap(new HashMap<>());
        inputData.setConsumerDTOMap(new HashMap<>());
        inputData.setRegistryDTOMap(new HashMap<>());
        inputData.setSecretStoreDTOMap(new HashMap<>());
        inputData.setClusterMap(new HashMap<>());
        inputData.setTenantDTO(null);
        inputData.setCloudDTO(null);
        inputData.setCompositeStructureDTO(null);
        inputData.setBgDomainEntityDTO(null);
        inputData.setSolutionBomDTO(Optional.empty());
        inputData.setExternalOnly(false);
    }

    @Test
    void warmupRuns() {
        AppCdsWarmup.run(sharedData, fileDataRepository, parser);
        assertFalse(Files.exists(Path.of(sharedData.getOutputDir())));
    }
}
