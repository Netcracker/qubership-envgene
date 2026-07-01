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

package org.qubership.cloud.extcreds.valsref.cli;

import io.quarkus.picocli.runtime.annotations.TopCommand;
import io.quarkus.test.junit.QuarkusTest;
import jakarta.inject.Inject;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import picocli.CommandLine;

import java.nio.file.Files;
import java.nio.file.Path;

import static org.junit.jupiter.api.Assertions.assertEquals;

@QuarkusTest
class ExtCredsValsRefCliTest {

    @TopCommand
    @Inject
    ExtCredsValsRefCli cli;

    @Test
    void resolvesVaultCredential(@TempDir Path tempDir) throws Exception {
        Path credentials = tempDir.resolve("credentials.yml");
        Files.writeString(credentials, """
                app-sidecar-token:
                  type: external
                  secretStore: default_store
                  remoteRefPath: test_cluster_01/env-1
                """);

        Path secretStores = tempDir.resolve("secret-stores.yml");
        Files.writeString(secretStores, """
                default_store:
                  type: vault
                  mountPath: secret/data/app
                """);

        CommandLine cmd = new CommandLine(cli);
        int exitCode = cmd.execute(
                "--credentials", credentials.toString(),
                "--secret-stores", secretStores.toString()
        );

        assertEquals(0, exitCode);
    }

    @Test
    void resolvesRequestedProperty(@TempDir Path tempDir) throws Exception {
        Path credentials = tempDir.resolve("credentials.yml");
        Files.writeString(credentials, """
                app-dbaas-cred:
                  type: external
                  secretStore: dbaas_store
                  remoteRefPath: test-cluster-01/env-1
                  properties:
                    - name: username
                    - name: password
                """);

        Path secretStores = tempDir.resolve("secret-stores.yml");
        Files.writeString(secretStores, """
                dbaas_store:
                  type: gcp
                  projectId: agf56hoji8
                """);

        Path requests = tempDir.resolve("requests.json");
        Files.writeString(requests, """
                {
                  "requests": [
                    { "credId": "app-dbaas-cred", "property": "username" }
                  ]
                }
                """);

        CommandLine cmd = new CommandLine(cli);
        int exitCode = cmd.execute(
                "--credentials", credentials.toString(),
                "--secret-stores", secretStores.toString(),
                "--requests", requests.toString(),
                "--fields", "both"
        );

        assertEquals(0, exitCode);
    }

    @Test
    void reportsMissingCredential(@TempDir Path tempDir) throws Exception {
        Path credentials = tempDir.resolve("credentials.yml");
        Files.writeString(credentials, "{}\n");

        Path secretStores = tempDir.resolve("secret-stores.yml");
        Files.writeString(secretStores, """
                default_store:
                  type: vault
                  mountPath: secret/data/app
                """);

        Path requests = tempDir.resolve("requests.json");
        Files.writeString(requests, """
                {
                  "requests": [
                    { "credId": "missing-cred" }
                  ]
                }
                """);

        CommandLine cmd = new CommandLine(cli);
        int exitCode = cmd.execute(
                "--credentials", credentials.toString(),
                "--secret-stores", secretStores.toString(),
                "--requests", requests.toString()
        );

        assertEquals(1, exitCode);
    }
}
