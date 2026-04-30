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

import org.apache.commons.codec.digest.DigestUtils;
import org.apache.commons.lang3.StringUtils;
import org.qubership.cloud.devops.commons.Injector;
import org.qubership.cloud.devops.commons.exceptions.NotFoundException;
import org.qubership.cloud.devops.commons.pojo.bg.BgDomainEntityDTO;
import org.qubership.cloud.devops.commons.pojo.clouds.model.Cloud;
import org.qubership.cloud.devops.commons.pojo.credentials.model.Credential;
import org.qubership.cloud.devops.commons.pojo.credentials.model.SecretCredentials;
import org.qubership.cloud.devops.commons.pojo.credentials.model.UsernamePasswordCredentials;
import org.qubership.cloud.devops.commons.pojo.cs.CompositeEntityDTO;
import org.qubership.cloud.devops.commons.pojo.cs.CompositeStructureDTO;
import org.qubership.cloud.devops.commons.pojo.namespaces.model.Namespace;
import org.qubership.cloud.devops.commons.service.interfaces.InputDataService;
import org.qubership.cloud.devops.commons.utils.CredentialUtils;
import org.qubership.cloud.devops.commons.utils.Parameter;
import org.qubership.cloud.devops.commons.utils.constant.ParametersConstants;

import java.nio.charset.StandardCharsets;
import java.util.Map;

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
        InputDataService inputDataService = Injector.getInstance().getInputDataService();
        CompositeStructureDTO compositeStructureDTO = inputDataService.getCompositeData();
        BgDomainEntityDTO bgDomainEntityDTO = inputDataService.getBGDomainData();
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
                map.putIfAbsent(STATIC_CACHE_SERVICE_ROUTE_HOST, String.format("static-cache-service-%s.%s", originalNamespace, cloudHostname));

                CredentialUtils credentialUtils = Injector.getInstance().getDi().get(CredentialUtils.class);


                if (bgDomainEntityDTO != null) {

                    BgDomainEntityDTO.NamespaceDTO origin = bgDomainEntityDTO.getOriginNamespace();
                    BgDomainEntityDTO.NamespaceDTO peer = bgDomainEntityDTO.getPeerNamespace();
                    BgDomainEntityDTO.NamespaceDTO controller = bgDomainEntityDTO.getControllerNamespace();

                    //Primary Namespace & Secondary Namespace
                    if (origin.getName().equalsIgnoreCase(originalNamespace)) {
                        map.put(ORIGIN_NAMESPACE, originalNamespace);
                        map.put(PEER_NAMESPACE, peer.getName());
                        map.put(CONTROLLER_NAMESPACE, controller.getName());
                    } else if (controller.getName().equalsIgnoreCase(originalNamespace)) { //Controller Namespace
                        if (origin != null) {
                            map.put(ORIGIN_NAMESPACE, origin.getName());
                        } else {
                            map.put(ORIGIN_NAMESPACE, originalNamespace);
                        }
                        map.put(PEER_NAMESPACE, peer.getName());
                        map.put(CONTROLLER_NAMESPACE, controller.getName());

                        if (controller != null) {
                            if (controller.getUrl() != null && !controller.getUrl().isEmpty()) {
                                map.put(BG_CONTROLLER_URL, controller.getUrl());
                            } else {
                                String bg_url = String.format("%s://bluegreen-controller-%s.%s", protocol.toLowerCase(), originalNamespace, customHost);
                                map.put(BG_CONTROLLER_URL, bg_url);
                            }

                            if (controller.getCredentials() != null && !controller.getCredentials().isEmpty()) {
                                Credential credentialPojo = credentialUtils.getCredentialsById(controller.getCredentials());
                                if (credentialPojo instanceof UsernamePasswordCredentials) {
                                    UsernamePasswordCredentials usernamePasswordCredentials = (UsernamePasswordCredentials) credentialPojo;
                                    map.put(BG_CONTROLLER_LOGIN, usernamePasswordCredentials.getUsername());
                                    map.put(BG_CONTROLLER_PASSWORD, usernamePasswordCredentials.getPassword());
                                }
                            } else {
                                map.put(BG_CONTROLLER_LOGIN, "bgoperator");
                                map.put(BG_CONTROLLER_PASSWORD, "F21wuZNRpw");
                            }
                        }

//                        String rootUrl = Injector.getInstance().get(URLUtils.class).getRootUrl();
//                        rootUrl = rootUrl.endsWith("/") ? rootUrl.substring(0, rootUrl.length() - 1) : rootUrl;
                        map.put(CMDB_CALLBACK_TOKEN, "");
                        map.put(CMDB_CALLBACK_URL, "");
//                        map.put(CMDB_CALLBACK_TOKEN, Injector.getInstance().get(BGDomainRepository.class).getBgDomainToken(tenant, cloud, config.getBgDomainNamespaceData().getName()));
//                        map.put(CMDB_CALLBACK_URL, String.format("%s/cm/v1/tenants/%s/clouds/%s/bgdomains/clone",
//                                rootUrl, tenant, cloud));
                    }
                } else {
                    map.put(ORIGIN_NAMESPACE, originalNamespace);
                }

                if (compositeStructureDTO != null) {
                    setBaselineVars(map, compositeStructureDTO.getBaseline(), bgDomainEntityDTO);
                } else if (bgDomainEntityDTO != null && compositeStructureDTO != null) {
                    if (bgDomainEntityDTO.getType().equalsIgnoreCase(BG_DOMAIN)) {
                        setBaselineVars(map, compositeStructureDTO.getBaseline(), bgDomainEntityDTO);
                    }

                }

                // Deprecated deployer parameters
                map.putIfAbsent(GATEWAY_URL, "http://internal-gateway-service:8080");
                map.putIfAbsent(STATIC_CACHE_SERVICE_ROUTE_HOST, String.format("static-cache-service-%s.%s", originalNamespace, cloudHostname));

                String gatewayNamespace = "";
                String idpUrlNamespace = "";

                if (bgDomainEntityDTO != null) {
                    if (bgDomainEntityDTO.getType().equalsIgnoreCase(BG_DOMAIN)) {
                        gatewayNamespace = bgDomainEntityDTO.getOriginNamespace().getName();
                        idpUrlNamespace = bgDomainEntityDTO.getName();
                    } else {
                        String originNamespaceName = bgDomainEntityDTO.getOriginNamespace().getName();
                        gatewayNamespace = originNamespaceName;
                        idpUrlNamespace = originNamespaceName;
                    }
                } else if (compositeStructureDTO != null) {
                    CompositeEntityDTO compositeEntityBase = compositeStructureDTO.getBaseline();
                    String namespaceFromBaseline = compositeEntityBase.getName();
                    gatewayNamespace = originalNamespace;
                    idpUrlNamespace = originalNamespace;
                    if(!originalNamespace.equalsIgnoreCase(compositeEntityBase.getName())){
                        gatewayNamespace = originalNamespace;
                        idpUrlNamespace = namespaceFromBaseline;
                    }
                } else {
                    gatewayNamespace = originalNamespace;
                    idpUrlNamespace = originalNamespace;
                }

                // Deployer parameters
                addGatewayIdentityUrls(config.getCustomParameters(), map, false, protocol.toLowerCase(), customHost, gatewayNamespace, idpUrlNamespace);
                addGatewayIdentityUrls(config.getCustomParameters(), map, true, protocol.toLowerCase(), cloudHostname, gatewayNamespace, idpUrlNamespace);
//                map.putIfAbsent(SSL_SECRET, "defaultsslcertificate"); setting this value after being validated finally
                map.putIfAbsent(BUILD_TAG_NEW, "keycloak-database");
                if (binding.getDeployerInputs() != null) {
                    map.put("CLIENT_PREFIX", originalNamespace);
                    if (binding.getDeployerInputs().getSecretId() != null) {
                        setSecretValues(map, credentialUtils);
                    }
                }
            }

            EscapeMap e2e = new EscapeMap(config.getE2eParameters(), binding, String.format(ParametersConstants.NS_E2E_ORIGIN, tenant, this.cloud, namespaceName));
            EscapeMap configServer = new EscapeMap(config.getConfigServerParameters(), binding, String.format(ParametersConstants.NS_CONFIG_SERVER_ORIGIN, tenant, this.cloud, namespaceName));

            map.put(E2E, new Parameter(e2e));
            map.put(CONFIG_SERVER, new Parameter(configServer));
            maps.put(namespaceName, map);
            return map;
        }
        return null;
    }

    private void setBaselineVars(EscapeMap map, CompositeEntityDTO baselineEntity, BgDomainEntityDTO bgDomainEntityDTO) {
        if (baselineEntity != null) {
            if (baselineEntity.getType().equalsIgnoreCase(BG_DOMAIN) && bgDomainEntityDTO != null) {
                map.put(BASELINE_ORIGIN, bgDomainEntityDTO.getOriginNamespace().getName());
                map.put(BASELINE_PEER, bgDomainEntityDTO.getPeerNamespace().getName());
                map.put(BASELINE_CONTROLLER, bgDomainEntityDTO.getControllerNamespace().getName());
                map.put(BASELINE_PROJ, bgDomainEntityDTO.getControllerNamespace().getName());
            } else if (baselineEntity.getType().equalsIgnoreCase(NAMESPACE) &&
                    !baselineEntity.getName().equalsIgnoreCase(originalNamespace)) {
                map.put(BASELINE_ORIGIN, baselineEntity.getName());
                map.put(BASELINE_PROJ, baselineEntity.getName());
            }
        }
    }

    private void setSecretValues(EscapeMap map, CredentialUtils credentialUtils) {
        String credId = binding.getDeployerInputs().getSecretId();
        String credentialValue;
        if (org.apache.commons.lang.StringUtils.isNotEmpty(credId)) {
            SecretCredentials ca = (SecretCredentials) credentialUtils.getCredentialsById(credId);
            if (ca == null) {
                throw new NotFoundException(String.format("The entered certificate \"%s\" were not found in the certificates store, " +
                        "check the correctness of the selected certificate", credId));
            }
            credentialValue = ca.getSecret();
            credentialValue = credentialValue.replace("\r\n", "\n");
            map.put("SSL_SECRET_VALUE", credentialValue);
            map.put("CERTIFICATE_BUNDLE_MD5SUM", DigestUtils.md5Hex(DigestUtils.getMd5Digest().digest(credentialValue.getBytes(StandardCharsets.UTF_8))));
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
