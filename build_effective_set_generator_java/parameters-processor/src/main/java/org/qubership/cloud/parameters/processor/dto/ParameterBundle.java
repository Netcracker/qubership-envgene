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

package org.qubership.cloud.parameters.processor.dto;

import lombok.Builder;
import lombok.Data;

import java.util.Map;

@Builder
@Data
public class ParameterBundle {
    Map<String, Object> securedDeployParams;
    Map<String, Object> deployParams;
    Map<String, Object> securedConfigParams;
    Map<String, Object> configServerParams;
    Map<String, Object> securedE2eParams;
    Map<String, Object> e2eParams;
    Map<String, Object> deployDescParams;
    Map<String, Object> perServiceParams;
    Map<String, Object> collisionDeployParameters;
    Map<String, Object> collisionSecureParameters;
    boolean processPerServiceParams;
    String appChartName;
}
