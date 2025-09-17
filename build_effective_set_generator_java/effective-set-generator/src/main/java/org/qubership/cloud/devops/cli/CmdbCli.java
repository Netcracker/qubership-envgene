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

package org.qubership.cloud.devops.cli;


import org.apache.commons.lang3.exception.ExceptionUtils;
import org.qubership.cloud.devops.cli.parser.CliParameterParser;
import org.qubership.cloud.devops.cli.pojo.dto.shared.SharedData;
import org.qubership.cloud.devops.cli.repository.implementation.FileDataRepositoryImpl;
import jakarta.inject.Inject;
import lombok.extern.slf4j.Slf4j;
import picocli.CommandLine;

import java.time.Duration;
import java.time.Instant;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.concurrent.Callable;

import static org.qubership.cloud.devops.cli.exceptions.constants.ExceptionMessage.EFFECTIVE_SET_FAILED;
import static org.qubership.cloud.devops.commons.utils.ConsoleLogger.*;

@Slf4j
@CommandLine.Command(name = "generate-effective-set", mixinStandardHelpOptions = true, description = "generate effective parameter set")
public class CmdbCli implements Callable<Integer> {

    @CommandLine.ArgGroup(exclusive = false, multiplicity = "1")
    EnvCommandSpace envParams;

    @Inject
    SharedData sharedData;

    @Inject
    FileDataRepositoryImpl fileDataRepository;
    @Inject
    CliParameterParser parser;

    @Override
    public Integer call() {
        initializeParams();
        try {
            Instant start = Instant.now();
            logInfo("Starting effective set generation");
            fileDataRepository.prepareProcessingEnv();
            parser.generateEffectiveSet();
            logSuccess("Successfully generated the effective set");
            Instant end = Instant.now();
            Duration timeElapsed = Duration.between(start, end);
            logInfo("Total Time taken : "+ timeElapsed.toMillis() +" milliseconds");
            return 0;
        } catch (Exception e) {
            logError(String.format(EFFECTIVE_SET_FAILED, ExceptionUtils.getStackTrace(e)));
            log.debug("stack trace="+e);
            return 1;
        }
    }

    private void initializeParams() {
        if (envParams.solsbomPath == null || envParams.solsbomPath.isEmpty()) {
            envParams.solsbomPath = String.format("%s/%s/%s/", envParams.envsPath, envParams.envId, "Inventory/solution-descriptor/solution.sbom.json");
        }
        if (envParams.outputDir == null || envParams.outputDir.isEmpty()) {
            envParams.outputDir = String.format("%s/%s/%s/", envParams.envsPath, envParams.envId, "effective-set");
        }
        setSharedData();
    }

    private void setSharedData() {
        sharedData.setEnvId(envParams.envId);
        sharedData.setEnvsPath(envParams.envsPath);
        sharedData.setSbomsPath(envParams.sbomsPath);
        sharedData.setSolsbomPath(envParams.solsbomPath);
        sharedData.setRegistryPath(envParams.registryPath);
        sharedData.setOutputDir(envParams.outputDir);
        sharedData.setEffectiveSetVersion(envParams.version);
        sharedData.setPcsspPaths(envParams.pcssp != null ? List.of(envParams.pcssp) : new ArrayList<>());
        sharedData.setAppChartValidation(envParams.appChartValidation);
        populateDeploymentSessionId(envParams.extraParams);
    }

    private void populateDeploymentSessionId(String[] extraParams) {
        if(extraParams != null){
            Arrays.stream(extraParams).forEach(key -> {
                if(key.contains("DEPLOYMENT_SESSION_ID")){
                    String[] deployString = key.split("=");
                    sharedData.setDeploymentSessionId(deployString[1]);
                }
            });
        }
    }

    static class EnvCommandSpace {
        @CommandLine.Option(names = {"-e", "--env-id"}, description = "cluster-name/environment-name", required = true)
        String envId;

        @CommandLine.Option(names = {"-ep", "--envs-path"}, description = "Path to environments folder", defaultValue = "./", required = true)
        String envsPath;

        @CommandLine.Option(names = {"-sp", "--sboms-path"}, description = "Path to the folder with Application and Environment Template SBOMs", required = true)
        String sbomsPath;

        @CommandLine.Option(names = {"-ssp", "--solution-sbom-path"}, description = "Path to the Solution SBOM", required = true)
        String solsbomPath;

        @CommandLine.Option(names = {"-r", "--registries"}, description = "Path to the registry configuration", required = true)
        String registryPath;

        @CommandLine.Option(names = {"-o", "--output"}, description = "Output directory", required = true)
        String outputDir;

        @CommandLine.Option(names = {"-esv", "--effective-set-version"}, description = "Effective Set Version", defaultValue = "v2.0")
        String version;

        @CommandLine.Option(names = {"-pcssp", "--pipeline-consumer-specific-schema-path"}, description = "Pipeline Consumer Specific path")
        String[] pcssp;

        @CommandLine.Option(names = {"-ex", "--extra_params"}, description = "Additional params that used to generate effective set")
        String[] extraParams;

        @CommandLine.Option(names = {"-acv", "--app_chart_validation"}, description = "App chart validation parameter on sbom", arity = "1")
        boolean appChartValidation = true;

    }
}
