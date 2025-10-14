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

import org.qubership.cloud.devops.commons.utils.constant.CredentialConstants;
import org.qubership.cloud.devops.commons.utils.constant.ParametersConstants;
import org.qubership.cloud.devops.commons.Injector;
import org.qubership.cloud.devops.commons.pojo.credentials.model.Credential;
import org.qubership.cloud.devops.commons.pojo.credentials.model.UsernamePasswordCredentials;
import org.qubership.cloud.devops.commons.pojo.parameterset.ParameterSet;
import org.qubership.cloud.devops.commons.pojo.parameterset.ParameterSetApplication;
import org.qubership.cloud.devops.commons.utils.Parameter;
import org.qubership.cloud.parameters.processor.dto.DeployerInputs;
import org.qubership.cloud.parameters.processor.parser.EscapeParametersParser;
import org.qubership.cloud.parameters.processor.parser.OldParametersParser;
import org.qubership.cloud.parameters.processor.parser.ParametersParser;

import lombok.Getter;
import lombok.extern.slf4j.Slf4j;

import java.util.*;
import java.util.stream.Collectors;

@Slf4j
public class Binding extends HashMap<String, Parameter> implements Cloneable {

    String escapeSequence;
    @Getter
    private DeployerInputs deployerInputs;
    private Map<String, Parameter> defaultMap;
    private final Map<String, Parameter> calculatedMap = new HashMap<>();
    @Getter
    private String tenant;
    private ParametersParser escapeParser;
    private ParametersParser oldParser;

    public Binding(String defaultEscapeSequence) {
        this.escapeSequence = defaultEscapeSequence;
        this.tenant = "";
    }

    public Binding(String defaultEscapeSequence, DeployerInputs deployerInputs) {
        this.escapeSequence = defaultEscapeSequence;
        this.tenant = "";
        this.deployerInputs = deployerInputs;
    }

    public String getProcessorType() {
        return escapeSequence;
    }

    public ParametersParser getParser() {
        ParametersParser parser;
        if (escapeSequence.equals("true")) {
            return (parser = escapeParser) == null ? (escapeParser = new EscapeParametersParser()) : parser;
        } else {
            return (parser = oldParser) == null ? (oldParser = new OldParametersParser()) : parser;
        }
    }

    private void processSet(String tenant, String setName, String application, EscapeMap parameterSet, EscapeMap applicationMap) {
        ParameterSet set = Injector.getInstance().getParameterSetService().getParameterSet(tenant, setName);
        if (set != null) {
            parameterSet.putAllStrings(set.getParameters(), String.format(ParametersConstants.PARAMETER_SET_ORIGIN, setName));
            ParameterSetApplication parameterSetApplication = set.getApplications().stream()
                    .filter(app -> app.getAppName().equals(application))
                    .findFirst()
                    .orElse(null);
            if (parameterSetApplication != null) {
                applicationMap.putAllStrings(parameterSetApplication.getParameters(), String.format(ParametersConstants.PARAMETER_SET_APP_ORIGIN, setName, application));
            }
        }
    }

    public Binding init(String tenant, String cloud, String namespace, String application, String originalNamespace) {
        this.tenant = tenant;
        super.put("tenant", new Parameter(new TenantMap(tenant, cloud, namespace, application, this, originalNamespace).init()));
        super.put("application", new Parameter(new ApplicationMap(application, this, namespace).init()));
        super.put("creds", new Parameter(new CredentialsMap(this).init()));

        Map<String, Parameter> processed = calculateCredentialsAndPrepareStructuredParams(this, Boolean.parseBoolean(getProcessorType()));

        this.putAll(processed);
        return this;
    }

    public Binding additionalParameters(Map<String, Parameter> parameters) {
        super.putAll(parameters);
        return this;
    }

    private Map<String, Parameter> calculateCredentialsAndPrepareParams(String keyCloudParameter, Parameter valueCloudParameter, boolean escapeSequence) {
        Object value = valueCloudParameter.getValue();
        if (value instanceof String) {
            value = ((String) value).trim();
        }
        if (keyCloudParameter.startsWith(CredentialConstants.CALCULABLE_CREDS_FIELD)) {
            String replaceKey = CredentialConstants.CALCULABLE_CREDS_FIELD;
            String credId = (String) value;
            if (keyCloudParameter.startsWith(CredentialConstants.CALCULABLE_CLOUD_CREDS_FIELD)) {
                replaceKey = CredentialConstants.CALCULABLE_CLOUD_CREDS_FIELD;
                credId = String.format("%s-%s-%s", this.getTenant(), this.get("tenant").get("cloud").get("CLOUDNAME"), credId);
            } else if (keyCloudParameter.startsWith(CredentialConstants.CALCULABLE_NS_CREDS_FIELD)) {
                replaceKey = CredentialConstants.CALCULABLE_NS_CREDS_FIELD;
                credId = String.format("%s-%s-%s-%s", this.getTenant(), this.get("tenant").get("cloud").get("CLOUDNAME"), this.get("tenant").get("cloud").get("namespace").get("NAMESPACE"), credId);
            }

            String[] loginPassVarNames = keyCloudParameter.replaceFirst(replaceKey + "\\{", "").split(",", 0);
            String loginVarName = loginPassVarNames[0];
            String passVarName = loginPassVarNames[1].replaceFirst("\\}", "");


            Credential credentials = Injector.getInstance().getCredentialUtils().getCredentialsById(credId);
            if (credentials == null) {
                throw new UnsupportedOperationException("Credentials id " + credId + " was not found  : ");
            }

            return new HashMap<>() {
                {
                    String password = ((UsernamePasswordCredentials) credentials).getPassword();
                    String username = ((UsernamePasswordCredentials) credentials).getUsername();
                    put(loginVarName.trim(), new Parameter(username, valueCloudParameter.getOrigin(), true, true, null));
                    put(passVarName.trim(), new Parameter(password, valueCloudParameter.getOrigin(), true, true, null));
                }
            };
        } else {
            return new HashMap<>() {
                {
                    put(keyCloudParameter.trim(), valueCloudParameter);
                }
            };
        }
    }

    private Map<String, Parameter> calculateCredentialsAndPrepareStructuredParams(Map<String, Parameter> params, Boolean escape) {
        Map<String, Parameter> result = params.entrySet().stream().map(entry -> {
                    Parameter param = new Parameter(entry.getValue());
                    if (param.getValue() instanceof Map) {
                        return new HashMap<String, Parameter>() {
                            {
                                put(entry.getKey(), new Parameter(calculateCredentialsAndPrepareStructuredParams((Map<String, Parameter>) param.getValue(), escape)));
                            }
                        };
                    }
                    return calculateCredentialsAndPrepareParams(entry.getKey(), param, escape);
                }).flatMap(c -> c.entrySet().stream())
                .collect(Collectors.toMap(Map.Entry::getKey, Map.Entry::getValue, (e1, e2) -> e2));
        params.clear();
        params.putAll(result);
        return params;
    }

    public Map<String, Parameter> getDotMap(String defaultName) {
        Map<String, Parameter> defaultMap = this;
        for (String token : defaultName.split("\\.")) {
            if (!token.isEmpty() && defaultMap.containsKey(token)) {
                defaultMap = (Map<String, Parameter>) defaultMap.get(token).getValue();
            }
        }
        return defaultMap;
    }

    public Map<String, Parameter> setDefault(String defaultName) {
        this.defaultMap = getDotMap(defaultName);
        return defaultMap;
    }

    @Override
    public Set<String> keySet() {
        return super.keySet();
    }

    @Override
    public Collection<Parameter> values() {
        return super.values();
    }

    @Override
    public Set<Entry<String, Parameter>> entrySet() {
        return super.entrySet();
    }

    @Override
    public Parameter getOrDefault(Object key, Parameter defaultValue) {
        return super.getOrDefault(key, defaultValue);
    }

    public Parameter get(Object key) {
        Parameter result = super.get(key);
        if (result == null) {
            result = calculatedMap.get(key);
        }
        if (result == null && defaultMap != this) {
            result = defaultMap.get(key);
        }
        if (result == null || result.getValue() == null) {
            return null;
        }
        return result;
    }

    public void putAllCalculated(Map<? extends String, ? extends Parameter> m) {
        calculatedMap.putAll(m);
    }

    public Object clone() {
        return super.clone();
    }
}
