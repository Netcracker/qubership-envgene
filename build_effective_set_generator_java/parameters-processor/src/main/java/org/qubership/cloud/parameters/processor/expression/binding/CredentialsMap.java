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

package org.qubership.cloud.parameters.processor.expression.binding;

import org.qubership.cloud.devops.commons.Injector;
import org.qubership.cloud.devops.commons.exceptions.UnsupportedCredentialsTypeException;
import org.qubership.cloud.devops.commons.pojo.credentials.model.Credential;
import org.qubership.cloud.devops.commons.pojo.credentials.model.SecretCredentials;
import org.qubership.cloud.devops.commons.pojo.credentials.model.StringCredentials;
import org.qubership.cloud.devops.commons.pojo.credentials.model.UsernamePasswordCredentials;
import org.qubership.cloud.devops.commons.pojo.credentials.model.VaultAppRoleCredentials;
import org.qubership.cloud.devops.commons.utils.CredentialUtils;
import org.qubership.cloud.devops.commons.utils.Parameter;

import java.util.HashMap;
import java.util.Map;

public class CredentialsMap extends DynamicMap {

    public CredentialsMap(Binding binding) {
        super(null, binding);
    }

    @Override
    public Map<String, Parameter> getMap(String key) {
        Credential credentials = Injector.getInstance().getDi().get(CredentialUtils.class).getCredentialsById(key);
        if (credentials == null) {
            return null;
        }
        Map<String, Parameter> map = new HashMap<>();
        if (credentials instanceof StringCredentials) {
            StringCredentials stringCredentials = (StringCredentials) credentials;
            map.put("secret", Parameter.builder()
                    .value(stringCredentials.getSecret())
                    .secured(true)
                    .build());
        } else if (credentials instanceof UsernamePasswordCredentials) {
            UsernamePasswordCredentials usernamePasswordCredentials = (UsernamePasswordCredentials) credentials;
            map.put("username", Parameter.builder()
                    .value(usernamePasswordCredentials.getUsername())
                    .secured(true)
                    .build());
            map.put("password", Parameter.builder()
                    .value(usernamePasswordCredentials.getPassword().replaceAll("(?<!\\\\)\\$", "\\\\\\$"))
                    .secured(true)
                    .build());
        } else if (credentials instanceof VaultAppRoleCredentials) {
            VaultAppRoleCredentials vaultAppRoleCredentials = (VaultAppRoleCredentials) credentials;
            map.put("roleId", Parameter.builder()
                    .value(vaultAppRoleCredentials.getRoleId())
                    .secured(true)
                    .build());
            map.put("secretId", Parameter.builder()
                    .value(vaultAppRoleCredentials.getSecretId())
                    .secured(true)
                    .build());
            map.put("path", Parameter.builder()
                    .value(vaultAppRoleCredentials.getPath())
                    .secured(true)
                    .build());
            map.put("namespace", Parameter.builder()
                    .value(vaultAppRoleCredentials.getNamespace())
                    .secured(true)
                    .build());
        } else if (credentials instanceof SecretCredentials) {
            SecretCredentials secretCredentials = (SecretCredentials) credentials;
            map.put("secret", Parameter.builder()
                    .value(secretCredentials.getSecret())
                    .secured(true)
                    .build());
        } else {
            throw new UnsupportedCredentialsTypeException("Unsupported credentials type");
        }
        maps.put(key, map);
        return map;
    }
}
