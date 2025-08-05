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
import com.hubspot.jinjava.doc.annotations.JinjavaParam;
import com.hubspot.jinjava.doc.annotations.JinjavaSnippet;
import com.hubspot.jinjava.interpret.JinjavaInterpreter;
import com.hubspot.jinjava.interpret.TemplateSyntaxException;
import com.hubspot.jinjava.lib.filter.Filter;

import java.util.Collection;
import java.util.Objects;
import java.util.Optional;

@JinjavaDoc(
        value = "Takes prefix from context variable NAMESPACE depending on list of values." +
                "Acts as alternative to " +
                "${[list..].findResult{ " +
                "if (NAMESPACE.contains(it)) NAMESPACE.substring(0, NAMESPACE.indexOf(it)) " +
                "} ?: ''} in GStringTemplate.",
        input = @JinjavaParam(value = "list", desc = "the list of values", required = true),
        params = {
                @JinjavaParam(
                        value = "default",
                        desc = "Default string if there's no prefix",
                        required = true
                )
        },
        snippets = {
                @JinjavaSnippet(
                        code = "<<['bss-pim','bss','nrm','ops-dpt','ops-dpc','opt-ssm'] | envPrefix('')>>"
                )
        }
)
public class EnvPrefixFilter implements Filter {
    @Override
    public Object filter(Object object, JinjavaInterpreter interpreter, String... args) {
        if (args.length < 1) {
            throw new TemplateSyntaxException(
                    interpreter,
                    getName(),
                    "requires 1 argument (default string if there's no prefix)"
            );
        }

        if (object == null) {
            return null;
        }

        if (object instanceof Collection) {
            Collection<String> collection = (Collection<String>) object;

            String namespace = (String) Optional.ofNullable(interpreter.resolveELExpression("NAMESPACE", -1)).orElse("");
            return collection.stream().map(it -> {
                        if (namespace.contains(it)) {
                            return namespace.substring(0, namespace.indexOf(it));
                        }
                        return null;})
                    .filter(Objects::nonNull)
                    .findFirst().orElse(Objects.toString(args[0], ""));
        }
        return null;
    }

    @Override
    public String getName() {
        return "envPrefix";
    }
}
