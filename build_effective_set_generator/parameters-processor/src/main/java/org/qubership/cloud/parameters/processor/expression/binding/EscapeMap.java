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

import org.qubership.cloud.devops.commons.utils.Parameter;

import java.util.*;
import java.util.stream.Collectors;

public class EscapeMap extends LinkedHashMap<String, Parameter> {

    private final Binding binding;
    private final String origin;

    public EscapeMap(Map<String, ?> map, Binding binding, String origin) {
        super(map == null ? new HashMap<>() : map.entrySet().stream()
                .map(entry -> new AbstractMap.SimpleEntry<>(entry.getKey(), new Parameter(entry.getValue(), origin, false)))
                .collect(Collectors.toMap(AbstractMap.SimpleEntry<String, Parameter>::getKey, AbstractMap.SimpleEntry<String, Parameter>::getValue)));
        this.binding = binding;
        this.origin = origin;
    }

    @Override
    public Parameter get(Object key) {
        Parameter param = super.get(key);
        if (param == null) {
            return Parameter.NULL;
        }
        if (!param.isParsed() && param.getValue() instanceof String) {
            param.setValue(binding.getParser().processParam((String) param.getValue()));
            param.setParsed(true);
        }
        return param;
    }

    @Override
    public Set<Map.Entry<String, Parameter>> entrySet() {
        Set<Map.Entry<String, Parameter>> entrySet = new HashSet<>();
        for (Map.Entry<String, Parameter> entry : super.entrySet()) {
            entry.setValue(get(entry.getKey()));
            entrySet.add(entry);
        }
        return entrySet;
    }

    public Parameter put(String key, Map<?, ?> map) {
        return super.put(key, new Parameter(map, origin, false));
    }

    public Parameter put(String key, String string) {
        return super.put(key, new Parameter(string, origin, false));
    }

    public Parameter putIfAbsent(String key, String string) {
        return super.putIfAbsent(key, new Parameter(string, origin, false));
    }

    public void putAllStrings(Map<? extends String, ? extends String> m, String origin) {
        super.putAll(m.entrySet().stream()
                .map(entry -> new AbstractMap.SimpleEntry<String, Parameter>(entry.getKey(), new Parameter(entry.getValue(), origin, false)))
                .collect(Collectors.toMap(AbstractMap.SimpleEntry<String, Parameter>::getKey, AbstractMap.SimpleEntry<String, Parameter>::getValue)));
    }

    public void putAllStringsIfAbsent(Map<? extends String, ? extends String> m, String origin) {
        m.entrySet().stream()
                .map(entry -> new AbstractMap.SimpleEntry<String, Parameter>(entry.getKey(), new Parameter(entry.getValue(), origin, false)))
                .forEach(entry -> super.putIfAbsent(entry.getKey(), entry.getValue()));
    }
}

