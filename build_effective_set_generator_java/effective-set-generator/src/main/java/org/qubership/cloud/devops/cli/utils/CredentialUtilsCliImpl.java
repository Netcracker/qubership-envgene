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

package org.qubership.cloud.devops.cli.utils;

import io.quarkus.arc.Unremovable;
import org.qubership.cloud.devops.cli.pojo.dto.input.InputData;
import org.qubership.cloud.devops.commons.pojo.credentials.dto.*;
import org.qubership.cloud.devops.commons.pojo.credentials.model.*;
import org.qubership.cloud.devops.commons.utils.CredentialUtils;
import jakarta.enterprise.context.ApplicationScoped;
import jakarta.inject.Inject;

import java.util.Map;

@ApplicationScoped
@Unremovable
public class CredentialUtilsCliImpl implements CredentialUtils {

    public static final String AWS_CODE_ARTIFACT_CREDENTIALS_TYPE = "AWSCodeArtifactCredentials";

    private final InputData inputData;


    @Inject
    public CredentialUtilsCliImpl(InputData inputData) {
        this.inputData = inputData;
    }

    @Override
    public Credential getCredentialsById(String id) {
        Map<String, CredentialDTO> credMap = getCredsFromYaml();
        CredentialDTO credentialDTO = credMap.get(id);
        if (credentialDTO == null) {
            return null;
        }
        if (credentialDTO.getData() instanceof UsernamePasswordCredentialsDTO) {
            UsernamePasswordCredentialsDTO usernamePwdDTO = (UsernamePasswordCredentialsDTO)credentialDTO.getData();
            return new UsernamePasswordCredentials(usernamePwdDTO.getUsername(), usernamePwdDTO.getPassword());
        } else if (credentialDTO.getData() instanceof SecretCredentialsDTO) {
            SecretCredentialsDTO secretCredDTO = (SecretCredentialsDTO)credentialDTO.getData();
            return new StringCredentials(secretCredDTO.getSecret());
        } else if  (credentialDTO.getData() instanceof VaultAppRoleCredentialsDTO) {
            VaultAppRoleCredentialsDTO vaultCredDto = (VaultAppRoleCredentialsDTO)credentialDTO.getData();
            return new VaultAppRoleCredentials(vaultCredDto.getRoleId(),vaultCredDto.getSecretId(),
                    vaultCredDto.getPath(), vaultCredDto.getNamespace());
        } else if  (credentialDTO.getData() instanceof SecretFileCredentialsDTO) {
            SecretFileCredentialsDTO secretFileDto = (SecretFileCredentialsDTO)credentialDTO.getData();
            return new SecretCredentials(secretFileDto.getSecretFile());
        } else if (AWS_CODE_ARTIFACT_CREDENTIALS_TYPE.equals(credentialDTO.getData().getClass().getSimpleName())) {
            UsernamePasswordCredentialsDTO passwordCredentials = ((UsernamePasswordCredentialsDTO) credentialDTO.getData());
            String password = passwordCredentials.getPassword();
            return new UsernamePasswordCredentials("AWS", password);
        }
        return null;
    }

    private Map<String, CredentialDTO> getCredsFromYaml() {
        return inputData.getCredentialDTOMap();
    }

}
