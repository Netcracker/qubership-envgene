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

package org.qubership.cloud.devops.commons.pojo.registries.model;

import com.fasterxml.jackson.annotation.JsonIgnore;
import lombok.*;
import lombok.extern.jackson.Jacksonized;
import org.qubership.cloud.devops.commons.pojo.applications.model.Application;
import org.qubership.cloud.devops.commons.pojo.tenants.model.Tenant;

import java.io.Serializable;
import java.util.HashSet;
import java.util.Set;

@Data
@Builder
@Jacksonized
@NoArgsConstructor
@AllArgsConstructor
public class Registry implements Serializable {

    private static final long serialVersionUID = -6531053074245709715L;

    @ToString.Exclude
    @EqualsAndHashCode.Exclude
    private final Set<Tenant> tenants = new HashSet<>();
    @JsonIgnore
    @ToString.Exclude
    @EqualsAndHashCode.Exclude
    private final Set<Application> applications = new HashSet<>();
    private String name;
    private String credentials;
    @Builder.Default
    private Maven mavenCfg = Maven.builder().build();
    @Builder.Default
    private Raw rawCfg = Raw.builder().build();
    @Builder.Default
    private Docker dockerCfg = Docker.builder().build();
    @Builder.Default
    private Go goCfg = Go.builder().build();
    @Builder.Default
    private Npm npmCfg = Npm.builder().build();;
    @Builder.Default
    private Helm helmCfg = Helm.builder().build();
    @Builder.Default
    private HelmApp helmAppCfg = HelmApp.builder().build();

    public Registry(String name) {
        this.name = name;
    }

}
