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

import com.fasterxml.jackson.annotation.JsonInclude;
import com.fasterxml.jackson.annotation.JsonProperty;

import java.util.ArrayList;
import java.util.List;

@JsonInclude(JsonInclude.Include.NON_NULL)
public class CliOutput {

    @JsonProperty("results")
    private List<ResultEntry> results = new ArrayList<>();

    @JsonProperty("errors")
    private List<ErrorEntry> errors = new ArrayList<>();

    public List<ResultEntry> getResults() {
        return results;
    }

    public void setResults(List<ResultEntry> results) {
        this.results = results;
    }

    public List<ErrorEntry> getErrors() {
        return errors;
    }

    public void setErrors(List<ErrorEntry> errors) {
        this.errors = errors;
    }

    @JsonInclude(JsonInclude.Include.NON_NULL)
    public static class ResultEntry {

        @JsonProperty("credId")
        private String credId;

        @JsonProperty("property")
        private String property;

        @JsonProperty("normalizedSecretName")
        private String normalizedSecretName;

        @JsonProperty("valsReference")
        private String valsReference;

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

        public String getNormalizedSecretName() {
            return normalizedSecretName;
        }

        public void setNormalizedSecretName(String normalizedSecretName) {
            this.normalizedSecretName = normalizedSecretName;
        }

        public String getValsReference() {
            return valsReference;
        }

        public void setValsReference(String valsReference) {
            this.valsReference = valsReference;
        }
    }

    public static class ErrorEntry {

        @JsonProperty("credId")
        private String credId;

        @JsonProperty("property")
        private String property;

        @JsonProperty("message")
        private String message;

        public ErrorEntry() {
        }

        public ErrorEntry(String credId, String property, String message) {
            this.credId = credId;
            this.property = property;
            this.message = message;
        }

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

        public String getMessage() {
            return message;
        }

        public void setMessage(String message) {
            this.message = message;
        }
    }
}
