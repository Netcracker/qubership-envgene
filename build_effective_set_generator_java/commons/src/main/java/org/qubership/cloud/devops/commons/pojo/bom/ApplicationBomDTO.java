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

package org.qubership.cloud.devops.commons.pojo.bom;


import lombok.Builder;
import lombok.Data;

import java.util.Map;

@Data
@Builder
public class ApplicationBomDTO {
    private String name;
    private String version;
    private String artifactId;
    private String groupId;
    private String mavenRepo;
    private String deployerSessionId;
    public String appChartName;
    private Map<String, Map<String, Object>> services;
    private Map<String, Map<String, Object>> configurations;
    private Map<String, Map<String, Object>> frontends;
    private Map<String, Map<String, Object>> smartplugs;
    private Map<String, Map<String, Object>> cdn;
    private Map<String, Map<String, Object>> sampleRepo;
    private Map<String, String> deployParams;

    //deployment-descriptor params
    private Map<String, Map<String, Object>> deployDescriptors;
    private Map<String, Map<String, Object>> commonDeployDescriptors;
    private Map<String, Map<String, Object>> perServiceParams;
}
