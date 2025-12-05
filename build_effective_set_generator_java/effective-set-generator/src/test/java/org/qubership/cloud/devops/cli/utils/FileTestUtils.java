package org.qubership.cloud.devops.cli.utils;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.dataformat.yaml.YAMLFactory;
import lombok.experimental.UtilityClass;

import java.io.IOException;
import java.io.InputStream;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.HashSet;
import java.util.Set;

import static org.junit.jupiter.api.Assertions.*;

@UtilityClass
public class FileTestUtils {

    private final ObjectMapper YAML_MAPPER = new ObjectMapper(new YAMLFactory());

    public void compareFolders(Path expected, Path generated) throws IOException {
        Set<Path> expectedFiles = listRelativePaths(expected);
        Set<Path> generatedFiles = listRelativePaths(generated);

        for (Path rel : expectedFiles) {
            Path expectedPath = expected.resolve(rel);
            Path generatedPath = generated.resolve(rel);

            assertTrue(Files.exists(generatedPath), "Missing file/folder: " + generatedPath);

            if (Files.isRegularFile(expectedPath)) {
                compareFiles(expectedPath, generatedPath);
            }
        }

        for (Path rel : generatedFiles) {
            assertTrue(expectedFiles.contains(rel),
                    "Unexpected file/folder: " + generated.resolve(rel));
        }
    }

    public void compareFiles(Path expected, Path generated) throws IOException {
        if (isYaml(expected)) {
            compareYaml(expected, generated);
        } else {
            compareBinary(expected, generated);
        }
    }

    public boolean isYaml(Path path) {
        String name = path.toString().toLowerCase();
        return name.endsWith(".yaml") || name.endsWith(".yml");
    }

    public void compareYaml(Path expected, Path generated) throws IOException {
        try (InputStream inExp = Files.newInputStream(expected);
             InputStream inGen = Files.newInputStream(generated)) {

            assertEquals(
                    YAML_MAPPER.readTree(inExp),
                    YAML_MAPPER.readTree(inGen),
                    "YAML content mismatch: " + generated
            );
        }
    }

    public void compareBinary(Path expected, Path generated) throws IOException {
        assertArrayEquals(
                Files.readAllBytes(expected),
                Files.readAllBytes(generated),
                "File content mismatch: " + generated
        );
    }

    public Set<Path> listRelativePaths(Path root) throws IOException {
        Set<Path> paths = new HashSet<>();
        try (var stream = Files.walk(root)) {
            stream.forEach(p -> paths.add(root.relativize(p)));
        }
        return paths;
    }
}
