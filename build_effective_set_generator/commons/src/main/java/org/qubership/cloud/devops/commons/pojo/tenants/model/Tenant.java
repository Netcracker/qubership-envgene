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

package org.qubership.cloud.devops.commons.pojo.tenants.model;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;
import lombok.extern.jackson.Jacksonized;
import org.qubership.cloud.devops.commons.pojo.registries.model.Registry;

import java.io.Serializable;
import java.util.ArrayList;
import java.util.List;


@Data
@Builder
@Jacksonized
@NoArgsConstructor
@AllArgsConstructor
public class Tenant implements Serializable {
    private static final long serialVersionUID = -726557292867412876L;

    private String name;
    @Builder.Default
    private String description = "";
    @Builder.Default
    private String owners = "";
    @Builder.Default
    private TenantGlobalParameters globalParameters = TenantGlobalParameters.builder().build();
    private Registry registry;
    @Builder.Default
    private String dcrRoot = "";
    @Builder.Default
    private String mvnGroup = "";
    @Builder.Default
    private List<String> deploymentParameterSets = new ArrayList<>();
    @Builder.Default
    private List<String> e2eParameterSets = new ArrayList<>();
    @Builder.Default
    private List<String> technicalParameterSets = new ArrayList<>();
    @Builder.Default
    private String gitRepository = "";
    @Builder.Default
    private String defaultBranch = "";
    @Builder.Default
    private String credential = "";
    @Builder.Default
    private String token = "";
    @Builder.Default
    private List<String> labels = new ArrayList<>();

    public Tenant(String name) {
        this.name = name;
    }

}
