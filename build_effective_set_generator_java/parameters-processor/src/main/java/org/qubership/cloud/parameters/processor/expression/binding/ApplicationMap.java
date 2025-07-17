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
import org.qubership.cloud.devops.commons.Injector;
import org.qubership.cloud.devops.commons.pojo.applications.model.Application;
import org.qubership.cloud.devops.commons.service.interfaces.ApplicationService;
import org.qubership.cloud.devops.commons.utils.Parameter;

import java.util.Map;

public class ApplicationMap extends DynamicMap {

    public ApplicationMap(String defaultApp, Binding binding) {
        super(defaultApp, binding);
    }

    @Override
    public Map<String, Parameter> getMap(String key) {

        Application config = Injector.getInstance().getDi().get(ApplicationService.class).getByName(key);
        if (config != null) {
            Map<String, Parameter> map = new EscapeMap(config.getParams(), binding, String.format(ParametersConstants.APP_ORIGIN, key));
            checkEscape(map);
            maps.put(key, map);
            return map;
        }
        return null;
    }

}
