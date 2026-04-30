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

package org.qubership.cloud.devops.commons.pojo.applications.dto;

import com.fasterxml.jackson.annotation.JsonPropertyOrder;
import com.fasterxml.jackson.databind.annotation.JsonDeserialize;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotEmpty;
import jakarta.validation.constraints.Pattern;
import lombok.Builder;
import lombok.Data;
import lombok.extern.jackson.Jacksonized;
import org.qubership.cloud.devops.commons.utils.convert.CustomDeserializer;

import javax.annotation.Nonnull;
import java.util.Map;

@Nonnull
@JsonPropertyOrder
@Data
@Builder
@Jacksonized
public class ApplicationDTO {
    @NotBlank(message = "Application name must not be blank.")
    @Pattern( regexp = "^[a-zA-Z0-9._-]*$", message = "Application name must match the regex: ^[a-zA-Z0-9._-]*$")
    private final String name;
    private final String registryName;
    @NotEmpty
    private final String artifactId;
    @NotEmpty
    private final String groupId;
    private final boolean supportParallelDeploy;
    @JsonDeserialize(using = CustomDeserializer.class)
    private final Map<String, Object> deployParameters;
    @JsonDeserialize(using = CustomDeserializer.class)
    private final Map<String, Object> technicalConfigurationParameters;
    private final boolean solutionDescriptor;
}
