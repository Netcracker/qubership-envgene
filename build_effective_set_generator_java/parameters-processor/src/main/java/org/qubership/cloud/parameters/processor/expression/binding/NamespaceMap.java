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
import org.qubership.cloud.devops.commons.exceptions.NotFoundException;
import org.qubership.cloud.devops.commons.pojo.clouds.model.Cloud;
import org.qubership.cloud.devops.commons.pojo.credentials.model.SecretCredentials;
import org.qubership.cloud.devops.commons.pojo.namespaces.model.Namespace;
import org.qubership.cloud.devops.commons.utils.CredentialUtils;
import org.qubership.cloud.devops.commons.utils.Parameter;
import org.qubership.cloud.devops.commons.utils.constant.ParametersConstants;
import org.apache.commons.codec.digest.DigestUtils;
import org.apache.commons.lang3.StringUtils;

import java.nio.charset.StandardCharsets;
import java.util.Map;
import java.util.UUID;

import static org.qubership.cloud.devops.commons.utils.constant.NamespaceConstants.*;


public class NamespaceMap extends DynamicMap {

    private final String tenant;
    private final String cloud;
    private String defaultApp;
    private boolean mergeE2E;
    private final String originalNamespace;

    public NamespaceMap(String tenant, String cloud, String defaultNamespace, String defaultApp,
                        Binding binding, String originalNamespace) {
        super(defaultNamespace, binding);
        this.tenant = tenant;
        this.cloud = cloud;
        this.defaultApp = defaultApp;
        this.originalNamespace = originalNamespace;
    }

    public boolean isMergeE2E() {
        return mergeE2E;
    }

    @Override
    public DynamicMap init() {
        DynamicMap result = super.init();
        defaultApp = null;
        return result;
    }

    @Override
    public Map<String, Parameter> getMap(String namespaceName) {
        Namespace config = Injector.getInstance().getNamespaceConfigurationService().getNamespaceByCloud(cloud, tenant, namespaceName);
        if (config != null) {
            mergeE2E = config.isMergeCustomPramsAndE2EParams();
            EscapeMap map = new EscapeMap(config.getCustomParameters(), binding, String.format(ParametersConstants.NS_ORIGIN, tenant, this.cloud, namespaceName));
            map.putIfAbsent(NAMESPACE, originalNamespace);

            map.put(APP, new Parameter(new NamespaceApplicationMap(config, defaultApp, binding).init()));

            Cloud cloud = Injector.getInstance().getCloudConfigurationService().getCloudByTenant(tenant, this.cloud);
            if (StringUtils.isNotBlank(cloud.getCloudApiUrl())) {
                String protocol = StringUtils.isNotBlank(cloud.getClProtocol()) ? cloud.getClProtocol() : "https";
                String publicDNS = cloud.getCloudUrlPub();
                String privateDNS = cloud.getCloudUrlPrv();

                String cloudHostname = StringUtils.isNotBlank(publicDNS) ? publicDNS : cloud.getCloudApiUrl();
                String customHost = StringUtils.isNotBlank(privateDNS) ? privateDNS : StringUtils.isNotBlank(publicDNS) ? publicDNS : cloudHostname;

                // Deprecated deployer parameters
                map.putIfAbsent(GATEWAY_URL, "http://internal-gateway-service:8080");
                map.putIfAbsent(STATIC_CACHE_SERVICE_ROUTE_HOST, String.format("static-cache-service-%s.%s", namespaceName, cloudHostname));

                CredentialUtils credentialUtils = Injector.getInstance().getDi().get(CredentialUtils.class);

                map.put(ORIGIN_NAMESPACE, originalNamespace);

                // Deprecated deployer parameters
                map.putIfAbsent(GATEWAY_URL, "http://internal-gateway-service:8080");
                map.putIfAbsent(STATIC_CACHE_SERVICE_ROUTE_HOST, String.format("static-cache-service-%s.%s", namespaceName, cloudHostname));

                // Deployer parameters
                addGatewayIdentityUrls(config.getCustomParameters(), map, false, protocol.toLowerCase(), customHost, namespaceName, namespaceName);
                addGatewayIdentityUrls(config.getCustomParameters(), map, true, protocol.toLowerCase(), cloudHostname, namespaceName, namespaceName);
                map.putIfAbsent(NAMESPACE, namespaceName);
                map.putIfAbsent(SSL_SECRET, "defaultsslcertificate");
                map.putIfAbsent(BUILD_TAG_NEW, "keycloak-database");
                if (binding.getDeployerInputs() != null) {
                    map.put("CLIENT_PREFIX",namespaceName);
                    if ( binding.getDeployerInputs().getSecretId() != null) {
                        setSecretValues(map, credentialUtils);
                    }
//                    if (binding.getDeployerInputs().getDeploySessionId() != null) {
//                        map.put("DEPLOYMENT_SESSION_ID",binding.getDeployerInputs().getDeploySessionId());
//                    } else {
//                        map.put("DEPLOYMENT_SESSION_ID", UUID.randomUUID().toString());
//                    }
                }
            }

            EscapeMap e2e = new EscapeMap(config.getE2eParameters(), binding, String.format(ParametersConstants.NS_E2E_ORIGIN, tenant, this.cloud, namespaceName));
            EscapeMap configServer = new EscapeMap(config.getConfigServerParameters(), binding, String.format(ParametersConstants.NS_CONFIG_SERVER_ORIGIN, tenant, this.cloud, namespaceName));

            checkEscape(map);
            checkEscape(e2e);
            checkEscape(configServer);

            map.put(E2E, new Parameter(e2e));
            map.put(CONFIG_SERVER, new Parameter(configServer));
            maps.put(namespaceName, map);
            return map;
        }
        return null;
    }

    private void setSecretValues(EscapeMap map, CredentialUtils credentialUtils) {
        String credId = binding.getDeployerInputs().getSecretId();
        String credentialValue ;
        if (org.apache.commons.lang.StringUtils.isNotEmpty(credId)) {
            SecretCredentials ca = (SecretCredentials) credentialUtils.getCredentialsById(credId);
            if (ca == null) {
                throw new NotFoundException(String.format("The entered certificate \"%s\" were not found in the certificates store, " +
                        "check the correctness of the selected certificate", credId));
            }
            credentialValue = ca.getSecret();
            credentialValue = credentialValue.replace("\r\n", "\n");
            map.put("SSL_SECRET_VALUE",credentialValue);
            map.put("CERTIFICATE_BUNDLE_MD5SUM",DigestUtils.md5Hex(DigestUtils.getMd5Digest().digest(credentialValue.getBytes(StandardCharsets.UTF_8))));
        }
    }

    private void addGatewayIdentityUrls(Map<String, Object> customParameters, EscapeMap map, boolean isPublic, String protocol, String host, String namespaceGatewayUrl, String namespaceIdpUrl) {
        String defaultGatewayUrl = isPublic ? String.format("%s://public-gateway-%s.%s", protocol.toLowerCase(), namespaceGatewayUrl, host)
                : String.format("%s://private-gateway-%s.%s", protocol.toLowerCase(), namespaceGatewayUrl, host);
        String defaultIdpUrl = isPublic ? String.format("%s://public-gateway-%s.%s", protocol.toLowerCase(), namespaceIdpUrl, host)
                : String.format("%s://private-gateway-%s.%s", protocol.toLowerCase(), namespaceIdpUrl, host);

        String gatewayUrl = isPublic ? PUBLIC_GATEWAY_URL : PRIVATE_GATEWAY_URL;
        String identityProviderUrl = isPublic ? PUBLIC_IDENTITY_PROVIDER_URL : PRIVATE_IDENTITY_PROVIDER_URL;
        if (customParameters.containsKey(gatewayUrl) && customParameters.containsKey(identityProviderUrl)) {
            map.put(gatewayUrl, String.valueOf(customParameters.get(gatewayUrl)));
            map.put(identityProviderUrl, String.valueOf(customParameters.get(identityProviderUrl)));
        } else {
            if (customParameters.containsKey(gatewayUrl)) {
                map.put(gatewayUrl, String.valueOf(customParameters.get(gatewayUrl)));
                map.put(identityProviderUrl, String.valueOf(customParameters.get(gatewayUrl)));
            }
            if (customParameters.containsKey(identityProviderUrl)) {
                map.put(identityProviderUrl, String.valueOf(customParameters.get(identityProviderUrl)));
            }
        }
        map.putIfAbsent(gatewayUrl, defaultGatewayUrl);
        map.putIfAbsent(identityProviderUrl, defaultIdpUrl);
    }

}
