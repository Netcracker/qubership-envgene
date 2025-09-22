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

package org.qubership.cloud.devops.commons.pojo.tenants.dto;

import com.fasterxml.jackson.annotation.JsonPropertyOrder;
import com.fasterxml.jackson.databind.annotation.JsonDeserialize;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Pattern;
import lombok.Builder;
import lombok.Data;
import lombok.extern.jackson.Jacksonized;
import org.qubership.cloud.devops.commons.utils.convert.CustomDeserializer;

import javax.annotation.Nonnull;
import java.util.List;
import java.util.Map;


@Data
@Builder
@JsonPropertyOrder
@Jacksonized
@Nonnull
public class TenantDTO {
    @Pattern( regexp = "^[a-zA-Z0-9_-]*$", message = "Tenant name must match the regex: ^[a-zA-Z0-9_-]*$")
    @NotBlank(message = "Tenant name must not be blank.")
    private final String name;
    private final String registryName;
    private final String description;
    private final String owners;
    @JsonDeserialize(using = CustomDeserializer.class)
    private final Map<String, Object> deployParameters;
    private final GlobalE2EParametersDTO globalE2EParameters;
    private final String gitRepository;
    private final String defaultBranch;
    private final String credential;
    private final List<String> labels;
    private final List<String> deploymentParameterSets;
    private final List<String> e2eParameterSets;
    private final List<String> technicalParameterSets;
    @JsonDeserialize(using = CustomDeserializer.class)
    private final Map<String, Object> technicalConfigurationParameters;
}
