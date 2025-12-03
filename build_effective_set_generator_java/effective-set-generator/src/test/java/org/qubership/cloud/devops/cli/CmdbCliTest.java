package org.qubership.cloud.devops.cli;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.dataformat.yaml.YAMLFactory;
import io.quarkus.picocli.runtime.annotations.TopCommand;
import io.quarkus.test.InjectMock;
import io.quarkus.test.junit.QuarkusTest;
import jakarta.inject.Inject;
import org.junit.jupiter.api.Test;
import org.mockito.Mockito;
import org.qubership.cloud.devops.cli.parser.CliParameterParser;
import org.qubership.cloud.devops.cli.pojo.dto.shared.SharedData;
import org.qubership.cloud.devops.cli.repository.implementation.FileDataRepositoryImpl;

import java.io.InputStream;
import java.nio.file.*;
import java.util.Comparator;

import static java.nio.file.StandardCopyOption.REPLACE_EXISTING;
import static org.junit.jupiter.api.Assertions.*;

@QuarkusTest
public class CmdbCliTest {

    @Inject @TopCommand
    CmdbCli cmdbCli;

    @Inject
    SharedData sharedData;

    @InjectMock
    FileDataRepositoryImpl fileDataRepository;

    CliParameterParser parser;

    private final ObjectMapper yamlMapper = new ObjectMapper(new YAMLFactory());

    @Test
    void testEffectiveSetFolderGeneration() throws Exception {
        // Mock parser to copy folder
        parser = Mockito.mock(CliParameterParser.class);
        cmdbCli.parser = parser;
        Mockito.doNothing().when(fileDataRepository).prepareProcessingEnv();
        Mockito.doAnswer(invocation -> {
            Path outputDir = Path.of(cmdbCli.envParams.outputDir);
            Files.createDirectories(outputDir);
            Path source = Paths.get(getClass().getClassLoader().getResource("expected-folder").toURI());
            Files.walk(source).forEach(src -> {
                try {
                    Path dest = outputDir.resolve(source.relativize(src));
                    if (Files.isDirectory(src)) Files.createDirectories(dest);
                    else Files.copy(src, dest, REPLACE_EXISTING);
                } catch (Exception e) { throw new RuntimeException(e); }
            });
            return null;
        }).when(parser).generateEffectiveSet();

        // CLI args
        CmdbCli.EnvCommandSpace env = new CmdbCli.EnvCommandSpace();
        env.envId = "example/env-1";
        env.envsPath = "src/test/resources/";
        env.outputDir = "target/effective-set-output";
        env.version = "v2.0";
        env.extraParams = new String[]{"DEPLOYMENT_SESSION_ID=ABC123"};
        cmdbCli.envParams = env;

        // Act
        int code = cmdbCli.call();

        // Assert shared data
        assertEquals(0, code);
        assertEquals("example/env-1", sharedData.getEnvId());
        assertEquals("ABC123", sharedData.getDeploymentSessionId());
        Mockito.verify(fileDataRepository).prepareProcessingEnv();
        Mockito.verify(parser).generateEffectiveSet();

        // Compare folders recursively
        Path generated = Path.of(env.outputDir);
        Path expected = Paths.get(getClass().getClassLoader().getResource("expected-folder").toURI());
        Files.walk(expected).forEach(path -> {
            try {
                Path rel = expected.relativize(path);
                Path act = generated.resolve(rel);
                assertTrue(Files.exists(act), "Missing: " + act);
                if (Files.isRegularFile(path)) {
                    if (path.toString().endsWith(".yaml") || path.toString().endsWith(".yml")) {
                        try (InputStream inExp = Files.newInputStream(path);
                             InputStream inAct = Files.newInputStream(act)) {
                            assertEquals(yamlMapper.readTree(inExp), yamlMapper.readTree(inAct),
                                    "YAML mismatch: " + act);
                        }
                    } else {
                        assertArrayEquals(Files.readAllBytes(path), Files.readAllBytes(act),
                                "File mismatch: " + act);
                    }
                }
            } catch (Exception e) { throw new RuntimeException(e); }
        });
    }
}
