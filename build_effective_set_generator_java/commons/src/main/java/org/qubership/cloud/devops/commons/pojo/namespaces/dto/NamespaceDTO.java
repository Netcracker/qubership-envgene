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

package org.qubership.cloud.devops.commons.pojo.namespaces.dto;

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
public class NamespaceDTO {
    @NotBlank(message = "Namespace name must not be blank.")
    @Pattern( regexp = "^[a-z0-9]([-a-z0-9]*[a-z0-9])?$", message = "Namespace name must match the regex: ^[a-z0-9]([-a-z0-9]*[a-z0-9])?$")
    private final String name;
    private final String credentialsId;
    private final boolean isServerSideMerge;
    private final List<String> labels;
    private final boolean cleanInstallApprovalRequired;
    private final boolean mergeDeployParametersAndE2EParameters;
    @JsonDeserialize(using = CustomDeserializer.class)
    private final Map<String, Object> deployParameters;
    @JsonDeserialize(using = CustomDeserializer.class)
    private final Map<String, Object> e2eParameters;
    @JsonDeserialize(using = CustomDeserializer.class)
    private final Map<String, Object> technicalConfigurationParameters;
    private final List<String> deployParameterSets;
    private final List<String> e2eParameterSets;
    private final List<String> technicalConfigurationParameterSets;
    private final ProfileDto profile;
    private final String tenantName;
    private final String cloudName;
    private final List<ApplicationLinkDTO> applications;
}