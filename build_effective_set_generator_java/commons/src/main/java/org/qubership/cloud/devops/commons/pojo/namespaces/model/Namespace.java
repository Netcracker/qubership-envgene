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

package org.qubership.cloud.devops.commons.pojo.namespaces.model;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;
import lombok.extern.jackson.Jacksonized;
import org.qubership.cloud.devops.commons.pojo.applications.model.ApplicationParams;
import org.qubership.cloud.devops.commons.pojo.clouds.model.Cloud;
import org.qubership.cloud.devops.commons.pojo.profile.model.Profile;

import java.io.Serializable;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.Map;

@Data
@Builder(toBuilder = true)
@Jacksonized
@NoArgsConstructor
@AllArgsConstructor
public final class Namespace implements Serializable {

    private static final long serialVersionUID = -850178630161720111L;

    private String name;
    @Builder.Default
    private List<String> labels = Collections.emptyList();
    private Cloud cloud;
    private String credId;
    @Builder.Default
    private List<ApplicationParams> applications = Collections.emptyList();
    @Builder.Default
    private Map<String, String> customParameters = Collections.emptyMap();
    @Builder.Default
    private Map<String, String> e2eParameters = Collections.emptyMap();
    private boolean mergeCustomPramsAndE2EParams;
    private boolean cleanInstallApprovalRequired;
    private boolean serverSideMerge;
    @Builder.Default
    private List<String> parameterSets = new ArrayList<>();
    private Map<String, String> configServerParameters;
    private List<String> e2eParameterSets;
    private List<String> technicalParameterSets;
    private boolean deprecatedDeployParametersNotAllowed;
    private String compositeType;
    private String compositeBaseline;
    private Profile profile;
    private String baseline;

    public Map<String, String> getCustomParameters() {
        return customParameters != null ? customParameters : Collections.emptyMap();
    }
}
