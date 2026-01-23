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

package org.qubership.cloud.devops.cli.utils.di;

import io.quarkus.arc.ClientProxy;
import org.qubership.cloud.devops.commons.utils.di.CopyOnWriteMap;
import org.qubership.cloud.devops.commons.utils.di.DIWrapper;
import io.quarkus.arc.Arc;

import java.util.Arrays;
import java.util.HashSet;
import java.util.Set;

public class CliDI implements DIWrapper {
    CopyOnWriteMap<Class<?>, Object> diInstance = new CopyOnWriteMap<>();

    @Override
    @SuppressWarnings("unchecked")
    public <T> T get(Class<T> clazz) {
        T result = (T) diInstance.get(clazz);
        if (result == null)
            return Arc.container().instance(clazz).get();
        return result;
    }

    @Override
    public <T> void add(T object) {
        Set<Class<?>> classes = new HashSet<>(Arrays.asList(object.getClass().getInterfaces()));
        if (object instanceof ClientProxy) {
            classes = new HashSet<>(Arrays.asList(object.getClass().getSuperclass().getInterfaces()));
        }
        diInstance.put(object.getClass(), object);
        classes.forEach(t -> diInstance.put(t, object));
    }

    public <T> CliDI withBean(T bean) {
        add(bean);
        return this;
    }
}
