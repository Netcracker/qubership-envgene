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

import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import com.fasterxml.jackson.dataformat.yaml.YAMLFactory;
import io.quarkus.picocli.runtime.annotations.TopCommand;
import io.quarkus.test.junit.QuarkusTest;
import jakarta.inject.Inject;
import org.apache.commons.io.FileUtils;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.qubership.cloud.devops.cli.pojo.dto.input.InputData;
import org.qubership.cloud.devops.cli.pojo.dto.shared.SharedData;
import org.qubership.cloud.devops.cli.utils.FileTestUtils;
import picocli.CommandLine;

import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Base64;
import java.util.Collections;
import java.util.HashMap;
import java.util.Map;
import java.util.Optional;
import java.util.Set;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNotEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;

@QuarkusTest
public class CmdbCliTest {

    @TopCommand
    @Inject
    CmdbCli cli;

    @Inject
    InputData inputData;

    @Inject
    SharedData sharedData;

    @Test
    void testGenerateEffectiveSetFromDeployPlan(@TempDir Path tempDir) throws Exception {
        Path envsPath = FileTestUtils.resource("environments");
        Path sbomsPath = FileTestUtils.resource("sboms");
        Path deployPlanPath = FileTestUtils.resource(
                "environments/cluster-01/pl-01/Inventory/deploy-plan.yml");
        Path registriesPath = FileTestUtils.resource("configuration/registry.yml");

        Path outputPath = tempDir.resolve("effective-set");

        CommandLine cmd = new CommandLine(cli);

        int exitCode = cmd.execute(
                "--env-id", "cluster-01/pl-01",
                "--envs-path", envsPath.toString(),
                "--sboms-path", sbomsPath.toString(),
                "--deploy-plan-path", deployPlanPath.toString(),
                "--registries", registriesPath.toString(),
                "--output", outputPath.toString(),
                "--effective-set-version", "v2.0",
                "--extra_params", "DEPLOYMENT_SESSION_ID=6d5a6ce9-0b55-429d-8877-f7a88dae3d9c",
                "--app_chart_validation", "false",
                "--custom-params", "@config.json"
        );

        assertEquals(0, exitCode);

        Path expected = FileTestUtils.resource("environments/cluster-01/pl-01/effective-set");

        FileTestUtils.compareFolders(expected, outputPath);
    }

    @Test
    void testGenerateEffectiveSetForNamespaceScopedCustomParams(@TempDir Path tempDir) throws Exception {
        Path envsPath = FileTestUtils.resource("environments");
        Path sbomsPath = FileTestUtils.resource("sboms");
        Path deployPlanPath = FileTestUtils.resource(
                "environments/cluster-01/pl-01/Inventory/deploy-plan.yml");
        Path registriesPath = FileTestUtils.resource("configuration/registry.yml");

        Path outputPath = tempDir.resolve("effective-set");

        CommandLine cmd = new CommandLine(cli);

        int exitCode = cmd.execute(
                "--env-id", "cluster-01/pl-01",
                "--envs-path", envsPath.toString(),
                "--sboms-path", sbomsPath.toString(),
                "--deploy-plan-path", deployPlanPath.toString(),
                "--registries", registriesPath.toString(),
                "--output", outputPath.toString(),
                "--effective-set-version", "v2.0",
                "--extra_params", "DEPLOYMENT_SESSION_ID=6d5a6ce9-0b55-429d-8877-f7a88dae3d9c",
                "--app_chart_validation", "false",
                "--custom-params", "@namespace-custom-param/namespace-custom-param.json"
        );

        assertEquals(0, exitCode);

        Path monitoringCustomParams = outputPath.resolve(
                "deployment/monitoring-origin/MONITORING/values/custom-params.yaml");
        assertTrue(Files.exists(monitoringCustomParams));
        assertEquals(0, Files.size(monitoringCustomParams));

        Path pgCustomParams = outputPath.resolve("deployment/pg/postgres/values/custom-params.yaml");
        assertTrue(Files.exists(pgCustomParams));
        FileTestUtils.compareFiles(
                FileTestUtils.resource("namespace-custom-param/pg-custom-params.yaml"),
                pgCustomParams);

        Path pgRuntimeCredentials = outputPath.resolve("runtime/pg/postgres/credentials.yaml");
        assertTrue(Files.exists(pgRuntimeCredentials));
        FileTestUtils.compareFiles(
                FileTestUtils.resource("namespace-custom-param/pg-runtime-credentials.yaml"),
                pgRuntimeCredentials);

        Path monitoringRuntimeCredentials = outputPath.resolve(
                "runtime/monitoring-origin/MONITORING/credentials.yaml");
        assertTrue(Files.exists(monitoringRuntimeCredentials));
        assertEquals(0, Files.size(monitoringRuntimeCredentials));
    }

    @Test
    void testGenerateEffectiveSetRejectsUnknownNamespaceInCustomParams(@TempDir Path tempDir) throws Exception {
        Path envsPath = FileTestUtils.resource("environments");
        Path sbomsPath = FileTestUtils.resource("sboms");
        Path deployPlanPath = FileTestUtils.resource(
                "environments/cluster-01/pl-01/Inventory/deploy-plan.yml");
        Path registriesPath = FileTestUtils.resource("configuration/registry.yml");

        Path outputPath = tempDir.resolve("effective-set");

        CommandLine cmd = new CommandLine(cli);

        int exitCode = cmd.execute(
                "--env-id", "cluster-01/pl-01",
                "--envs-path", envsPath.toString(),
                "--sboms-path", sbomsPath.toString(),
                "--deploy-plan-path", deployPlanPath.toString(),
                "--registries", registriesPath.toString(),
                "--output", outputPath.toString(),
                "--effective-set-version", "v2.0",
                "--extra_params", "DEPLOYMENT_SESSION_ID=6d5a6ce9-0b55-429d-8877-f7a88dae3d9c",
                "--app_chart_validation", "false",
                "--custom-params", "@namespace-custom-param/namespace-custom-param-invalid.json"
        );

        assertNotEquals(0, exitCode);
    }

    @Test
    void testGenerateEffectiveSetRejectsMixedCustomParamsModes(@TempDir Path tempDir) throws Exception {
        Path envsPath = FileTestUtils.resource("environments");
        Path sbomsPath = FileTestUtils.resource("sboms");
        Path deployPlanPath = FileTestUtils.resource(
                "environments/cluster-01/pl-01/Inventory/deploy-plan.yml");
        Path registriesPath = FileTestUtils.resource("configuration/registry.yml");

        Path outputPath = tempDir.resolve("effective-set");

        CommandLine cmd = new CommandLine(cli);

        int exitCode = cmd.execute(
                "--env-id", "cluster-01/pl-01",
                "--envs-path", envsPath.toString(),
                "--sboms-path", sbomsPath.toString(),
                "--deploy-plan-path", deployPlanPath.toString(),
                "--registries", registriesPath.toString(),
                "--output", outputPath.toString(),
                "--effective-set-version", "v2.0",
                "--extra_params", "DEPLOYMENT_SESSION_ID=6d5a6ce9-0b55-429d-8877-f7a88dae3d9c",
                "--app_chart_validation", "false",
                "--custom-params", "@namespace-custom-param/namespace-custom-param-mixed.json"
        );

        assertNotEquals(0, exitCode);
    }

    @Test
    void testGenerateEffectiveSetForExternalCred(@TempDir Path tempDir) throws Exception {
        Path envsPath = FileTestUtils.resource("environments");
        Path sbomsPath = FileTestUtils.resource("sboms");
        Path deployPlanPath = FileTestUtils.resource(
                "environments/cluster-01/pl-02/Inventory/deploy-plan.yml");
        Path registriesPath = FileTestUtils.resource("configuration/registry.yml");

        Path outputPath = tempDir.resolve("effective-set");

        CommandLine cmd = new CommandLine(cli);

        int exitCode = cmd.execute(
                "--env-id", "cluster-01/pl-02",
                "--envs-path", envsPath.toString(),
                "--sboms-path", sbomsPath.toString(),
                "--deploy-plan-path", deployPlanPath.toString(),
                "--registries", registriesPath.toString(),
                "--output", outputPath.toString(),
                "--effective-set-version", "v2.0",
                "--extra_params", "DEPLOYMENT_SESSION_ID=d3ef5cc0-df5c-42b7-82a8-b1aaaca8532d",
                "--app_chart_validation", "false"
        );

        assertEquals(0, exitCode);

        Path expected = FileTestUtils.resource("environments/cluster-01/pl-02/effective-set");

        FileTestUtils.compareFolders(expected, outputPath);
    }

    @Test
    void testGenerateEffectiveSetSkipsAppsInCleanedNamespace(@TempDir Path tempDir) throws Exception {
        Path envsPath = tempDir.resolve("environments");
        FileUtils.copyDirectory(FileTestUtils.resource("environments").toFile(), envsPath.toFile());
        Path pgNamespace = envsPath.resolve("cluster-01/pl-01/Namespaces/pg/namespace.yml");
        Files.writeString(pgNamespace, Files.readString(pgNamespace).replaceFirst(
                "(?m)^name: ", "cleaned: true\nname: "));

        Path outputPath = tempDir.resolve("effective-set");
        int exitCode = new CommandLine(cli).execute(
                "--env-id", "cluster-01/pl-01",
                "--envs-path", envsPath.toString(),
                "--sboms-path", FileTestUtils.resource("sboms").toString(),
                "--deploy-plan-path", envsPath.resolve("cluster-01/pl-01/Inventory/deploy-plan.yml").toString(),
                "--registries", FileTestUtils.resource("configuration/registry.yml").toString(),
                "--output", outputPath.toString(),
                "--effective-set-version", "v2.0",
                "--extra_params", "DEPLOYMENT_SESSION_ID=6d5a6ce9-0b55-429d-8877-f7a88dae3d9c",
                "--app_chart_validation", "false",
                "--custom-params", "@config.json");

        assertEquals(0, exitCode);
        assertTrue(Files.exists(outputPath.resolve("deployment/pg/.cleaned")));
        Path postgresAppDir = outputPath.resolve("deployment/pg/postgres");
        if (Files.isDirectory(postgresAppDir)) {
            assertTrue(FileUtils.listFiles(postgresAppDir.toFile(), null, true).isEmpty(),
                    "Cleaned namespace must not emit deployment files for postgres");
        }
    }

    @Test
    void testUniqForAppAndUniqForRunNestUnderSameDeployPostfix(@TempDir Path tempDir) throws Exception {
        Path envsPath = FileTestUtils.resource("environments");
        Path sbomsPath = FileTestUtils.resource("sboms");
        Path deployPlanPath = FileTestUtils.resource(
                "environments/cluster-01/pl-02/Inventory/deploy-plan-uniq-mixed.yml");
        Path registriesPath = FileTestUtils.resource("configuration/registry.yml");

        Path outputPath = tempDir.resolve("effective-set");

        int exitCode = executeGenerate(envsPath, sbomsPath, deployPlanPath, registriesPath, outputPath,
                "d3ef5cc0-df5c-42b7-82a8-b1aaaca8532d");

        assertEquals(0, exitCode);

        assertTrue(Files.isDirectory(outputPath.resolve("deployment/ns-test/eso-app/values")));
        assertTrue(Files.isDirectory(outputPath.resolve("runtime/ns-test/eso-app")));

        assertTrue(Files.isDirectory(outputPath.resolve(
                "deployment/ns-test/vals-app/0190c7e2-1a2b-7c3d-8e4f-5a6b7c8d9e0f/values")));
        assertTrue(Files.isDirectory(outputPath.resolve(
                "runtime/ns-test/vals-app/0190c7e2-1a2b-7c3d-8e4f-5a6b7c8d9e0f")));
    }

    @Test
    void testUniqForVersionAndUniqForRunSurviveAcrossRuns(@TempDir Path tempDir) throws Exception {
        Path envsPath = FileTestUtils.resource("environments");
        Path sbomsPath = FileTestUtils.resource("sboms");
        Path registriesPath = FileTestUtils.resource("configuration/registry.yml");
        Path outputPath = tempDir.resolve("effective-set");

        int firstExitCode = executeGenerate(envsPath, sbomsPath,
                FileTestUtils.resource("environments/cluster-01/pl-02/Inventory/deploy-plan-uniq-run1.yml"),
                registriesPath, outputPath, "d3ef5cc0-df5c-42b7-82a8-b1aaaca8532d");
        assertEquals(0, firstExitCode);

        resetInputData(inputData);
        resetSharedData(sharedData);

        int secondExitCode = executeGenerate(envsPath, sbomsPath,
                FileTestUtils.resource("environments/cluster-01/pl-02/Inventory/deploy-plan-uniq-run2.yml"),
                registriesPath, outputPath, "d3ef5cc0-df5c-42b7-82a8-b1aaaca8532d");
        assertEquals(0, secondExitCode);

        assertTrue(Files.isDirectory(outputPath.resolve(
                "deployment/ns-test/eso-app/0.1.0-delivery-20261115.141230-4-RELEASE/values")));
        assertTrue(Files.isDirectory(outputPath.resolve(
                "deployment/ns-test/eso-app/0.2.0-delivery-20261115.141230-4-RELEASE/values")));
        assertTrue(Files.isDirectory(outputPath.resolve(
                "runtime/ns-test/eso-app/0.1.0-delivery-20261115.141230-4-RELEASE")));
        assertTrue(Files.isDirectory(outputPath.resolve(
                "runtime/ns-test/eso-app/0.2.0-delivery-20261115.141230-4-RELEASE")));

        assertTrue(Files.isDirectory(outputPath.resolve(
                "deployment/ns-test/vals-app/0190c7e2-1a2b-7c3d-8e4f-5a6b7c8d9e0f/values")));
        assertTrue(Files.isDirectory(outputPath.resolve(
                "deployment/ns-test/vals-app/0190c7e2-2b3c-8d4e-9f5a-6b7c8d9e0f1a/values")));
    }

    @Test
    void testNamespaceBaselineAndOverrideReachEffectiveSet(@TempDir Path tempDir) throws Exception {
        Path envsPath = prepareProfileEnv(tempDir);
        setObjectProfile(envsPath, NS_FILE, "ns-over", "dev");
        writeProfile(envsPath, "ns-over", "prod");

        assertEquals(Map.of("BASELINE_MEMORY", "prod-mem", "REPLICAS", 5, "OVERRIDE_CPU", "700m"),
                profileParams(generateProfileEs(tempDir, envsPath)));
    }

    @Test
    void testNamespaceObjectBaselineReachesEffectiveSet(@TempDir Path tempDir) throws Exception {
        Path envsPath = prepareProfileEnv(tempDir);
        Path file = envsPath.resolve(NS_FILE);
        Files.writeString(file, Files.readString(file) + "\nprofile:\n  baseline: \"dev\"\n");

        assertEquals(Map.of("BASELINE_MEMORY", "dev-mem", "REPLICAS", 1),
                profileParams(generateProfileEs(tempDir, envsPath)));
    }

    @Test
    void testCloudSideUsedWhenNamespaceHasNoProfileSignal(@TempDir Path tempDir) throws Exception {
        Path envsPath = prepareProfileEnv(tempDir);
        setObjectProfile(envsPath, CLOUD_FILE, "cloud-over", "dev");
        writeProfile(envsPath, "cloud-over", "prod");

        assertEquals(Map.of("BASELINE_MEMORY", "prod-mem", "REPLICAS", 5, "OVERRIDE_CPU", "700m"),
                profileParams(generateProfileEs(tempDir, envsPath)));
    }

    private static final String NS_FILE = "cluster-01/pl-02/Namespaces/ns-test/namespace.yml";
    private static final String CLOUD_FILE = "cluster-01/pl-02/cloud.yml";
    private static final String VALS_APP_SBOM = "vals-app/vals-app-0.1.0-20261215.141230-3-RELEASE.sbom.json";
    private static final Set<String> BASE_SERVICE_KEYS = Set.of("ARTIFACT_DESCRIPTOR_VERSION", "DEPLOYMENT_RESOURCE_NAME",
            "DEPLOYMENT_SESSION_ID", "DEPLOYMENT_VERSION", "DOCKER_TAG", "IMAGE_REPOSITORY", "MANAGED_BY",
            "SERVICE_NAME", "TAG");

    private Path prepareProfileEnv(Path tempDir) throws Exception {
        Path envsPath = tempDir.resolve("environments");
        FileUtils.copyDirectory(FileTestUtils.resource("environments").toFile(), envsPath.toFile());
        FileUtils.copyDirectory(FileTestUtils.resource("configuration").toFile(), tempDir.resolve("configuration").toFile());
        Path sbomsPath = tempDir.resolve("sboms");
        FileUtils.copyDirectory(FileTestUtils.resource("sboms").toFile(), sbomsPath.toFile());
        ObjectMapper json = new ObjectMapper();
        Path sbom = sbomsPath.resolve(VALS_APP_SBOM);
        ObjectNode root = (ObjectNode) json.readTree(sbom.toFile());
        ArrayNode data = json.createArrayNode()
                .add(baselineData(json, "dev", "BASELINE_MEMORY: dev-mem\nREPLICAS: 1\n"))
                .add(baselineData(json, "prod", "BASELINE_MEMORY: prod-mem\nREPLICAS: 2\n"));
        ObjectNode baselineComponent = json.createObjectNode()
                .put("type", "data")
                .put("mime-type", "application/vnd.qubership.resource-profile-baseline")
                .put("bom-ref", "BomRef.profile-baselines")
                .set("data", data);
        ((ArrayNode) root.path("components").get(0).path("components")).add(baselineComponent);
        json.writerWithDefaultPrettyPrinter().writeValue(sbom.toFile(), root);
        return envsPath;
    }

    private static ObjectNode baselineData(ObjectMapper json, String name, String yaml) {
        ObjectNode attachment = json.createObjectNode()
                .put("contentType", "application/yaml")
                .put("encoding", "base64")
                .put("content", Base64.getEncoder().encodeToString(yaml.getBytes(StandardCharsets.UTF_8)));
        ObjectNode contents = json.createObjectNode().set("attachment", attachment);
        return json.createObjectNode()
                .put("type", "configuration")
                .put("name", name + ".yaml")
                .set("contents", contents);
    }

    private static void setObjectProfile(Path envsPath, String objectFile, String name, String baseline) throws Exception {
        Path file = envsPath.resolve(objectFile);
        Files.writeString(file, Files.readString(file)
                + "\nprofile:\n  name: \"" + name + "\"\n  baseline: \"" + baseline + "\"\n");
    }

    private static void writeProfile(Path envsPath, String name, String baseline) throws Exception {
        String profile = "name: \"" + name + "\"\nbaseline: \"" + baseline + "\"\n" + """
                applications:
                  - name: "vals-app"
                    services:
                      - name: "alertmanager"
                        parameters:
                          - name: "REPLICAS"
                            value: 5
                          - name: "OVERRIDE_CPU"
                            value: "700m"
                """;
        Path profiles = envsPath.resolve("cluster-01/pl-02/Profiles");
        Files.createDirectories(profiles);
        Files.writeString(profiles.resolve(name + ".yml"), profile);
    }

    private Path generateProfileEs(Path tempDir, Path envsPath) throws Exception {
        Path outputPath = tempDir.resolve("effective-set");
        int exitCode = executeGenerate(envsPath, tempDir.resolve("sboms"),
                envsPath.resolve("cluster-01/pl-02/Inventory/deploy-plan.yml"),
                FileTestUtils.resource("configuration/registry.yml"), outputPath,
                "d3ef5cc0-df5c-42b7-82a8-b1aaaca8532d");
        assertEquals(0, exitCode);
        return outputPath;
    }

    private static Map<String, Object> profileParams(Path outputPath) throws Exception {
        Path params = outputPath.resolve(
                "deployment/ns-test/vals-app/values/per-service-parameters/alertmanager/deployment-parameters.yaml");
        Map<String, Object> values = new ObjectMapper(new YAMLFactory()).readValue(params.toFile(),
                new TypeReference<Map<String, Object>>() {
                });
        values.keySet().removeAll(BASE_SERVICE_KEYS);
        return values;
    }

    private int executeGenerate(Path envsPath, Path sbomsPath, Path deployPlanPath, Path registriesPath,
                                 Path outputPath, String deploymentSessionId) throws Exception {
        CommandLine cmd = new CommandLine(cli);
        return cmd.execute(
                "--env-id", "cluster-01/pl-02",
                "--envs-path", envsPath.toString(),
                "--sboms-path", sbomsPath.toString(),
                "--deploy-plan-path", deployPlanPath.toString(),
                "--registries", registriesPath.toString(),
                "--output", outputPath.toString(),
                "--effective-set-version", "v2.0",
                "--extra_params", "DEPLOYMENT_SESSION_ID=" + deploymentSessionId,
                "--app_chart_validation", "false"
        );
    }

    @AfterEach
    void tearDown() {
        resetInputData(inputData);
        resetSharedData(sharedData);
    }

    private void resetInputData(InputData inputData) {
        if (inputData != null) {
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
    }

    private void resetSharedData(SharedData sharedData) {
        if (sharedData != null) {
            sharedData.setNamespaceScopedCustomParams(false);
            sharedData.setCustomDeployParamMap(Collections.emptyMap());
            sharedData.setCustomRuntimeParamMap(Collections.emptyMap());
            sharedData.setNamespaceCustomDeployParamMap(Collections.emptyMap());
            sharedData.setNamespaceCustomRuntimeParamMap(Collections.emptyMap());
            sharedData.setCustomParamsNamespaceKeys(Collections.emptySet());
            sharedData.setDeployPlanPath(Optional.empty());
        }
    }
}
