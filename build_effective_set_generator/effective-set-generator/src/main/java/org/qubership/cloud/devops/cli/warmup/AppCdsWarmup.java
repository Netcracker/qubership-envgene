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

import lombok.extern.slf4j.Slf4j;
import org.qubership.cloud.devops.cli.parser.CliParameterParser;
import org.qubership.cloud.devops.cli.pojo.dto.shared.EffectiveSetVersion;
import org.qubership.cloud.devops.cli.pojo.dto.shared.SharedData;
import org.qubership.cloud.devops.cli.repository.implementation.FileDataRepositoryImpl;
import org.qubership.cloud.devops.commons.utils.Parameter;
import org.qubership.cloud.parameters.processor.expression.ExpressionLanguage;
import org.qubership.cloud.parameters.processor.expression.binding.Binding;

import java.io.IOException;
import java.io.InputStream;
import java.net.JarURLConnection;
import java.net.URISyntaxException;
import java.net.URL;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.nio.file.StandardCopyOption;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.Enumeration;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.jar.JarEntry;
import java.util.jar.JarFile;
import java.util.stream.Stream;

@Slf4j
public final class AppCdsWarmup {

    private static final String WARMUP_ENV_ID = "cluster-01/pl-01";
    private static final String WARMUP_RESOURCES = "warmup-env";

    private AppCdsWarmup() {
    }

    public static void run(SharedData sharedData,
                           FileDataRepositoryImpl fileDataRepository,
                           CliParameterParser parser) {
        warmupExpressions();
        warmupPipeline(sharedData, fileDataRepository, parser);
    }

    private static void warmupPipeline(SharedData sharedData,
                                       FileDataRepositoryImpl fileDataRepository,
                                       CliParameterParser parser) {
        Path directory;
        try {
            directory = Files.createTempDirectory("envgene-appcds-warmup");
        } catch (IOException exception) {
            throw new IllegalStateException("Failed to create the AppCDS warmup directory", exception);
        }
        try {
            copyResourceTree(WARMUP_RESOURCES, directory);
            Path envsPath = directory.resolve("environments");
            Path envPath = envsPath.resolve(WARMUP_ENV_ID);

            sharedData.setEffectiveSetVersion(EffectiveSetVersion.V2_0);
            sharedData.setEnvId(WARMUP_ENV_ID);
            sharedData.setEnvsPath(envsPath.toString());
            sharedData.setSbomsPath(Optional.of(directory.resolve("sboms").toString()));
            sharedData.setDeployPlanPath(Optional.of(envPath.resolve("Inventory/deploy-plan.yml").toString()));
            sharedData.setRegistryPath(Optional.of(directory.resolve("configuration/registry.yml").toString()));
            sharedData.setOutputDir(directory.resolve("effective-set").toString());
            sharedData.setCredsOutput(directory.resolve("creds.json").toString());
            sharedData.setPcsspPaths(new ArrayList<>());
            sharedData.setDeploymentSessionId("appcds-warmup");
            sharedData.setGenerateCleanupContext(false);

            InputStream originalIn = System.in;
            try (InputStream credentials = Files.newInputStream(envPath.resolve("Credentials/credentials.yml"))) {
                System.setIn(credentials);
                fileDataRepository.prepareProcessingEnv();
                parser.generateEffectiveSet();
            } finally {
                System.setIn(originalIn);
            }
            if (!containsFile(directory.resolve("effective-set"))) {
                throw new IllegalStateException(
                        "The AppCDS warmup generated no effective set in " + directory.resolve("effective-set"));
            }
        } catch (IOException exception) {
            throw new IllegalStateException(
                    "Failed to prepare or run the AppCDS warmup pipeline from resources '" + WARMUP_RESOURCES + "'", exception);
        } finally {
            deleteTree(directory);
        }
    }

    private static boolean containsFile(Path directory) throws IOException {
        if (!Files.isDirectory(directory)) {
            return false;
        }
        try (Stream<Path> paths = Files.walk(directory)) {
            return paths.anyMatch(Files::isRegularFile);
        }
    }

    private static void copyResourceTree(String resourceRoot, Path target) throws IOException {
        URL url = AppCdsWarmup.class.getClassLoader().getResource(resourceRoot);
        if (url == null) {
            throw new IllegalStateException("Missing AppCDS warmup resources: " + resourceRoot);
        }
        if ("file".equals(url.getProtocol())) {
            copyFileTree(url, target);
        } else if ("jar".equals(url.getProtocol())) {
            copyJarTree(url, resourceRoot, target);
        } else {
            throw new IllegalStateException("Unsupported resource protocol: " + url.getProtocol());
        }
    }

    private static void copyFileTree(URL url, Path target) throws IOException {
        Path source;
        try {
            source = Paths.get(url.toURI());
        } catch (URISyntaxException exception) {
            throw new IOException(exception);
        }
        try (Stream<Path> paths = Files.walk(source)) {
            for (Path path : (Iterable<Path>) paths.filter(Files::isRegularFile)::iterator) {
                Path destination = target.resolve(source.relativize(path).toString());
                Files.createDirectories(destination.getParent());
                Files.copy(path, destination, StandardCopyOption.REPLACE_EXISTING);
            }
        }
    }

    private static void copyJarTree(URL url, String resourceRoot, Path target) throws IOException {
        JarURLConnection connection = (JarURLConnection) url.openConnection();
        connection.setUseCaches(false);
        String prefix = resourceRoot + "/";
        try (JarFile jar = connection.getJarFile()) {
            Enumeration<JarEntry> entries = jar.entries();
            while (entries.hasMoreElements()) {
                JarEntry entry = entries.nextElement();
                if (!entry.getName().startsWith(prefix) || entry.isDirectory()) {
                    continue;
                }
                Path destination = target.resolve(entry.getName().substring(prefix.length()));
                Files.createDirectories(destination.getParent());
                try (InputStream input = jar.getInputStream(entry)) {
                    Files.copy(input, destination, StandardCopyOption.REPLACE_EXISTING);
                }
            }
        }
    }

    private static void deleteTree(Path directory) {
        try (Stream<Path> paths = Files.walk(directory)) {
            paths.sorted(Comparator.reverseOrder()).forEach(path -> {
                try {
                    Files.deleteIfExists(path);
                } catch (IOException exception) {
                    log.warn("Failed to delete the AppCDS warmup file {}", path, exception);
                }
            });
        } catch (IOException exception) {
            log.warn("Failed to clean up the AppCDS warmup directory {}", directory, exception);
        }
    }

    private static void warmupExpressions() {
        Map<String, Parameter> tenant = map(
                "TENANT_ONLY", "tenant-only",
                "SHARED", "tenant-shared",
                "REF_TENANT", "${TENANT_ONLY}",
                "CHAIN_A", "${CHAIN_B}",
                "CHAIN_B", "${CHAIN_C}",
                "CHAIN_C", "chain-value",
                "INT_VALUE", 27017,
                "INT_REF", "${INT_VALUE}",
                "BOOL_VALUE", true,
                "BOOL_REF", "${BOOL_VALUE}",
                "PLAIN", "plain text",
                "SECURED", "secret",
                "DOLLAR", "\\$",
                "NESTED", map(
                        "INNER", "${TENANT_ONLY}",
                        "LIST", new ArrayList<>(List.of(
                                new Parameter("${TENANT_ONLY}"), new Parameter("literal")))),
                "GROOVY_VALUE", "first second third",
                "GROOVY_CHECK", "${GROOVY_VALUE instanceof String}",
                "LOWER", "${lower(TENANT_ONLY)}",
                "COMMENT", "before<# hidden #>after");
        Map<String, Parameter> cloud = map(
                "CLOUD_ONLY", "cloud-only",
                "SHARED", "cloud-shared",
                "REF_TENANT", "${TENANT_ONLY}",
                "app", map(
                        "CLOUD_APP_ONLY", "cloud-app-only",
                        "SHARED", "cloud-app-shared"),
                "namespace", map(
                        "NS_ONLY", "ns-only",
                        "SHARED", "ns-shared",
                        "REF_TENANT", "${TENANT_ONLY}",
                        "app", map(
                                "NS_APP_ONLY", "ns-app-only",
                                "SHARED", "ns-app-shared")));
        tenant.put("cloud", new Parameter(cloud));

        Binding binding = new Binding();
        binding.put("tenant", new Parameter(tenant));
        binding.put("application", new Parameter(map(
                "APP_ONLY", "app-only",
                "SHARED", "app-shared")));
        binding.setDefault("");
        new ExpressionLanguage(binding).processDeployment();

        Map<String, Parameter> configTenant = map(
                "config-server", map(
                        "CS_SHARED", "tenant-cs-shared",
                        "CS_TENANT_ONLY", "tenant-cs-only",
                        "CS_REF_CLOUD", "${CS_CLOUD_ONLY}"));
        configTenant.put("cloud", new Parameter(map(
                "config-server", map(
                        "CS_SHARED", "cloud-cs-shared",
                        "CS_CLOUD_ONLY", "cloud-cs-only",
                        "CS_REF_TENANT", "${CS_TENANT_ONLY}"),
                "app", map(
                        "config-server", map(
                                "CS_SHARED", "cloud-app-cs-shared",
                                "CS_CLOUD_APP_ONLY", "cloud-app-cs-only")),
                "namespace", map(
                        "config-server", map(
                                "CS_SHARED", "ns-cs-shared",
                                "CS_NS_ONLY", "ns-cs-only",
                                "CS_REF_TENANT", "${CS_TENANT_ONLY}"),
                        "app", map(
                                "config-server", map(
                                        "CS_SHARED", "ns-app-cs-shared",
                                        "CS_NS_APP_ONLY", "ns-app-cs-only"))))));

        Binding configBinding = new Binding();
        configBinding.put("tenant", new Parameter(configTenant));
        configBinding.setDefault("");
        new ExpressionLanguage(configBinding).processConfigServerApp();
    }

    private static Map<String, Parameter> map(Object... keyValues) {
        Map<String, Parameter> parameters = new LinkedHashMap<>();
        for (int index = 0; index < keyValues.length; index += 2) {
            parameters.put((String) keyValues[index], new Parameter(keyValues[index + 1]));
        }
        return parameters;
    }
}
