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

package org.qubership.cloud.extcreds.valsref;

public final class SecretStoreConfig {

    private final SecretStoreType type;
    private final String mountPath;
    private final String vaultName;
    private final String region;
    private final String projectId;

    private SecretStoreConfig(Builder builder) {
        this.type = builder.type;
        this.mountPath = builder.mountPath;
        this.vaultName = builder.vaultName;
        this.region = builder.region;
        this.projectId = builder.projectId;
    }

    public SecretStoreType getType() {
        return type;
    }

    public String getMountPath() {
        return mountPath;
    }

    public String getVaultName() {
        return vaultName;
    }

    public String getRegion() {
        return region;
    }

    public String getProjectId() {
        return projectId;
    }

    public static Builder builder() {
        return new Builder();
    }

    public static final class Builder {
        private SecretStoreType type;
        private String mountPath;
        private String vaultName;
        private String region;
        private String projectId;

        public Builder type(SecretStoreType type) {
            this.type = type;
            return this;
        }

        public Builder mountPath(String mountPath) {
            this.mountPath = mountPath;
            return this;
        }

        public Builder vaultName(String vaultName) {
            this.vaultName = vaultName;
            return this;
        }

        public Builder region(String region) {
            this.region = region;
            return this;
        }

        public Builder projectId(String projectId) {
            this.projectId = projectId;
            return this;
        }

        public SecretStoreConfig build() {
            return new SecretStoreConfig(this);
        }
    }
}
