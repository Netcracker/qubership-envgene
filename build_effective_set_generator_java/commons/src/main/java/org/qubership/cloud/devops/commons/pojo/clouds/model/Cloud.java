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

package org.qubership.cloud.devops.commons.pojo.clouds.model;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;
import lombok.extern.jackson.Jacksonized;
import org.qubership.cloud.devops.commons.pojo.applications.model.ApplicationParams;
import org.qubership.cloud.devops.commons.pojo.profile.model.Profile;
import org.qubership.cloud.devops.commons.pojo.tenants.model.Tenant;

import java.io.Serializable;
import java.util.*;


@Data
@Builder
@Jacksonized
@NoArgsConstructor
@AllArgsConstructor
public final class Cloud implements Serializable{

    private static final long serialVersionUID = -9184913085904794596L;

    private String name;
    private Tenant tenant;
    private String cloudApiUrl;
    private String cloudUrlPrv;
    private String cloudUrlPub;
    private String cloudApiPort;
    private String cloudDashboardUrl;
    @Builder.Default
    private List<String> labels = new ArrayList<>();
    private String defCred;
    private String clProtocol;
    private boolean serverSideMerge;
    @Builder.Default
    private String dbMode = "db";
    @Builder.Default
    private Map<String, String> cloudParams = new HashMap<>();
    @Builder.Default
    private Map<String, String> e2eParams = new HashMap<>();
    private boolean mergeCloudAndE2EParameters;
    @Builder.Default
    private Set<DBaaS> dbaasCfg = new HashSet<>();
    private Set<DB> db;
    @Builder.Default
    private Set<Map<String, String>> nameSpaces = new HashSet<>();
    private List<ApplicationParams> applicationParams;
    @Builder.Default
    private MaaS maas = MaaS.builder().build();
    @Builder.Default
    private Consul consul = Consul.builder().build();
    @Builder.Default
    private Vault vault = Vault.builder().build();
    private Profile profile;
    private String baseline;
    @Builder.Default
    private Map<String, String> configServerParams = new HashMap<>();
    @Builder.Default
    private List<String> deploymentParameterSets = new ArrayList<>();
    @Builder.Default
    private List<String> e2eParameterSets = new ArrayList<>();
    @Builder.Default
    private List<String> technicalParameterSets = new ArrayList<>();
    private boolean productionMode = false;
    private String supportedBy;

    public Cloud(Tenant tenant, String name) {
        this.tenant = tenant;
        this.name = name;
    }
}
