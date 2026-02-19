package org.qubership.cloud.devops.cli.repository.implementation;

import org.junit.jupiter.api.Test;
import org.mockito.Mockito;
import org.qubership.cloud.devops.cli.utils.FileSystemUtils;
import org.qubership.cloud.devops.commons.utils.Parameter;

import java.io.File;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

import static org.junit.jupiter.api.Assertions.*;

class FileDataConverterImplTest {

    @Test
    void shouldWriteYamlToConcreteWindowsPath() throws Exception {

        String outputPath = "C:/Kamal/test/result.yaml";
        Files.createDirectories(Path.of("C:/Kamal/test"));

        File outputFile = new File(outputPath);


        FileSystemUtils fs = Mockito.mock(FileSystemUtils.class);
        Mockito.when(fs.getFileFromGivenPath(Mockito.any()))
                .thenReturn(outputFile);


        FileDataConverterImpl converter =
                new FileDataConverterImpl(fs);


        Map<String, Object> data = buildFullCombinationTestData();

        converter.writeToFile(data, "ignored");


        assertTrue(outputFile.exists());


        String content = Files.readString(outputFile.toPath());

        System.out.println(content);
    }


    private Map<String, Object> buildFullCombinationTestData() {

        Map<String, Object> root = new LinkedHashMap<>();


        root.put("stringValue", "plainText");
        root.put("intValue", 100);
        root.put("booleanValue", true);
        root.put("nullValue", null);

        root.put("paramString",
                new Parameter("value1", "system",false));

        root.put("paramNumber",
                new Parameter(200, "default",false));


        root.put("paramBlankOrigin",
                new Parameter("noComment", "",false));


        root.put("paramNullOrigin",
                new Parameter("noComment2", null,false));


        root.put("multiLineParam",
                new Parameter("line1\nline2\nline3", "file",false));


        root.put("simpleList", List.of("a", "b", "c"));

        root.put("emptyList", new ArrayList<>());


        root.put("paramList", List.of(
                new Parameter("srv1", "inventory",false),
                new Parameter("srv2", "inventory",false)
        ));


        root.put("mixedList", List.of(
                8080,
                new Parameter(9090, "config",false),
                "text",
                new Parameter("text2", "runtime",false)
        ));


        root.put("listOfMaps", List.of(
                Map.of(
                        "name", new Parameter("dev", "profile",false),
                        "enabled", true
                ),
                Map.of(
                        "name", new Parameter("prod", "profile",false),
                        "enabled", false
                )
        ));

        root.put("nestedMap", Map.of(
                "level1", Map.of(
                        "level2", new Parameter("deepValue", "deepOrigin",false)
                )
        ));

        root.put("mapOfLists", Map.of(
                "numbers", List.of(
                        new Parameter(1, "src",false),
                        2,
                        3
                ),
                "strings", List.of(
                        "x",
                        new Parameter("y", "src",false)
                )
        ));

        root.put("paramWrappingMap",
                new Parameter(
                        Map.of(
                                "innerKey",
                                new Parameter("innerValue", "innerOrigin",false)
                        ),
                        "outerOrigin",false
                )
        );

        root.put("paramWrappingList",
                new Parameter(
                        List.of(
                                new Parameter("inside1", "listOrigin",false),
                                "plainInside"
                        ),
                        "outerListOrigin",false
                )
        );


        root.put("emptyMap", new LinkedHashMap<>());


        root.put("mergeExample", "!merge");

        return root;
    }
}
