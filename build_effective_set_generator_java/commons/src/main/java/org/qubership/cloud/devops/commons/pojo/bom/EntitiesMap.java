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

import lombok.*;
import java.util.HashMap;
import java.util.Map;


@AllArgsConstructor
@NoArgsConstructor
@Getter
@Setter
public class EntitiesMap {
    public Map<String, Map<String, Object>> serviceMap = new HashMap<>();
    public Map<String, Map<String, Object>> configurationMap = new HashMap<>();
    public Map<String, Map<String, Object>> smartplugMap = new HashMap<>();
    public Map<String, Map<String, Object>> frontEndMap = new HashMap<>();
    public Map<String, Map<String, Object>> cdnMap = new HashMap<>();
    public Map<String, Map<String, Object>> repoMap = new HashMap<>();
}
