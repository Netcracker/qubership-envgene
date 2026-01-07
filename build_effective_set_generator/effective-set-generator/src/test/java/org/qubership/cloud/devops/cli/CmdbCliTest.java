package org.qubership.cloud.devops.cli;

import io.quarkus.picocli.runtime.annotations.TopCommand;
import io.quarkus.test.junit.QuarkusTest;
import jakarta.inject.Inject;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.qubership.cloud.devops.cli.utils.FileTestUtils;
import picocli.CommandLine;

import java.nio.file.Path;

import static org.junit.jupiter.api.Assertions.assertEquals;

@QuarkusTest
public class CmdbCliTest {

    @TopCommand
    @Inject
    CmdbCli cli;

    //@Test
    void testGenerateEffectiveSet(@TempDir Path tempDir) throws Exception {
        Path envsPath = FileTestUtils.resource("environments");
        Path sbomsPath = FileTestUtils.resource("sboms");
        Path sdPath = FileTestUtils.resource(
                "environments/cluster-01/pl-01/Inventory/solution-descriptor/sd.yml");
        Path registriesPath = FileTestUtils.resource("configuration/registry.yml");

        Path outputPath = tempDir.resolve("effective-set");

        CommandLine cmd = new CommandLine(cli);

        int exitCode = cmd.execute(
                "--env-id", "cluster-01/pl-01",
                "--envs-path", envsPath.toString(),
                "--sboms-path", sbomsPath.toString(),
                "--sd-path", sdPath.toString(),
                "--registries", registriesPath.toString(),
                "--output", outputPath.toString(),
                "--effective-set-version", "v2.0",
                "--extra_params", "DEPLOYMENT_SESSION_ID=6d5a6ce9-0b55-429d-8877-f7a88dae3d9c",
                "--app_chart_validation", "false"
        );

        assertEquals(0, exitCode);

        Path expected = FileTestUtils.resource("environments/cluster-01/pl-01/effective-set");

        FileTestUtils.compareFolders(expected, outputPath);
    }
}
