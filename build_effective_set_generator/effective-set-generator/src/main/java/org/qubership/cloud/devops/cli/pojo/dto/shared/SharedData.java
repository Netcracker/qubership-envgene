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

package org.qubership.cloud.devops.cli.pojo.dto.shared;


import jakarta.enterprise.context.ApplicationScoped;
import lombok.Getter;
import lombok.Setter;

import java.util.List;
import java.util.Optional;

@Getter
@Setter
@ApplicationScoped
public class SharedData {

    private String envId;

    private String envsPath;

    private Optional<String> sbomsPath;

    private Optional<String> sdPath;

    private Optional<String> registryPath;

    private String outputDir;

    private EffectiveSetVersion effectiveSetVersion;

    private List<String> pcsspPaths;

    private String deploymentSessionId;

    private boolean appChartValidation;

    private boolean enableTraceability;

}
