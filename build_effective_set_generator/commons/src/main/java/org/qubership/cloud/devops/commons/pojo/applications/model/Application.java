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

package org.qubership.cloud.devops.commons.pojo.applications.model;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;
import lombok.extern.jackson.Jacksonized;
import org.qubership.cloud.devops.commons.pojo.registries.model.Registry;
import org.qubership.cloud.devops.commons.pojo.tenants.model.Tenant;

import java.io.Serializable;
import java.util.HashMap;
import java.util.Map;


@Data
@Builder
@Jacksonized
@NoArgsConstructor
@AllArgsConstructor
public class Application implements Serializable {

    private static final long serialVersionUID = 8526061874813081961L;

    private String name;
    private String artifactId;
    private String groupId;
    @Builder.Default
    private Map<String, Object> params = new HashMap<>();
    private Map<String, Object> technicalParams;
    private Registry registry;
    private Tenant tenant;
    private boolean supportParallelDeploy;
    private String config;
    private String baseline;
    private Notification notifications;
    private PublishInfo publishInfo;
    private boolean solutionDescriptor;
    private boolean remoteApp;
    private String rawConfig;
    private String prefix;
}
