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

package org.qubership.cloud.parameters.processor.expression;

import org.qubership.cloud.devops.commons.utils.Parameter;
import org.qubership.cloud.parameters.processor.expression.binding.Binding;
import org.qubership.cloud.parameters.processor.expression.binding.CloudMap;
import org.qubership.cloud.parameters.processor.expression.binding.NamespaceMap;
import org.qubership.cloud.parameters.processor.expression.binding.TenantMap;

import java.util.Map;
import java.util.function.Consumer;

public abstract class AbstractLanguage implements Language {

    protected Binding binding;

    protected AbstractLanguage(Binding binding) {
        this.binding = binding;
    }

    protected abstract Map<String, Parameter> processMap(String mapName);

    protected abstract Map<String, Parameter> processMap(Map<String, Parameter> map);

    protected abstract Map<String, Parameter> createMap();

    private void process(Map<String, Parameter> map, Consumer<Consumer<String>> function) {
        Map<String, Parameter> map2 = createMap();
        function.accept(mapName -> map2.putAll(binding.getDotMap(mapName)));
        binding.putAllCalculated(map2);

        map.putAll(map2);
        function.accept(mapName -> {
                binding.setDefault(mapName);
                Map<String, Parameter> m = this.processMap(map2);
                m.forEach((key, value) -> {
                    if (value.isValid()) {
                        map.put(key, value);
                    }
                });
        });
    }

    protected void processE2E(Map<String, Parameter> map) {
        process(map, function -> {
            if (((TenantMap) binding.getDotMap("tenant")).isMergeE2E()) {
                function.accept("tenant");
            }
            function.accept("tenant.e2e");

            if (((CloudMap) binding.getDotMap("tenant.cloud")).isMergeE2E()) {
                function.accept("tenant.cloud");
            }
            function.accept("tenant.cloud.e2e");

            if (((NamespaceMap) binding.getDotMap("tenant.cloud.namespace")).isMergeE2E()) {
                function.accept("tenant.cloud.namespace");
            }
            function.accept("tenant.cloud.namespace.e2e");
        });
    }

    protected void processCloudE2E(Map<String, Parameter> map) {
        process(map, function -> {
            if (((CloudMap) binding.getDotMap("tenant.cloud")).isMergeE2E()) {
                function.accept("tenant.cloud");
            }
            function.accept("tenant.cloud.e2e");
        });
    }

    protected void processNamespaceApp(Map<String, Parameter> map) {
        process(map, function -> {
            function.accept("tenant");

            function.accept("application");

            function.accept("tenant.cloud");

            function.accept("tenant.cloud.app");

            function.accept("tenant.cloud.namespace");

            function.accept("tenant.cloud.namespace.app");
        });
    }

    protected void processNamespaceAppConfigServer(Map<String, Parameter> map) {
        process(map, (function) -> {
            function.accept("tenant.config-server");

            function.accept("tenant.cloud.config-server");

            function.accept("tenant.cloud.app.config-server");

            function.accept("tenant.cloud.namespace.config-server");

            function.accept("tenant.cloud.namespace.app.config-server");
        });
    }

}
