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

package org.qubership.cloud.parameters.processor;

import org.qubership.cloud.devops.commons.utils.Parameter;
import org.qubership.cloud.parameters.processor.expression.binding.DynamicMap;
import org.qubership.cloud.parameters.processor.expression.binding.EscapeMap;

import java.util.Collection;
import java.util.HashMap;
import java.util.Map;

public class MergeMap extends HashMap<String, Parameter> {

    private Map<String, Object> merge(Map<String, Object> target, Map<String, Object> source) {
        source.forEach((key, src) -> {
            Object res = merge(target.get(key), src);
            if (!((res instanceof Parameter &&
                    (((Parameter) res).getValue() instanceof EscapeMap || ((Parameter) res).getValue() instanceof DynamicMap)) ||
                    res instanceof EscapeMap || res instanceof DynamicMap)
            ) {
                target.put(key, res);
                }
        });
        return target;
    }

    private Collection<Object> merge(Collection<Object> target, Collection<Object> source) {
        source.stream()
                .filter(item -> !(item instanceof Parameter && target.contains(((Parameter) item).getValue()) || target.contains(item)))
                .forEach(target::add);
        return target;
    }

    private Object merge(Object target, Object source) {
        if (target instanceof Map && source instanceof Map) {
            return merge((Map) target, (Map) source);
        }
        if (target instanceof Collection && source instanceof Collection) {
            return merge((Collection) target, (Collection) source);
        }
        if (target instanceof Parameter && source instanceof Parameter) {
            ((Parameter) source).setValue(merge(((Parameter)target).getValue(), ((Parameter)source).getValue()));
            return source;
        }
        return source;
    }
    
    @Override
    public void putAll(Map<? extends String, ? extends Parameter> override) {
        merge(this, override);
    }

}
