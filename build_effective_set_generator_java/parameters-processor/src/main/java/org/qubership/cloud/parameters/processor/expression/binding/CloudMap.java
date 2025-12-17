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

import org.qubership.cloud.devops.commons.Injector;
import org.qubership.cloud.devops.commons.pojo.clouds.model.Cloud;
import org.qubership.cloud.devops.commons.pojo.clouds.model.Consul;
import org.qubership.cloud.devops.commons.pojo.clouds.model.DBaaS;
import org.qubership.cloud.devops.commons.pojo.clouds.model.MaaS;
import org.qubership.cloud.devops.commons.pojo.clouds.model.Vault;
import org.qubership.cloud.devops.commons.pojo.credentials.model.Credential;
import org.qubership.cloud.devops.commons.pojo.credentials.model.StringCredentials;
import org.qubership.cloud.devops.commons.pojo.credentials.model.UsernamePasswordCredentials;
import org.qubership.cloud.devops.commons.pojo.credentials.model.VaultAppRoleCredentials;
import org.qubership.cloud.devops.commons.utils.CredentialUtils;
import org.qubership.cloud.devops.commons.utils.constant.ParametersConstants;
import org.qubership.cloud.devops.commons.utils.Parameter;

import com.bettercloud.vault.SslConfig;
import com.bettercloud.vault.VaultException;
import org.apache.commons.lang.StringUtils;

import java.util.Map;

import static org.qubership.cloud.devops.commons.utils.constant.CredentialConstants.*;

public class CloudMap extends DynamicMap {

    private final String tenant;
    private String defaultApp;
    private String defaultNamespace;
    private boolean mergeE2E;
    private String originalNamespace;

    public CloudMap(String tenant, String defaultCloud, String defaultNamespace, String defaultApp,
                    Binding binding, String originalNamespace) {
        super(defaultCloud, binding);
        this.tenant = tenant;
        this.defaultNamespace = defaultNamespace;
        this.defaultApp = defaultApp;
        this.originalNamespace = originalNamespace;
    }

    public boolean isMergeE2E() {
        return mergeE2E;
    }

    @Override
    public DynamicMap init() {
        DynamicMap result = super.init();
        defaultNamespace = null;
        defaultApp = null;
        return result;
    }

    @Override
    public Map<String, Parameter> getMap(String cloudName) {
        Cloud config = Injector.getInstance().getCloudConfigurationService().getCloudByTenant(tenant, cloudName);
        if (config == null) {
            return null; // return empty map instead?
        }
        mergeE2E = config.isMergeCloudAndE2EParameters();
        EscapeMap map = new EscapeMap(config.getCloudParams(), binding, String.format(ParametersConstants.CLOUD_ORIGIN, tenant, cloudName));
        EscapeMap e2e = new EscapeMap(config.getE2eParams(), binding, String.format(ParametersConstants.CLOUD_E2E_ORIGIN, tenant, cloudName));
        EscapeMap configServer = new EscapeMap(config.getConfigServerParams(), binding, String.format(ParametersConstants.CLOUD_CONFIG_SERVER_ORIGIN, tenant, cloudName));

        map.put("app", new Parameter(new CloudApplicationMap(config, defaultApp, binding).init()));


        checkEscape(map);
        checkEscape(e2e);
        checkEscape(configServer);
        CredentialUtils credentialUtils = Injector.getInstance().getCredentialUtils();
        for (DBaaS dbaas : config.getDbaasCfg()) {
            if (dbaas.getApiUrl() != null) {
                map.putIfAbsent("API_DBAAS_ADDRESS", dbaas.getApiUrl());
            } else {
                map.putIfAbsent("API_DBAAS_ADDRESS", "");
            }
            if (dbaas.getAggregatorUrl() != null) {
                map.putIfAbsent("DBAAS_AGGREGATOR_ADDRESS", dbaas.getAggregatorUrl());
            } else {
                map.putIfAbsent("DBAAS_AGGREGATOR_ADDRESS", "");
            }

            Credential cred = credentialUtils.getCredentialsById(dbaas.getCredId());
            if (cred instanceof UsernamePasswordCredentials) {
                map.putIfAbsent("DBAAS_AGGREGATOR_USERNAME", ((UsernamePasswordCredentials) cred).getUsername());
                map.putIfAbsent("DBAAS_AGGREGATOR_PASSWORD", ((UsernamePasswordCredentials) cred).getPassword());
                map.putIfAbsent("DBAAS_CLUSTER_DBA_CREDENTIALS_USERNAME", ((UsernamePasswordCredentials) cred).getUsername());
                map.putIfAbsent("DBAAS_CLUSTER_DBA_CREDENTIALS_PASSWORD", ((UsernamePasswordCredentials) cred).getPassword());
            } else {
                map.putIfAbsent("DBAAS_AGGREGATOR_USERNAME", DEFAULT_DBAAS_AGGREGATOR_LOGIN);
                map.putIfAbsent("DBAAS_AGGREGATOR_PASSWORD", DEFAULT_DBAAS_AGGREGATOR_PASSWORD);
                map.putIfAbsent("DBAAS_CLUSTER_DBA_CREDENTIALS_USERNAME", DEFAULT_DBAAS_AGGREGATOR_LOGIN);
                map.putIfAbsent("DBAAS_CLUSTER_DBA_CREDENTIALS_PASSWORD", DEFAULT_DBAAS_AGGREGATOR_PASSWORD);
            }
            map.putIfAbsent("DBAAS_ENABLED", new Parameter(dbaas.isEnable()));
        }

        MaaS maas = config.getMaas();
        if (maas != null) {
            map.putIfAbsent("MAAS_ENABLED", new Parameter(maas.isEnable()));
            if (maas.isEnable()) {
                //Deprecated. For backward compatibility. New name MAAS_EXTERNAL_ROUTE
                map.put("MAAS_SERVICE_ADDRESS", maas.getMaasUrl());

                map.put("MAAS_EXTERNAL_ROUTE", maas.getMaasUrl());
                map.put("MAAS_INTERNAL_ADDRESS", maas.getMaasInternalAddress());
                Credential cred = credentialUtils.getCredentialsById(maas.getCredId());
                if (cred instanceof UsernamePasswordCredentials) {
                    map.putIfAbsent("MAAS_CREDENTIALS_USERNAME", ((UsernamePasswordCredentials) cred).getUsername());
                    map.putIfAbsent("MAAS_CREDENTIALS_PASSWORD", ((UsernamePasswordCredentials) cred).getPassword());
                } else {
                    map.putIfAbsent("MAAS_CREDENTIALS_USERNAME", DEFAULT_MAAS_LOGIN);
                    map.putIfAbsent("MAAS_CREDENTIALS_PASSWORD", DEFAULT_MAAS_PASSWORD);
                }
            }
        } else {
            map.putIfAbsent("MAAS_ENABLED", new Parameter(false));
        }

        Vault vaultConfig = config.getVault();
        if (vaultConfig != null && vaultConfig.isEnable()) {
            //map.put("VAULT_INTEGRATION", Boolean.toString(vaultConfig.isEnable()));
            map.putIfAbsent("VAULT_ADDR", vaultConfig.getVaultUrl());

            // Not required, is equal to VAULT_ADDR by default //
            String address = StringUtils.isEmpty(vaultConfig.getPublicVaultUrl()) ? vaultConfig.getVaultUrl() : vaultConfig.getPublicVaultUrl();
            map.putIfAbsent("PUBLIC_VAULT_URL", address);

            Credential credentials = credentialUtils.getCredentialsById(vaultConfig.getCredId());
            if (credentials instanceof VaultAppRoleCredentials) {
                try {
                    VaultAppRoleCredentials vaultAppRole = (VaultAppRoleCredentials) credentials;
                    com.bettercloud.vault.Vault vault = new com.bettercloud.vault.Vault(new com.bettercloud.vault.VaultConfig()
                            .address(address)
                            .engineVersion(2)
                            .sslConfig(new SslConfig().verify(false).build())
                            .build());
                    String token = vault.auth()
                            .loginByAppRole(vaultAppRole.getPath(), vaultAppRole.getRoleId(), vaultAppRole.getSecretId())
                            .getAuthClientToken();
                    map.put("VAULT_TOKEN", token);
                } catch (VaultException e) {
                    map.putIfAbsent("VAULT_TOKEN", "");
                }
            } else {
                map.putIfAbsent("VAULT_TOKEN", "");
            }
        }
        Consul consul = config.getConsul();
        if (consul != null && consul.isEnabled()) {
            map.putIfAbsent("CONSUL_URL", consul.getInternalUrl());
            map.putIfAbsent("CONSUL_PUBLIC_URL", consul.getPublicUrl());

            Credential cred = credentialUtils.getCredentialsById(consul.getTokenSecret());
            if (cred instanceof StringCredentials) {
                map.putIfAbsent("CONSUL_ADMIN_TOKEN", ((StringCredentials) cred).getSecret());
            } else {
                map.putIfAbsent("CONSUL_ADMIN_TOKEN", "");
            }
        }

        map.put("PRODUCTION_MODE", new Parameter(config.isProductionMode()));
        map.put("namespace", new Parameter(new NamespaceMap(tenant, cloudName, defaultNamespace, defaultApp, binding, originalNamespace).init()));
        map.put("CLOUDNAME", cloudName);
        map.put("e2e", new Parameter(e2e));
        map.put("config-server", new Parameter(configServer));

        String api = "https://" + config.getCloudApiUrl() + ":" + config.getCloudApiPort();
        String publicDNS = config.getCloudUrlPub();
        String privateDNS = config.getCloudUrlPrv();
        String cloudHostname = StringUtils.isNotBlank(publicDNS) ? publicDNS : config.getCloudApiUrl();
        String customHost = StringUtils.isNotBlank(privateDNS) ? privateDNS : StringUtils.isNotBlank(publicDNS) ? publicDNS : cloudHostname;

        // Deprecated deployer parameters
        map.putIfAbsent("CUSTOM_HOST", customHost);
        map.putIfAbsent("SERVER_HOSTNAME", cloudHostname);
        map.putIfAbsent("OPENSHIFT_SERVER", api);

        // Deployer parameters
        String protocol = StringUtils.isNotBlank(config.getClProtocol()) ? config.getClProtocol() : "https";
        map.putIfAbsent("CLOUD_PROTOCOL", protocol.toLowerCase());
        map.putIfAbsent("CLOUD_API_HOST", config.getCloudApiUrl());
        if (StringUtils.isBlank(config.getCloudUrlPrv())) {
            map.putIfAbsent("CLOUD_PRIVATE_HOST", config.getCloudUrlPub());
        } else {
            map.putIfAbsent("CLOUD_PRIVATE_HOST", config.getCloudUrlPrv());
        }
        map.putIfAbsent("CLOUD_PUBLIC_HOST", config.getCloudUrlPub());

        String port = StringUtils.isNotBlank(config.getCloudApiPort()) ? config.getCloudApiPort() : "8443";
        map.putIfAbsent("CLOUD_API_PORT ", port);

        maps.put(cloudName, map);

        return map;
    }
}
