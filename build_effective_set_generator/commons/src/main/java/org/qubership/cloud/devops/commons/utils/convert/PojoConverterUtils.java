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

package org.qubership.cloud.devops.commons.utils.convert;


import org.qubership.cloud.devops.commons.Injector;
import org.qubership.cloud.devops.commons.exceptions.NotFoundException;
import org.qubership.cloud.devops.commons.exceptions.constant.ExceptionAdditionalInfoMessages;
import org.qubership.cloud.devops.commons.pojo.applications.dto.ApplicationDTO;
import org.qubership.cloud.devops.commons.pojo.applications.model.Application;
import org.qubership.cloud.devops.commons.pojo.applications.model.Notification;
import org.qubership.cloud.devops.commons.pojo.applications.model.PublishInfo;
import org.qubership.cloud.devops.commons.pojo.applications.dto.ApplicationLinkDTO;
import org.qubership.cloud.devops.commons.pojo.applications.model.ApplicationParams;
import org.qubership.cloud.devops.commons.pojo.clouds.dto.*;
import org.qubership.cloud.devops.commons.pojo.clouds.model.*;
import org.qubership.cloud.devops.commons.pojo.namespaces.dto.NamespaceDTO;
import org.qubership.cloud.devops.commons.pojo.namespaces.model.Namespace;
import org.qubership.cloud.devops.commons.pojo.registries.dto.*;
import org.qubership.cloud.devops.commons.pojo.registries.model.*;
import org.qubership.cloud.devops.commons.pojo.tenants.dto.TenantDTO;
import org.qubership.cloud.devops.commons.pojo.tenants.model.Tenant;
import org.qubership.cloud.devops.commons.pojo.tenants.model.GlobalE2EParameters;
import org.qubership.cloud.devops.commons.pojo.tenants.model.TenantGlobalParameters;
import org.qubership.cloud.devops.commons.pojo.tenants.dto.GlobalE2EParametersDTO;
import org.qubership.cloud.devops.commons.pojo.profile.model.Profile;
import lombok.extern.slf4j.Slf4j;

import java.io.Serializable;
import java.util.*;
import java.util.stream.Collectors;

import static org.qubership.cloud.devops.commons.utils.TokenUtils.createToken;
import static java.util.Objects.isNull;
import static java.util.Objects.nonNull;

@Slf4j
public class PojoConverterUtils implements Serializable {
    private static final long serialVersionUID = -6980736161895571063L;

    public static Namespace convertDTOToNamespace(String tenantName, String cloudName, NamespaceDTO namespaceDTO, Profile profile) {
        return Namespace.builder()
                .cloud(Injector.getInstance().getCloudConfigurationService().getCloudByTenant(tenantName, cloudName))
                .name(namespaceDTO.getName())
                .credId(namespaceDTO.getCredentialsId())
                .serverSideMerge(namespaceDTO.isServerSideMerge())
                .labels(namespaceDTO.getLabels())
                .cleanInstallApprovalRequired(namespaceDTO.isCleanInstallApprovalRequired())
                .mergeCustomPramsAndE2EParams(namespaceDTO.isMergeDeployParametersAndE2EParameters())
                .customParameters(namespaceDTO.getDeployParameters())
                .e2eParameters(namespaceDTO.getE2eParameters())
                .configServerParameters(namespaceDTO.getTechnicalConfigurationParameters())
                .parameterSets(namespaceDTO.getDeployParameterSets())
                .e2eParameterSets(namespaceDTO.getE2eParameterSets())
                .technicalParameterSets(namespaceDTO.getTechnicalConfigurationParameterSets())
                .profile(profile)
                .baseline(namespaceDTO.getProfile() != null ? namespaceDTO.getProfile().getBaseline() : null)
                .applications(Optional.ofNullable(namespaceDTO.getApplications())
                        .orElseGet(Collections::emptyList)
                        .stream()
                        .map(PojoConverterUtils::convertApplicationLinkDTOToApplication)
                        .collect(Collectors.toList()))
                .build();
    }

    public static ApplicationParams convertApplicationLinkDTOToApplication(ApplicationLinkDTO applicationLinkDTO) {
        return ApplicationParams.builder()
                .appName(applicationLinkDTO.getName())
                .appParams(applicationLinkDTO.getDeployParameters())
                .configServerParams(applicationLinkDTO.getTechnicalConfigurationParameters())
                .build();
    }

    public static Cloud convertDTOToCloud(String tenantName, CloudDTO cloudDTO, Profile profile) {
        List<DbaaSConfigDTO> dbaaSConfigDTOs = cloudDTO.getDbaasConfigs();
        Set<DBaaS> dBaaSSet = new HashSet<>();
        if (nonNull(dbaaSConfigDTOs) && !dbaaSConfigDTOs.isEmpty()) {
            dBaaSSet.addAll(dbaaSConfigDTOs.stream()
                    .map(dbaaSConfigDTO ->
                            DBaaS.builder()
                                    .credId(dbaaSConfigDTO.getCredentialsId())
                                    .apiUrl(dbaaSConfigDTO.getApiUrl())
                                    .aggregatorUrl(dbaaSConfigDTO.getAggregatorUrl())
                                    .enable(dbaaSConfigDTO.isEnable())
                                    .build())
                    .collect(Collectors.toList())
            );
        }
        List<DatabaseDTO> databaseConfigs = cloudDTO.getDatabases();
        Set<DB> dbs = new HashSet<>();
        if (nonNull(databaseConfigs) && !databaseConfigs.isEmpty()) {
            dbs.addAll(databaseConfigs.stream()
                    .map(databaseDTO ->
                            DB.builder()
                                    .type(databaseDTO.getType())
                                    .url(databaseDTO.getUrl())
                                    .external(databaseDTO.getExternal())
                                    .build())
                    .collect(Collectors.toList())
            );
        }
        MaaSConfigDTO maaSConfigDTO = cloudDTO.getMaasConfig();
        MaaS maaS;
        if (nonNull(maaSConfigDTO)) {
            maaS = MaaS.builder()
                    .Password("")
                    .Login("")
                    .credId(maaSConfigDTO.getCredentialsId())
                    .maasUrl(maaSConfigDTO.getMaasUrl())
                    .maasInternalAddress(maaSConfigDTO.getMaasInternalAddress())
                    .enable(maaSConfigDTO.isEnable())
                    .build();
        } else {
            throw new NotFoundException(
                    String.format(ExceptionAdditionalInfoMessages.CLOUD_MAAS_NOT_FOUND, cloudDTO.getName())
            );
        }
        VaultConfigDTO vaultConfigDTO = cloudDTO.getVaultConfig();
        Vault vault;
        if (nonNull(vaultConfigDTO)) {
            vault = Vault.builder()
                    .vaultUrl(vaultConfigDTO.getUrl())
                    .publicVaultUrl(vaultConfigDTO.getPublicUrl())
                    .credId(vaultConfigDTO.getCredentialsId())
                    .enable(vaultConfigDTO.isEnable())
                    .build();
        } else {
            throw new NotFoundException(
                    String.format(ExceptionAdditionalInfoMessages.CLOUD_VAULT_NOT_FOUND, cloudDTO.getName())
            );
        }

        ConsulConfigDTO consulConfigDTO = cloudDTO.getConsulConfig();
        Consul consul;
        if (nonNull(consulConfigDTO)) {
            consul = Consul.builder()
                    .enabled(consulConfigDTO.isEnabled())
                    .publicUrl(consulConfigDTO.getPublicUrl())
                    .internalUrl(consulConfigDTO.getInternalUrl())
                    .tokenSecret(consulConfigDTO.getTokenSecret())
                    .build();
        } else {
            throw new NotFoundException(
                    String.format(ExceptionAdditionalInfoMessages.CLOUD_CONSUL_NOT_FOUND,
                            cloudDTO.getName()));
        }

        return Cloud.builder()
                .name(cloudDTO.getName())
                .tenant(Injector.getInstance().getTenantConfigurationService().getTenantByName(tenantName))
                .cloudApiUrl(cloudDTO.getApiUrl())
                .cloudUrlPrv(cloudDTO.getPrivateUrl())
                .cloudUrlPub(cloudDTO.getPublicUrl())
                .cloudApiPort(cloudDTO.getApiPort())
                .cloudDashboardUrl(cloudDTO.getDashboardUrl())
                .labels(cloudDTO.getLabels())
                .defCred(cloudDTO.getDefaultCredentialsId())
                .clProtocol(cloudDTO.getProtocol())
                .dbMode(cloudDTO.getDbMode())
                .serverSideMerge(false)
                .cloudParams(cloudDTO.getDeployParameters())
                .e2eParams(cloudDTO.getE2eParameters())
                .mergeCloudAndE2EParameters(cloudDTO.isMergeDeployParametersAndE2EParameters())
                .dbaasCfg(dBaaSSet)
                .db(dbs)
                .nameSpaces(Collections.emptySet())
                .applicationParams(Optional.ofNullable(cloudDTO.getApplications())
                        .orElseGet(Collections::emptyList)
                        .stream()
                        .map(PojoConverterUtils::convertApplicationLinkDTOToApplication)
                        .collect(Collectors.toList()))
                .maas(maaS)
                .vault(vault)
                .consul(consul)
                .configServerParams(cloudDTO.getTechnicalConfigurationParameters())
                .deploymentParameterSets(cloudDTO.getDeployParameterSets())
                .e2eParameterSets(cloudDTO.getE2eParameterSets())
                .technicalParameterSets(cloudDTO.getTechnicalConfigurationParameterSets())
                .productionMode(cloudDTO.isProductionMode())
                .supportedBy(cloudDTO.getSupportedBy())
                .profile(profile)
                .baseline(cloudDTO.getProfile() != null ? cloudDTO.getProfile().getBaseline() : null)
                .build();
    }


    public static Registry convertDTOToRegistry(RegistryDTO registryDTO) {
        MavenDTO mavenDTO = registryDTO.getMavenConfig();
        Maven maven;
        if (nonNull(mavenDTO)) {
            maven = Maven.builder()
                    .repositoryDomainName(mavenDTO.getRepositoryDomainName())
                    .fullRepositoryURL(mavenDTO.getFullRepositoryUrl())
                    .targetSnapshot(mavenDTO.getTargetSnapshot())
                    .targetStaging(mavenDTO.getTargetStaging())
                    .targetRelease(mavenDTO.getTargetRelease())
                    .snapshotGroup(mavenDTO.getSnapshotGroup())
                    .releaseGroup(mavenDTO.getReleaseGroup())
                    .build();
        } else {
            throw new NotFoundException(
                    String.format(ExceptionAdditionalInfoMessages.REGISTRY_MAVEN_CONFIG_NOT_FOUND, registryDTO.getName())
            );
        }
        DockerDTO dockerDTO = registryDTO.getDockerConfig();
        Docker docker;
        if (nonNull(dockerDTO)) {
            docker = Docker.builder()
                    .snapshotUri(dockerDTO.getSnapshotUri())
                    .stagingUri(dockerDTO.getStagingUri())
                    .releaseUri(dockerDTO.getReleaseUri())
                    .groupUi(dockerDTO.getGroupUri())
                    .repositoryNameSnapshot(dockerDTO.getSnapshotRepoName())
                    .repositoryNameStaging(dockerDTO.getStagingRepoName())
                    .repositoryNameRelease(dockerDTO.getReleaseRepoName())
                    .dcGroup(dockerDTO.getGroupName())
                    .build();
        } else {
            throw new NotFoundException(
                    String.format(ExceptionAdditionalInfoMessages.REGISTRY_DOCKER_CONFIG_NOT_FOUND, registryDTO.getName())
            );
        }
        GoDTO goDTO = registryDTO.getGoConfig();
        Go go;
        if (nonNull(goDTO)) {
            go = Go.builder()
                    .targetRelease(goDTO.getGoTargetRelease())
                    .targetSnapshot(goDTO.getGoTargetSnapshot())
                    .proxyRepository(goDTO.getGoProxyRepository())
                    .build();
        } else {
            go = Go.builder()
                    .build();
        }
        RawDTO rawDTO = registryDTO.getRawConfig();
        Raw raw;
        if (nonNull(rawDTO)) {
            raw = Raw.builder()
                    .releaseRepository(rawDTO.getRawTargetRelease())
                    .snapshotRepository(rawDTO.getRawTargetSnapshot())
                    .stagingRepository(rawDTO.getRawTargetStaging())
                    .proxyRepository(rawDTO.getRawTargetProxy())
                    .build();
        } else {
            raw = Raw.builder().build();
        }
        NpmDTO npmDTO = registryDTO.getNpmConfig();
        Npm npm;
        if (nonNull(npmDTO)) {
            npm = Npm.builder()
                    .targetRelease(npmDTO.getNpmTargetRelease())
                    .targetSnapshot(npmDTO.getNpmTargetSnapshot())
                    .build();
        } else {
            npm = Npm.builder().build();
        }

        HelmDTO helmDTO = registryDTO.getHelmConfig();
        Helm helm;
        if (nonNull(helmDTO)) {
            helm = Helm.builder()
                    .targetRelease(helmDTO.getHelmTargetRelease())
                    .targetStaging(helmDTO.getHelmTargetStaging())
                    .build();
        } else {
            helm = Helm.builder().build();
        }

        HelmAppDTO helmAppDTO = registryDTO.getHelmAppConfig();
        HelmApp helmApp;
        if (nonNull(helmAppDTO)) {
            helmApp = HelmApp.builder()
                    .targetStaging(helmAppDTO.getHelmStagingRepoName())
                    .targetRelease(helmAppDTO.getHelmReleaseRepoName())
                    .helmDevRepoName(helmAppDTO.getHelmDevRepoName())
                    .helmGroupRepoName(helmAppDTO.getHelmGroupRepoName())
                    .build();
        } else {
            helmApp = HelmApp.builder().build();
        }


        return Registry.builder()
                .name(registryDTO.getName())
                .credentials(registryDTO.getCredentialsId())
                .mavenCfg(maven)
                .dockerCfg(docker)
                .goCfg(go)
                .rawCfg(raw)
                .npmCfg(npm)
                .helmCfg(helm)
                .helmAppCfg(helmApp)
                .build();
    }

    public static Tenant convertDTOToTenant(TenantDTO tenantDTO) {
        GlobalE2EParametersDTO globalE2EParametersDTO = tenantDTO.getGlobalE2EParameters();
        if (isNull(globalE2EParametersDTO)) {
            throw new NotFoundException(
                    String.format(ExceptionAdditionalInfoMessages.TENANT_GLOBAL_E2E_PARAMETERS_NOT_FOUND,
                            tenantDTO.getName()
                    )
            );
        }
        GlobalE2EParameters globalE2EParameters = GlobalE2EParameters.builder()
                .pipelineDefaultRecipients(globalE2EParametersDTO.getPipelineDefaultRecipients())
                .recipientsStrategy(globalE2EParametersDTO.getRecipientsStrategy())
                .mergeTenantAndE2EParams(globalE2EParametersDTO.isMergeTenantsAndE2EParameters())
                .envParameters(globalE2EParametersDTO.getEnvironmentParameters())
                .build();
        TenantGlobalParameters tenantGlobalParameters = TenantGlobalParameters.builder()
                .deployParameters(tenantDTO.getDeployParameters())
                .e2eParameters(globalE2EParameters)
                .technicalConfiguration(tenantDTO.getTechnicalConfigurationParameters() != null ?
                        tenantDTO.getTechnicalConfigurationParameters() : Collections.emptyMap())
                .build();

        return Tenant.builder()
                .name(tenantDTO.getName())
                .description(tenantDTO.getDescription())
                .owners(tenantDTO.getOwners())
                .globalParameters(tenantGlobalParameters)
                .registry(new Registry(tenantDTO.getRegistryName()))
                .dcrRoot("")
                .mvnGroup("")
                .gitRepository(tenantDTO.getGitRepository())
                .defaultBranch(tenantDTO.getDefaultBranch())
                .credential(tenantDTO.getCredential())
                .token(createToken())
                .labels(tenantDTO.getLabels())
                .deploymentParameterSets(tenantDTO.getDeploymentParameterSets() != null
                        ? tenantDTO.getDeploymentParameterSets() : Collections.emptyList())
                .e2eParameterSets(tenantDTO.getE2eParameterSets() != null
                        ? tenantDTO.getE2eParameterSets() : Collections.emptyList())
                .technicalParameterSets(tenantDTO.getTechnicalParameterSets() != null
                        ? tenantDTO.getTechnicalParameterSets() : Collections.emptyList())
                .build();
    }

    public static Application convertDTOToApplication(ApplicationDTO applicationDTO) {
        Registry registry = Registry.builder().name(applicationDTO.getRegistryName()).build();
        return Application.builder()
                .name(applicationDTO.getName())
                .artifactId(applicationDTO.getArtifactId())
                .groupId(applicationDTO.getGroupId())
                .params(applicationDTO.getDeployParameters())
                .technicalParams(applicationDTO.getTechnicalConfigurationParameters())
                .registry(registry)
                .tenant(null)
                .supportParallelDeploy(applicationDTO.isSupportParallelDeploy())
                .config("")
                .baseline("")
                .notifications(new Notification())
                .publishInfo(PublishInfo.builder().build())
                .solutionDescriptor(applicationDTO.isSolutionDescriptor())
                .build();
    }

}
