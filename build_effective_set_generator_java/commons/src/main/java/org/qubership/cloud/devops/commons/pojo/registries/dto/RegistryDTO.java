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

package org.qubership.cloud.devops.commons.pojo.registries.dto;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonPropertyOrder;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Pattern;
import lombok.Builder;
import lombok.Data;
import lombok.extern.jackson.Jacksonized;

import java.io.Serializable;

@Data
@Builder
@Jacksonized
@JsonPropertyOrder
@JsonIgnoreProperties(ignoreUnknown = true)
public class RegistryDTO implements Serializable {

    private static final long serialVersionUID = -8691792613671479529L;
    private final String name;
    private final String credentialsId;
    private final String username;
    private final String password;
    private final String releaseRepository;
    private final String snapshotRepository;
    private final String stagingRepository;
    private final String proxyRepository;
    private final String releaseTemplateRepository;
    private final String snapshotTemplateRepository;
    private final String stagingTemplateRepository;
    private final MavenDTO mavenConfig;
    private final DockerDTO dockerConfig;
    private final GoDTO goConfig;
    private final RawDTO rawConfig;
    private final NpmDTO npmConfig;
    private final HelmDTO helmConfig;
    private final HelmAppDTO helmAppConfig;

}