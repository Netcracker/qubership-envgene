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

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonProperty;

import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

@JsonIgnoreProperties(ignoreUnknown = true)
public class CliInput {

    @JsonProperty("secretStores")
    private Map<String, Map<String, Object>> secretStores = new LinkedHashMap<>();

    @JsonProperty("credentials")
    private Map<String, CredentialInput> credentials = new LinkedHashMap<>();

    @JsonProperty("requests")
    private List<RequestInput> requests = new ArrayList<>();

    public Map<String, Map<String, Object>> getSecretStores() {
        return secretStores;
    }

    public void setSecretStores(Map<String, Map<String, Object>> secretStores) {
        this.secretStores = secretStores;
    }

    public Map<String, CredentialInput> getCredentials() {
        return credentials;
    }

    public void setCredentials(Map<String, CredentialInput> credentials) {
        this.credentials = credentials;
    }

    public List<RequestInput> getRequests() {
        return requests;
    }

    public void setRequests(List<RequestInput> requests) {
        this.requests = requests;
    }

    @JsonIgnoreProperties(ignoreUnknown = true)
    public static class CredentialInput {

        @JsonProperty("type")
        private String type;

        @JsonProperty("secretStore")
        private String secretStore;

        @JsonProperty("remoteRefPath")
        private String remoteRefPath;

        @JsonProperty("properties")
        private List<PropertyInput> properties = new ArrayList<>();

        public String getType() {
            return type;
        }

        public void setType(String type) {
            this.type = type;
        }

        public String getSecretStore() {
            return secretStore;
        }

        public void setSecretStore(String secretStore) {
            this.secretStore = secretStore;
        }

        public String getRemoteRefPath() {
            return remoteRefPath;
        }

        public void setRemoteRefPath(String remoteRefPath) {
            this.remoteRefPath = remoteRefPath;
        }

        public List<PropertyInput> getProperties() {
            return properties;
        }

        public void setProperties(List<PropertyInput> properties) {
            this.properties = properties;
        }
    }

    @JsonIgnoreProperties(ignoreUnknown = true)
    public static class PropertyInput {

        @JsonProperty("name")
        private String name;

        public String getName() {
            return name;
        }

        public void setName(String name) {
            this.name = name;
        }
    }

    @JsonIgnoreProperties(ignoreUnknown = true)
    public static class RequestInput {

        @JsonProperty("credId")
        private String credId;

        @JsonProperty("property")
        private String property;

        public String getCredId() {
            return credId;
        }

        public void setCredId(String credId) {
            this.credId = credId;
        }

        public String getProperty() {
            return property;
        }

        public void setProperty(String property) {
            this.property = property;
        }
    }
}
