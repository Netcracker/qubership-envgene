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

package org.qubership.cloud.devops.cli.utils.yaml;

import jakarta.enterprise.context.ApplicationScoped;
import org.qubership.cloud.devops.commons.utils.Parameter;

import java.util.HashMap;
import java.util.List;
import java.util.Map;

@ApplicationScoped
public class YamlReferenceCounter {

    public Map<Object, Integer> countReferences(Object root) {
        Map<Object, Integer> refCount = new HashMap<>();
        countReferencesRecursively(root, refCount);
        return refCount;
    }

    private void countReferencesRecursively(Object obj, Map<Object, Integer> refCount) {
        if (obj == null) {
            return;
        }

        Object value = (obj instanceof Parameter p) ? p.getValue() : obj;
        if (value instanceof Map<?, ?> map) {
            if (incrementAndCheckVisited(map, refCount)) {
                return;
            }
            for (Object v : map.values()) {
                countReferencesRecursively(v, refCount);
            }
        } else if (value instanceof List<?> list) {
            if (incrementAndCheckVisited(list, refCount)) {
                return;
            }
            for (Object item : list) {
                countReferencesRecursively(item, refCount);
            }
        }
    }

    private boolean incrementAndCheckVisited(Object obj, Map<Object, Integer> refCount) {
        int count = refCount.getOrDefault(obj, 0);
        refCount.put(obj, count + 1);
        return count > 0;
    }
}
