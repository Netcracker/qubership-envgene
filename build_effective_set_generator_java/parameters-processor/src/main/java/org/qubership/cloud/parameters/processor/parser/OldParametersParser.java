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

package org.qubership.cloud.parameters.processor.parser;

import org.qubership.cloud.devops.commons.utils.constant.ParametersConstants;
import org.qubership.cloud.devops.commons.utils.Parameter;

import groovy.json.JsonSlurperClassic;

import java.io.Serializable;
import java.util.HashMap;
import java.util.Map;

public class OldParametersParser implements ParametersParser, Serializable {

    @Override
    public Object processParam(String param) {
        // auto escape symbols \ and " for CRM guys
        String valueOfParam = param.replaceAll("(\"|\\\\)", "\\\\$0").trim();
        if (valueOfParam.startsWith("\'{")) {
            String jsString = valueOfParam.substring(1, valueOfParam.length() - 1);
            return new JsonSlurperClassic().parseText(jsString.replaceAll("\\\\", ""));
        } else {
            return valueOfParam;
        }
    }

    @Override
    public Map<String, Parameter> parse(String customParams) {
        Map<String, Parameter> k = new HashMap<>();

        for (String paramLine : customParams.split(";")) {
            if (!paramLine.trim().isEmpty()) {
                String[] pairs = paramLine.split("=", 2);

                if (!paramLine.contains("=") || pairs[0].isEmpty())
                    throw new IllegalArgumentException(
                            "For CUSTOM_PARAMS line " + paramLine + " can not be parsed. This field should contain only lines like PARAM1=VALUE1");


                String valueOfParam = pairs[1].replaceAll("(\"|\\\\)", "\\\\$0");

                if (valueOfParam.trim().startsWith("\'") && !valueOfParam.trim().startsWith("\'{") && !valueOfParam.trim().startsWith("\'["))
                    throw new IllegalArgumentException(
                            "Key " + pairs[0] + " has incorrect value " + valueOfParam + " ' symbol is invalid for non-structured variable format");

                k.put(pairs[0].trim(), new Parameter(processParam(pairs[1]), ParametersConstants.CUSTOM_PARAMS_ORIGIN, true));
            }
        }
        return k;
    }
}

