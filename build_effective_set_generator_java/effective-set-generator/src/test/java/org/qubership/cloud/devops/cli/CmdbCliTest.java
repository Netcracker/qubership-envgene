package org.qubership.cloud.devops.cli;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.dataformat.yaml.YAMLFactory;
import io.quarkus.picocli.runtime.annotations.TopCommand;
import io.quarkus.test.junit.QuarkusTest;
import jakarta.inject.Inject;
import org.junit.jupiter.api.Test;
import picocli.CommandLine;

import java.io.IOException;
import java.io.InputStream;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.HashSet;
import java.util.Set;

import static org.junit.jupiter.api.Assertions.assertArrayEquals;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;

@QuarkusTest
public class CmdbCliTest {

    private final ObjectMapper yamlMapper = new ObjectMapper(new YAMLFactory());

    @TopCommand
    @Inject
    CmdbCli cli;

    @Test
    void testGenerateEffectiveSet() throws Exception {
        ClassLoader classLoader = getClass().getClassLoader();

        Path envsPath = Paths.get(classLoader.getResource("environments").toURI());
        Path sbomsPath = Paths.get(classLoader.getResource("sboms").toURI());
        Path solutionSbomPath = Paths.get(classLoader.getResource(
                "environments/cluster-01/pl-01/Inventory/solution-descriptor/solution.sbom.json").toURI());
        Path registriesPath = Paths.get(classLoader.getResource("configuration/registry.yml").toURI());
        Path outputPath = Paths.get("target/test-output/cluster-01/pl-01/effective-set");
        Files.createDirectories(outputPath);

        CommandLine cmd = new CommandLine(cli);

        int exitCode = cmd.execute(
                "--env-id", "cluster-01/pl-01",
                "--envs-path", envsPath.toString(),
                "--sboms-path", sbomsPath.toString(),
                "--solution-sbom-path", solutionSbomPath.toString(),
                "--registries", registriesPath.toString(),
                "--output", outputPath.toString(),
                "--effective-set-version", "v2.0",
                "--extra_params", "DEPLOYMENT_SESSION_ID=6d5a6ce9-0b55-429d-8877-f7a88dae3d9c",
                "--app_chart_validation", "false"
        );

        assertEquals(0, exitCode);

        // Compare folders recursively
        Path generated = outputPath;
        Path expected = Paths.get(classLoader.getResource(
                "environments/cluster-01/pl-01/effective-set").toURI());

        compareFolders(expected, generated);
    }

    private void compareFolders(Path expected, Path generated) throws IOException {
        Set<Path> expectedFiles = new HashSet<>();
        Set<Path> generatedFiles = new HashSet<>();

        // Collect expected files
        try (var stream = Files.walk(expected)) {
            stream.forEach(p -> expectedFiles.add(expected.relativize(p)));
        }

        // Collect generated files
        try (var stream = Files.walk(generated)) {
            stream.forEach(p -> generatedFiles.add(generated.relativize(p)));
        }

        // Check for missing files
        for (Path rel : expectedFiles) {
            Path expectedPath = expected.resolve(rel);
            Path generatedPath = generated.resolve(rel);
            assertTrue(Files.exists(generatedPath), "Missing file/folder: " + generatedPath);

            if (Files.isRegularFile(expectedPath)) {
                if (expectedPath.toString().endsWith(".yaml") || expectedPath.toString().endsWith(".yml")) {
                    try (InputStream inExp = Files.newInputStream(expectedPath);
                         InputStream inGen = Files.newInputStream(generatedPath)) {
                        assertEquals(
                                yamlMapper.readTree(inExp),
                                yamlMapper.readTree(inGen),
                                "YAML content mismatch: " + generatedPath
                        );
                    }
                } else {
                    assertArrayEquals(
                            Files.readAllBytes(expectedPath),
                            Files.readAllBytes(generatedPath),
                            "File content mismatch: " + generatedPath
                    );
                }
            }
        }

        // Check for unexpected extra files
        for (Path rel : generatedFiles) {
            assertTrue(expectedFiles.contains(rel), "Unexpected file/folder: " + generated.resolve(rel));
        }
    }
}
