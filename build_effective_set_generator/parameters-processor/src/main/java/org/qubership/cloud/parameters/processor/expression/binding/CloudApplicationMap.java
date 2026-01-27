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

package org.qubership.cloud.parameters.processor.expression.binding;

import org.qubership.cloud.devops.commons.utils.constant.ParametersConstants;
import org.qubership.cloud.devops.commons.pojo.applications.model.ApplicationParams;
import org.qubership.cloud.devops.commons.pojo.clouds.model.Cloud;
import org.qubership.cloud.devops.commons.utils.Parameter;

import java.util.ArrayDeque;
import java.util.HashMap;
import java.util.Map;

public class CloudApplicationMap extends DynamicMap {

    private final Cloud cloud;

    public CloudApplicationMap(Cloud cloud, String defaultApp, Binding binding) {
        super(defaultApp, binding);
        this.cloud = cloud;
    }

    @Override
    public Map<String, Parameter> getMap(String appName) {
        ApplicationParams applicationParams = cloud.getApplicationParams().stream()
                .filter(app -> app.getAppName().equals(appName))
                .findAny()
                .orElse(null);

        Map<String, Object> appParams = applicationParams != null ? applicationParams.getAppParams() : new HashMap<>();
        Map<String, Object> configServerParams = applicationParams != null ? applicationParams.getConfigServerParams() : new HashMap<>();
        EscapeMap map = new EscapeMap(appParams, binding,
                String.format(ParametersConstants.CLOUD_APP_ORIGIN, cloud.getTenant().getName(), cloud.getName(), appName));
        EscapeMap configServerMap = new EscapeMap(configServerParams, binding,
                String.format(ParametersConstants.CLOUD_APP_CONFIG_SERVER_ORIGIN, cloud.getTenant().getName(), cloud.getName(), appName));

        EscapeMap parameterSetMap = new EscapeMap(null, binding, "");
        map.put("parameterSet", parameterSetMap);
        if (cloud.getDeploymentParameterSets() != null) {
            new ArrayDeque<>(cloud.getDeploymentParameterSets()).descendingIterator().forEachRemaining(set -> {
                String origin = String.format(ParametersConstants.CLOUD_PARAMETER_SET_APP_ORIGIN,
                        cloud.getTenant().getName(), cloud.getName(), set, appName);
                processApplicationSet(cloud.getTenant().getName(), set, appName, origin, parameterSetMap);
            });
        }
        EscapeMap parameterSetConfigServerMap = new EscapeMap(null, binding, "");
        configServerMap.put("parameterSet", parameterSetConfigServerMap);
        if (cloud.getTechnicalParameterSets() != null) {
            new ArrayDeque<>(cloud.getTechnicalParameterSets()).descendingIterator().forEachRemaining(set -> {
                String origin = String.format(ParametersConstants.CLOUD_PARAMETER_SET_APP_ORIGIN,
                        cloud.getTenant().getName(), cloud.getName(), set, appName);
                processApplicationSet(cloud.getTenant().getName(), set, appName, origin, configServerMap);
            });
        }

        checkEscape(map);
        checkEscape(parameterSetMap);
        checkEscape(configServerMap);
        checkEscape(parameterSetConfigServerMap);
        map.put("config-server", configServerMap);
        maps.put(appName, map);
        return map;
    }
}
