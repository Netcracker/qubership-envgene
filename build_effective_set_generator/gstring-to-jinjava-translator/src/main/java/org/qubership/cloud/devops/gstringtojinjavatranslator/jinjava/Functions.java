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

package org.qubership.cloud.devops.gstringtojinjavatranslator.jinjava;

import com.hubspot.jinjava.doc.annotations.JinjavaDoc;
import com.hubspot.jinjava.doc.annotations.JinjavaSnippet;
import com.hubspot.jinjava.interpret.JinjavaInterpreter;
import com.hubspot.jinjava.lib.fn.ELFunctionDefinition;

public class Functions {
    private Functions() {}
    @JinjavaDoc(
            value = "Generates random double number.",
            snippets = {
                    @JinjavaSnippet(code = "{{ random() }}"),
            }
    )

    private static double random() {
        return JinjavaInterpreter.getCurrent().getRandom().nextDouble();
    }

    public static ELFunctionDefinition randomFunction() {
        return new ELFunctionDefinition(
                "",
                "random",
                Functions.class,
                "random"
        );
    }
}
