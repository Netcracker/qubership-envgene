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

import org.snakeyaml.engine.v2.common.Anchor;
import org.snakeyaml.engine.v2.nodes.AnchorNode;
import org.snakeyaml.engine.v2.nodes.Node;

import java.util.Collection;
import java.util.HashMap;
import java.util.Map;
import java.util.Optional;
import java.util.concurrent.atomic.AtomicInteger;

public class YamlAnchorRegistry {

    private final Map<Object, Integer> refCount;
    private final Map<Object, Node> builtNodes = new HashMap<>();
    private final AtomicInteger nextAnchorId = new AtomicInteger(1);

    public YamlAnchorRegistry(Map<Object, Integer> refCount) {
        this.refCount = refCount;
    }

    public Node getAliasNodeIfExists(Object obj) {
        if (!shouldAnchor(obj) || !builtNodes.containsKey(obj)) {
            return null;
        }
        return new AnchorNode(builtNodes.get(obj));
    }

    public void registerAnchorIfNeeded(Object obj, Node node) {
        if (!shouldAnchor(obj)) {
            return;
        }
        builtNodes.put(obj, node);
        node.setAnchor(Optional.of(new Anchor(nextAnchorId())));
    }

    private boolean shouldAnchor(Object obj) {
        if ((obj instanceof Collection<?> c && c.isEmpty()) || (obj instanceof Map<?, ?> m && m.isEmpty())) {
            return false;
        }
        return refCount.getOrDefault(obj, 0) > 1;
    }

    private String nextAnchorId() {
        return String.format("id%03d", nextAnchorId.getAndIncrement());
    }
}
