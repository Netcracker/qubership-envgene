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

import org.qubership.cloud.devops.commons.Injector;
import org.qubership.cloud.devops.commons.pojo.parameterset.ParameterSet;
import org.qubership.cloud.devops.commons.utils.Parameter;

import java.io.Serializable;
import java.util.Collection;
import java.util.HashMap;
import java.util.Map;
import java.util.Set;

public abstract class DynamicMap implements Map<String, Parameter>, Serializable {

    protected final Binding binding;
    private final String defaultMap;
    public Map<String, Map<String, Parameter>> maps = new HashMap<>();


    DynamicMap(String defaultMap, Binding binding) {
        this.defaultMap = defaultMap;
        this.binding = binding;
    }

    public abstract Map<String, Parameter> getMap(String key);


    public DynamicMap init() {
        if (defaultMap != null) {
            Map<String, Parameter> map = getMap(defaultMap);
            if (map == null) {
                maps.put(defaultMap, new HashMap<>());
            } else {
                maps.put(defaultMap, map);
            }
        }
        return this;
    }

    @Override
    public Parameter get(Object key) {
        Parameter result = null;
        if (defaultMap != null) {
            result = maps.get(defaultMap).get(key);
        }
        if (result == null) {
            result = new Parameter(getMap(key.toString()));
        }
        return result;
    }

    @Override
    public String toString() {
        if (defaultMap != null) {
            Map map = maps.get(defaultMap);
            if (map != null) {
                return map.toString();
            }
        }
        return "null";
    }

    @Override
    public int size() {
        return maps.get(defaultMap) != null ? maps.get(defaultMap).size() : 0;
    }

    @Override
    public boolean isEmpty() {
        return maps.get(defaultMap) == null || maps.get(defaultMap).isEmpty();
    }

    @Override
    public boolean containsKey(Object key) {
        if (maps.get(defaultMap) == null) {
            return false;
        }
        boolean result = maps.get(defaultMap).containsKey(key);
        if (!result) {
            result = getMap(key.toString()) != null;
        }
        return result;
    }

    @Override
    public boolean containsValue(Object value) {
        throw new UnsupportedOperationException("Not supported.");
    }

    @Override
    public Parameter put(String key, Parameter value) {
        Parameter result = null;
        if (defaultMap != null) {
            result = maps.get(defaultMap).put(key, value);
        }
        return result;
    }

    @Override
    public Parameter remove(Object key) {
        throw new UnsupportedOperationException("Not supported.");
    }

    @Override
    public void putAll(Map<? extends String, ? extends Parameter> m) {
        if (maps.get(defaultMap) != null) {
            maps.get(defaultMap).putAll(m);
        }
    }

    @Override
    public void clear() {
        if (maps.get(defaultMap) != null) {
            maps.get(defaultMap).clear();
        }
    }

    @Override
    public Set<String> keySet() {
        throw new UnsupportedOperationException("Not supported.");
    }

    @Override
    public Collection<Parameter> values() {
        throw new UnsupportedOperationException("Not supported.");
    }

    @Override
    public Set<Entry<String, Parameter>> entrySet() {
        Map<String, Parameter> map = maps.get(defaultMap);
        return map == null ? new HashMap().entrySet() : map.entrySet();
    }

    protected void processApplicationSet(String tenant, String setName, String application, String origin, EscapeMap applicationMap) {
        ParameterSet set = Injector.getInstance().getParameterSetService().getParameterSet(tenant, setName);
        if (set != null && application != null) {
            set.getApplications().stream()
                    .filter(app -> app.getAppName().equals(application))
                    .findFirst()
                    .ifPresent(appSet ->
                            applicationMap.putAllStringsIfAbsent(appSet.getParameters(), origin));
        }
    }

    protected void processSet(String tenant, String setName, String origin, EscapeMap map) {
        ParameterSet set = Injector.getInstance().getParameterSetService().getParameterSet(tenant, setName);
        if (set != null) {
            map.putAllStringsIfAbsent(set.getParameters(), origin);
        }
    }
}
