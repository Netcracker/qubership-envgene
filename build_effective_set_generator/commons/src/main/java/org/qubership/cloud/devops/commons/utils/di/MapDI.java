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

package org.qubership.cloud.devops.commons.utils.di;

import java.util.Arrays;
import java.util.HashSet;
import java.util.Set;

public class MapDI implements DIWrapper {
    CopyOnWriteMap<Class<?>, Object> diInstance = new CopyOnWriteMap<>();

    @Override
    @SuppressWarnings("unchecked")
    public <T> T get(Class<T> clazz) {
        return (T) diInstance.get(clazz);
    }

    @Override
    public <T> void add(T object) {
        Set<Class<?>> classes = new HashSet<>(Arrays.asList(object.getClass().getInterfaces()));
        diInstance.put(object.getClass(), object);
        classes.forEach(t -> diInstance.put(t, object));
    }

    public <T> void bind(Class<?> as, T object) {
        diInstance.put(as, object);
    }

    public <T> MapDI withBean(T bean) {
        add(bean);
        return this;
    }
}
