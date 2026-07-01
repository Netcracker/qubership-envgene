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

import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.dataformat.yaml.YAMLFactory;
import jakarta.enterprise.context.ApplicationScoped;
import org.qubership.cloud.extcreds.valsref.ExternalCredValsException;
import org.qubership.cloud.extcreds.valsref.SecretStoreConfig;
import org.qubership.cloud.extcreds.valsref.SecretStoreType;
import org.qubership.cloud.extcreds.valsref.ValsReferenceBuilder;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

@ApplicationScoped
public class ValsRefBatchProcessor {

    private static final String DEFAULT_STORE = "default_store";
    private static final String EXTERNAL_TYPE = "external";

    private final ObjectMapper jsonMapper = new ObjectMapper();
    private final ObjectMapper yamlMapper = new ObjectMapper(new YAMLFactory());

    public CliOutput process(Path credentialsPath, Path secretStoresPath, Path requestsPath, OutputFields fields)
            throws IOException {
        CliInput input = loadInput(credentialsPath, secretStoresPath, requestsPath);
        return process(input, fields);
    }

    public CliOutput process(CliInput input, OutputFields fields) {
        CliOutput output = new CliOutput();
        List<CliInput.RequestInput> requests = resolveRequests(input);
        for (CliInput.RequestInput request : requests) {
            processRequest(input, request, fields, output);
        }
        return output;
    }

    private CliInput loadInput(Path credentialsPath, Path secretStoresPath, Path requestsPath) throws IOException {
        CliInput input = new CliInput();
        input.setCredentials(readCredentials(credentialsPath));
        input.setSecretStores(readSecretStores(secretStoresPath));
        if (requestsPath != null) {
            input.setRequests(readRequests(requestsPath));
        }
        return input;
    }

    @SuppressWarnings("unchecked")
    private Map<String, CliInput.CredentialInput> readCredentials(Path credentialsPath) throws IOException {
        Map<String, Object> raw = yamlMapper.readValue(credentialsPath.toFile(), Map.class);
        Map<String, CliInput.CredentialInput> credentials = new LinkedHashMap<>();
        for (Map.Entry<String, Object> entry : raw.entrySet()) {
            credentials.put(entry.getKey(), jsonMapper.convertValue(entry.getValue(), CliInput.CredentialInput.class));
        }
        return credentials;
    }

    @SuppressWarnings("unchecked")
    private Map<String, Map<String, Object>> readSecretStores(Path secretStoresPath) throws IOException {
        return yamlMapper.readValue(secretStoresPath.toFile(), Map.class);
    }

    private List<CliInput.RequestInput> readRequests(Path requestsPath) throws IOException {
        if (requestsPath.toString().endsWith(".json")) {
            CliInput input = jsonMapper.readValue(requestsPath.toFile(), CliInput.class);
            return input.getRequests();
        }
        Map<String, Object> raw = yamlMapper.readValue(requestsPath.toFile(), Map.class);
        Object requests = raw.get("requests");
        if (requests == null) {
            return List.of();
        }
        return jsonMapper.convertValue(
                requests,
                jsonMapper.getTypeFactory().constructCollectionType(List.class, CliInput.RequestInput.class)
        );
    }

    private List<CliInput.RequestInput> resolveRequests(CliInput input) {
        if (input.getRequests() != null && !input.getRequests().isEmpty()) {
            return input.getRequests();
        }
        List<CliInput.RequestInput> requests = new ArrayList<>();
        for (Map.Entry<String, CliInput.CredentialInput> entry : input.getCredentials().entrySet()) {
            CliInput.CredentialInput credential = entry.getValue();
            if (!EXTERNAL_TYPE.equals(credential.getType())) {
                continue;
            }
            CliInput.RequestInput request = new CliInput.RequestInput();
            request.setCredId(entry.getKey());
            requests.add(request);
        }
        return requests;
    }

    private void processRequest(
            CliInput input,
            CliInput.RequestInput request,
            OutputFields fields,
            CliOutput output
    ) {
        String credId = request.getCredId();
        CliInput.CredentialInput credential = input.getCredentials().get(credId);
        if (credential == null) {
            output.getErrors().add(new CliOutput.ErrorEntry(credId, request.getProperty(), "Credential not found"));
            return;
        }
        if (!EXTERNAL_TYPE.equals(credential.getType())) {
            output.getErrors().add(new CliOutput.ErrorEntry(credId, request.getProperty(), "Credential is not external"));
            return;
        }
        String storeId = credential.getSecretStore() == null || credential.getSecretStore().isBlank()
                ? DEFAULT_STORE
                : credential.getSecretStore();
        Map<String, Object> storeRaw = input.getSecretStores().get(storeId);
        if (storeRaw == null) {
            output.getErrors().add(new CliOutput.ErrorEntry(
                    credId, request.getProperty(), "Secret store '" + storeId + "' not found"));
            return;
        }
        try {
            SecretStoreConfig store = toStoreConfig(storeRaw);
            List<String> propertyNames = credential.getProperties() == null
                    ? List.of()
                    : credential.getProperties().stream().map(CliInput.PropertyInput::getName).toList();
            CliOutput.ResultEntry result = new CliOutput.ResultEntry();
            result.setCredId(credId);
            result.setProperty(request.getProperty());
            if (fields.includeNormalized()) {
                result.setNormalizedSecretName(
                        ValsReferenceBuilder.buildNormalizedSecretName(
                                credId, credential.getRemoteRefPath(), store));
            }
            if (fields.includeVals()) {
                result.setValsReference(ValsReferenceBuilder.buildValsReference(
                        credId,
                        credential.getRemoteRefPath(),
                        request.getProperty(),
                        propertyNames,
                        store
                ));
            }
            output.getResults().add(result);
        } catch (ExternalCredValsException e) {
            output.getErrors().add(new CliOutput.ErrorEntry(credId, request.getProperty(), e.getMessage()));
        }
    }

    private SecretStoreConfig toStoreConfig(Map<String, Object> storeRaw) {
        String typeValue = String.valueOf(storeRaw.get("type"));
        return SecretStoreConfig.builder()
                .type(SecretStoreType.valueOf(typeValue))
                .mountPath(asString(storeRaw.get("mountPath")))
                .vaultName(asString(storeRaw.get("vaultName")))
                .region(asString(storeRaw.get("region")))
                .projectId(asString(storeRaw.get("projectId")))
                .build();
    }

    private String asString(Object value) {
        return value == null ? null : value.toString();
    }

    public enum OutputFields {
        NORMALIZED,
        VALS,
        BOTH;

        boolean includeNormalized() {
            return this == NORMALIZED || this == BOTH;
        }

        boolean includeVals() {
            return this == VALS || this == BOTH;
        }
    }
}
