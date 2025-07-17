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

package org.qubership.cloud.devops.commons.pojo.clouds.dto;


import com.fasterxml.jackson.annotation.JsonPropertyOrder;
import com.fasterxml.jackson.databind.annotation.JsonDeserialize;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Pattern;
import lombok.Builder;
import lombok.Data;
import lombok.extern.jackson.Jacksonized;
import org.qubership.cloud.devops.commons.pojo.applications.dto.ApplicationLinkDTO;
import org.qubership.cloud.devops.commons.pojo.profile.dto.ProfileDto;
import org.qubership.cloud.devops.commons.utils.convert.CustomDeserializer;

import javax.annotation.Nonnull;
import java.util.List;
import java.util.Map;

@Nonnull
@JsonPropertyOrder
@Data
@Builder(toBuilder = true)
@Jacksonized
public class CloudDTO {
    @NotBlank(message = "cloud name must not be blank.")
    @Pattern( regexp = "^[a-zA-Z0-9_]*$", message = "cloud name must match the regex: ^[a-zA-Z0-9_]*$")
    private final String name;
    private final String apiUrl;
    private final String apiPort;
    private final String privateUrl;
    private final String publicUrl;
    private final String dashboardUrl;
    private final List<String> labels;
    private final String defaultCredentialsId;
    private final String protocol;
    @JsonDeserialize(using = CustomDeserializer.class)
    private final Map<String, String> deployParameters;
    @JsonDeserialize(using = CustomDeserializer.class)
    private final Map<String, String> e2eParameters;
    @JsonDeserialize(using = CustomDeserializer.class)
    private final Map<String, String> technicalConfigurationParameters;
    private final List<String> deployParameterSets;
    private final List<String> e2eParameterSets;
    private final List<String> technicalConfigurationParameterSets;
    private final boolean mergeDeployParametersAndE2EParameters;
    private final String dbMode;
    private final List<DatabaseDTO> databases;
    private final MaaSConfigDTO maasConfig;
    private final VaultConfigDTO vaultConfig;
    private final ConsulConfigDTO consulConfig;
    private final List<DbaaSConfigDTO> dbaasConfigs;
    private final boolean productionMode;
    private final String supportedBy;
    private final ProfileDto profile;
    private final String tenantName;
    private final List<ApplicationLinkDTO> applications;
}
