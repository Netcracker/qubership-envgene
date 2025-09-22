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

import org.qubership.cloud.parameters.processor.MergeMap;
import org.qubership.cloud.parameters.processor.expression.binding.Binding;
import org.qubership.cloud.parameters.processor.expression.binding.DynamicMap;
import org.qubership.cloud.parameters.processor.expression.binding.EscapeMap;
import org.qubership.cloud.devops.commons.utils.Parameter;

import java.util.AbstractMap;
import java.util.Collections;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

public class PlainLanguage extends AbstractLanguage {

    public PlainLanguage(Binding binding) {
        super(binding);
    }

    @Override
    protected Map<String, Parameter> createMap() {
        return new HashMap<>();
    }

    private Object getValue(Object object) {
        if (object instanceof Parameter) {
            return ((Parameter) object).getValue();
        } else {
            return object;
        }
    }

    private Parameter processValue(Object value) {
        Object val = getValue(value);
        if (val instanceof List) {
            val = processList((List<Parameter>) val);
        } else if (val instanceof Map) {
            val = processMap((Map<String, Parameter>) val);
        }
        Parameter ret = new Parameter(value);
        ret.setValue(val);
        return ret;
    }

    protected Map<String, Parameter> processMap(Map<String, Parameter> map) {
        if (map == null) {
            map = Collections.emptyMap();
        }
        return map.entrySet().stream()
                .filter(x -> getValue(x.getValue()) instanceof String || !(getValue(x.getValue()) instanceof DynamicMap || getValue(x.getValue()) instanceof EscapeMap))
                .collect(Collectors.toMap(Map.Entry::getKey, e -> processValue(e.getValue())));
    }

    private List<Parameter> processList(List<?> list) {
        return list.stream().map(this::processValue).collect(Collectors.toList());
    }

    protected Map<String, Parameter> processMap(String mapName) {
        return processMap(binding.setDefault(mapName));
    }

    private Object convertParameterToObject(Object value) {
        if (value instanceof Parameter) {
            value = ((Parameter) value).getValue();
        }
        if (value instanceof Map) {
            value = convertParameterMapToObject((Map) value);
        } else if (value instanceof List) {
            value = convertParameterListToObject((List) value);
        }
        return value;
    }

    private List<Object> convertParameterListToObject(List<Parameter> list) {
        return list.stream()
                .map(this::convertParameterToObject)
                .collect(Collectors.toList());
    }

    private Map<String, Object> convertParameterMapToObject(Map<String, Parameter> map) {
        return map.entrySet().stream()
                .map(entry -> new AbstractMap.SimpleEntry<>(entry.getKey(), entry.getValue().getValue()))
                .collect(HashMap::new, (m, v) -> m.put(v.getKey(), convertParameterToObject(v.getValue())), HashMap::putAll);
    }

    public Map<String, Parameter> processDeployment() {
        Map<String, Parameter> result = new MergeMap();

        Map<String, Parameter> override = new HashMap<>();
        processNamespaceApp(override);

        //merge only overall cloud and custom params
        result.putAll(override);
        result.putAll(processMap(""));

        return result;
    }


    @Override
    public Map<String, Parameter> processE2E() {
        Map<String, Parameter> result = new HashMap<>();
        processE2E(result);

        return result;
    }

    @Override
    public Map<String, Parameter> processCloudE2E() {
        Map<String, Parameter> result = new HashMap<>();
        processCloudE2E(result);

        return result;
    }

    @Override
    public Map<String, Parameter> processNamespaceApp() {
        Map<String, Parameter> result = new HashMap<>();

        processNamespaceApp(result);
        return processMap(result);
    }

    @Override
    public Map<String, Parameter> processNamespace() {
        Map<String, Parameter> result = new MergeMap();

        processNamespace(result);

        return processMap(result);
    }

    @Override
    public Map<String, Parameter> processConfigServerApp() {
        return processNamespaceAppConfigServer();
    }

    @Override
    public Map<String, Parameter> processNamespaceAppConfigServer() {
        Map<String, Parameter> result = new HashMap<>();

        processNamespaceAppConfigServer(result);
        return processMap(result);
    }
    @Override
    public Map<String, Parameter> processParameters(Map<String, String> parameters) {
        return new HashMap<>();
    }

}
