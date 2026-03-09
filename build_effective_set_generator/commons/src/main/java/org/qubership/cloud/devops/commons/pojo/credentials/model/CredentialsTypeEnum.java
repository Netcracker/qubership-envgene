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

package org.qubership.cloud.devops.commons.pojo.credentials.model;


import lombok.Getter;

@Getter
public enum CredentialsTypeEnum {
    secret(Constants.SECRET_VALUE),
    secretFile(Constants.SECRET_FILE_VALUE),
    usernamePassword(Constants.USERNAME_PASSWORD_VALUE),
    vaultAppRole(Constants.VAULT_APP_ROLE_VALUE);
    private final String type;

    CredentialsTypeEnum(String type) {
        this.type = type;
    }

    public static class Constants {
        public static final String SECRET_VALUE = "secret";
        public static final String SECRET_FILE_VALUE = "secretFile";
        public static final String USERNAME_PASSWORD_VALUE = "usernamePassword";
        public static final String VAULT_APP_ROLE_VALUE = "vaultAppRole";
    }
}
