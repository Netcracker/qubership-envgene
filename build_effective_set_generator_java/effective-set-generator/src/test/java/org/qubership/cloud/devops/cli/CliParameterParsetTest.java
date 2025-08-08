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
import com.fasterxml.jackson.dataformat.yaml.YAMLFactory;
import io.quarkus.test.junit.QuarkusTest;
import org.apache.commons.io.FileUtils;
import org.junit.jupiter.api.AfterAll;
import org.junit.jupiter.api.BeforeAll;
import org.junit.jupiter.api.Test;
import org.yaml.snakeyaml.Yaml;
import org.junit.jupiter.api.Disabled;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.qubership.cloud.devops.cli.TestConstants.GENERATED_CREDENTIALS_YAML;


import java.io.*;
import java.net.URISyntaxException;
import java.net.URL;
import java.util.HashMap;
import java.util.Map;
import java.util.stream.Collectors;


@QuarkusTest
//@Disabled
public class CliParameterParsetTest extends BaseInit {

    private final ObjectMapper objectMapper = new ObjectMapper(new YAMLFactory());


    @BeforeAll
    public static void generateEffectSetTest() throws IOException {
        cliParameterParser.generateEffectiveSet();
    }

    @AfterAll
    public static void cleanUp() throws IOException {
        File folderToBeDeleted = pathDir.toFile();
        if (folderToBeDeleted.exists()) {
            FileUtils.forceDelete(folderToBeDeleted);
        }
    }

    @Test
    void validateCredentialFile() throws URISyntaxException, IOException {
        URL storedCredsFileURL = getClass().getClassLoader().getResource(TestConstants.STORED_CREDENTIALS_YAML);
        assert storedCredsFileURL != null;
        File storedCredsFile = new File(storedCredsFileURL.toURI());
        Map<String, Object> storedCreds = objectMapper.readValue(storedCredsFile,
                new TypeReference<HashMap<String, Object>>() {
                });


        File credsFile = new File(String.format("%s/%s", pathDir.toFile().getAbsolutePath(), GENERATED_CREDENTIALS_YAML));
        Map<String, Object> generatedCreds = objectMapper.readValue(credsFile,
                new TypeReference<HashMap<String, Object>>() {
                });
        assertEquals(storedCreds, generatedCreds);
    }

    @Test
    void validateDeployParamsFile() throws IOException {
        Yaml yaml = new Yaml();
        InputStream inputStream1  = getClass().getClassLoader().getResourceAsStream(TestConstants.STORED_PARAMS_YAML);
        Map<String, Object> storedParams = yaml.load(inputStream1);

        File file = new File(String.format("%s/%s", pathDir.toFile().getAbsolutePath(), TestConstants.GENERATED_PARAMS_YAML));
        Map<String, Object> generatedParams;
        try (FileInputStream targetStream = new FileInputStream(file)) {
            generatedParams = yaml.load(targetStream);
        }
        generatedParams.remove("DEPLOYMENT_SESSION_ID");
        ((Map<String, String>) generatedParams.get("global")).remove("DEPLOYMENT_SESSION_ID");
        ((Map<String, String>) generatedParams.get("service-test")).remove("DEPLOYMENT_SESSION_ID");
        Map<String, Object> result = storedParams.entrySet()
                .stream()
                .filter(e -> !generatedParams.containsKey(e.getKey()))
                .collect(Collectors.toMap(Map.Entry::getKey, Map.Entry::getValue));
        assertEquals(storedParams, generatedParams);
    }

    @Test
    void validateTechFile() throws URISyntaxException, IOException {

        URL storedTechFileURL = getClass().getClassLoader().getResource(TestConstants.STORED_TECHPARAM_YAML);
        assert storedTechFileURL != null;
        File storedTechFile = new File(storedTechFileURL.toURI());
        Map<String, String> storedTechParams = objectMapper.readValue(storedTechFile,
                new TypeReference<HashMap<String, String>>() {
                });

        File techFile = new File(String.format("%s/%s", pathDir.toFile().getAbsolutePath(), TestConstants.GENERATED_TECHPARAM_YAML));
        Map<String, String> generatedTechParams = objectMapper.readValue(techFile,
                new TypeReference<HashMap<String, String>>() {
                });

        assertEquals(storedTechParams, generatedTechParams);
    }

    @Test
    void validateMappingFile() throws URISyntaxException, IOException {
        URL storedTechFileURL = getClass().getClassLoader().getResource(TestConstants.STORED_MAPPING_YAML);
        assert storedTechFileURL != null;
        File storedMappingFile = new File(storedTechFileURL.toURI());
        Map<String, String> storedMappingProps = objectMapper.readValue(storedMappingFile,
                new TypeReference<HashMap<String, String>>() {
                });

        File mappingFile = new File(String.format("%s/%s", pathDir.toFile().getAbsolutePath(), TestConstants.GENERATED_MAPPING_YAML));
        Map<String, String> generatedMappingProps = objectMapper.readValue(mappingFile,
                new TypeReference<HashMap<String, String>>() {
                });
        assertEquals(storedMappingProps, generatedMappingProps);
    }


}
