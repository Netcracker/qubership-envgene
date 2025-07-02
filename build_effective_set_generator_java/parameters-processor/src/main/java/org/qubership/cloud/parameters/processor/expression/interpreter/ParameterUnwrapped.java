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

package org.qubership.cloud.parameters.processor.expression.interpreter;

import org.qubership.cloud.devops.commons.utils.Parameter;

import com.hubspot.jinjava.el.ObjectUnwrapper;
import com.hubspot.jinjava.interpret.LazyExpression;

import java.util.Optional;

public class ParameterUnwrapped implements ObjectUnwrapper {
    @Override
    public Object unwrapObject(Object o) {
        if (o instanceof Parameter) {
            if (((Parameter) o).getValue() instanceof String) {
                o = o.toString();
            } else {
                o = ((Parameter) o).getValue();
            }
        }

        if (o instanceof LazyExpression) {
            o = ((LazyExpression) o).get();
        }

        if (o instanceof Optional) {
            Optional<?> optValue = (Optional<?>) o;
            if (optValue.isEmpty()) {
                return null;
            }

            o = optValue.get();
        }

        return o;
    }
}
