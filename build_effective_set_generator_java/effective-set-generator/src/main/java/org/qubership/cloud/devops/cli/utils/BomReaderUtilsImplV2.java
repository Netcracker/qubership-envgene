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

package org.qubership.cloud.devops.cli.utils;

import com.fasterxml.jackson.core.type.TypeReference;
import jakarta.enterprise.context.ApplicationScoped;
import lombok.extern.slf4j.Slf4j;
import org.apache.commons.collections4.CollectionUtils;
import org.apache.commons.collections4.MapUtils;
import org.apache.commons.lang3.StringUtils;
import org.cyclonedx.model.Bom;
import org.cyclonedx.model.Component;
import org.cyclonedx.model.Property;
import org.cyclonedx.model.component.data.ComponentData;
import org.cyclonedx.model.component.data.Content;
import org.qubership.cloud.devops.cli.exceptions.MandatoryParameterException;
import org.qubership.cloud.devops.cli.pojo.dto.shared.SharedData;
import org.qubership.cloud.devops.commons.utils.Parameter;
import org.qubership.cloud.devops.commons.exceptions.AppChartValidationException;
import org.qubership.cloud.devops.commons.exceptions.BomProcessingException;
import org.qubership.cloud.devops.commons.pojo.bom.ApplicationBomDTO;
import org.qubership.cloud.devops.commons.pojo.bom.EntitiesMap;
import org.qubership.cloud.devops.commons.pojo.profile.model.Profile;
import org.qubership.cloud.devops.commons.pojo.registries.dto.RegistrySummaryDTO;
import org.qubership.cloud.devops.commons.repository.interfaces.FileDataConverter;
import org.qubership.cloud.devops.commons.service.interfaces.ProfileService;
import org.qubership.cloud.devops.commons.service.interfaces.RegistryConfigurationService;
import org.qubership.cloud.devops.commons.utils.ServiceArtifactType;

import java.io.File;
import java.util.*;
import java.util.regex.Pattern;

import static org.qubership.cloud.devops.commons.utils.constant.ApplicationConstants.*;

@ApplicationScoped
@Slf4j
public class BomReaderUtilsImplV2 {
    private static final Pattern MAVEN_PATTERN = Pattern.compile("(pkg:maven.*)\\?registry_id=(.*)&repository_id=(.*)");
    private static final List<String> IMAGE_SERVICE_MIME_TYPES = List.of(APPLICATION_VND_QUBERSHIP_SERVICE, APPLICATION_OCTET_STREAM);
    private static final List<String> CONFIG_SERVICE_MIME_TYPES = List.of(APPLICATION_VND_QUBERSHIP_CONFIGURATION_SMARTPLUG, APPLICATION_VND_QUBERSHIP_CONFIGURATION_FRONTEND, APPLICATION_VND_QUBERSHIP_CONFIGURATION_CDN, APPLICATION_VND_QUBERSHIP_CONFIGURATION);
    private static final List<String> SUB_SERVICE_ARTIFACT_MIME_TYPES = List.of(APPLICATION_XML, APPLICATION_ZIP, APPLICATION_VND_OSGI_BUNDLE, APPLICATION_JAVA_ARCHIVE);
    private final FileDataConverter fileDataConverter;
    private final ProfileService profileService;
    private final RegistryConfigurationService registryConfigurationService;
    private final SharedData sharedData;
    private final BomCommonUtils bomCommonUtils;

    public BomReaderUtilsImplV2(FileDataConverter fileDataConverter, ProfileService profileService, RegistryConfigurationService registryConfigurationService, SharedData sharedData, BomCommonUtils bomCommonUtils) {
        this.fileDataConverter = fileDataConverter;
        this.profileService = profileService;
        this.registryConfigurationService = registryConfigurationService;
        this.sharedData = sharedData;
        this.bomCommonUtils = bomCommonUtils;
    }

    public ApplicationBomDTO getAppServicesWithProfiles(String appName, String appFileRef, String baseline, Profile override, String overrideProfileName) {
        Bom bomContent = fileDataConverter.parseSbomFile(new File(appFileRef));
        if (bomContent == null) {
            return null;
        }
        EntitiesMap entitiesMap = new EntitiesMap();
        try {
            Component component = bomContent.getMetadata().getComponent();
            if (component.getMimeType().contains("application")) {
                ApplicationBomDTO applicationBomDto = component.getComponents()
                        .stream()
                        .map(subComp -> {
                            RegistrySummaryDTO registrySummaryDTO = bomCommonUtils.getRegistrySummaryDTO(subComp, MAVEN_PATTERN);
                            String mavenRepoName = registryConfigurationService.getMavenRepoForApp(registrySummaryDTO);
                            return ApplicationBomDTO.builder().name(appName).artifactId(subComp.getName()).groupId(subComp.getGroup())
                                    .version(subComp.getVersion()).mavenRepo(mavenRepoName).build();
                        }).findFirst().orElse(null);

                bomCommonUtils.getServiceEntities(entitiesMap, bomContent.getComponents());

                validateAppChart(entitiesMap, bomContent.getComponents(), appName, appFileRef);

                getPerServiceEntities(entitiesMap, bomContent.getComponents(), appName, baseline, override, bomContent, overrideProfileName);

                populateEntityDeployDescParams(entitiesMap, bomContent.getComponents(), bomContent);

                if (applicationBomDto != null) {
                    applicationBomDto.setServices(entitiesMap.getServiceMap());
                    applicationBomDto.setDeployerSessionId(entitiesMap.getDeployerSessionId());
                    applicationBomDto.setPerServiceParams(entitiesMap.getPerServiceParams());
                    applicationBomDto.setDeployDescriptors(entitiesMap.getDeployDescParamsMap());
                    applicationBomDto.setCommonDeployDescriptors(entitiesMap.getCommonParamsMap());
                    applicationBomDto.setAppChartName(entitiesMap.getAppChartName());
                    applicationBomDto.setDeployParams(entitiesMap.getDeployParams());
                }
                return applicationBomDto;
            }
        } catch (Exception e) {
            throw new BomProcessingException("error reading application sbom \n Root Cause: " + e.getMessage());
        }
        return null;
    }

    private void populateEntityDeployDescParams(EntitiesMap entitiesMap, List<Component> components, Bom bomContent) {
        Map<String, Object> commonParamsMap = new TreeMap<>();
        commonParamsMap.put("APPLICATION_NAME", bomContent.getMetadata().getComponent().getName());
        commonParamsMap.put("MANAGED_BY", "argocd");
        if (StringUtils.isNotEmpty(sharedData.getDeploymentSessionId())) {
            commonParamsMap.put("DEPLOYMENT_SESSION_ID", sharedData.getDeploymentSessionId());
            entitiesMap.setDeployerSessionId(sharedData.getDeploymentSessionId());
        } else {
            String deployerSessionId = UUID.randomUUID().toString();
            commonParamsMap.put("DEPLOYMENT_SESSION_ID", deployerSessionId);
            entitiesMap.setDeployerSessionId(deployerSessionId);
        }
        for (Component component : components) {
            if (IMAGE_SERVICE_MIME_TYPES.contains(component.getMimeType())) {
                entitiesMap.getCommonParamsMap().put(component.getName(), commonParamsMap);
                processImageServiceComponentDeployDescParams(entitiesMap.getDeployDescParamsMap(), component);
            } else if (CONFIG_SERVICE_MIME_TYPES.contains(component.getMimeType())) {
                entitiesMap.getCommonParamsMap().put(component.getName(), commonParamsMap);
                processConfigServiceComponentDeployDescParams(entitiesMap.getDeployDescParamsMap(), component);
            }
        }
    }

    private void processConfigServiceComponentDeployDescParams(Map<String, Map<String, Object>> deployParamsMap, Component component) {
        Map<String, Object> deployDescParams = new TreeMap<>();
        boolean enableTraceability = sharedData.isEnableTraceability();
        ServiceArtifactType serviceArtifactType = ServiceArtifactType.of(component.getMimeType());
        String entity = "service:" + component.getName();
        Map<String, Object> primaryArtifactMap = new TreeMap<>();
        List<Map<String, Object>> artifacts = new ArrayList<>();
        Map<String, Object> tArtifactMap = new TreeMap<>();
        if (CollectionUtils.isNotEmpty(component.getComponents())) {
            for (Component subComponent : component.getComponents()) {
                entity = "sub component '" + subComponent.getName() + "' of service:" + component.getName();
                if (subComponent.getMimeType().equalsIgnoreCase(serviceArtifactType.getArtifactMimeType())) {
                    populateOptionalParam(primaryArtifactMap, "artifactId", subComponent.getName());
                    populateOptionalParam(primaryArtifactMap, "groupId", subComponent.getGroup());
                    populateOptionalParam(primaryArtifactMap, "version", subComponent.getVersion());
                }
                if (SUB_SERVICE_ARTIFACT_MIME_TYPES.contains(subComponent.getMimeType())) {
                    String name = checkIfMandatory(subComponent.getName(), "name", entity);
                    String version = checkIfMandatory(subComponent.getVersion(), "version", entity);
                    Map<String, Object> artifactMap = new TreeMap<>();
                    artifactMap.put("artifact_id", "");
                    artifactMap.put("artifact_path", "");
                    artifactMap.put("artifact_type", "");
                    artifactMap.put("classifier", getPropertyValue(subComponent, "classifier", null, true, entity));
                    artifactMap.put("deploy_params", "");
                    artifactMap.put("gav", "");
                    artifactMap.put("group_id", "");
                    artifactMap.put("id", checkIfMandatory(subComponent.getGroup(), "group", entity) + ":" + name + ":" + version);
                    artifactMap.put("name", name + "-" + version + "." +
                            getPropertyValue(subComponent, "type", null, true, entity));
                    artifactMap.put("repository", "");
                    artifactMap.put("type", getPropertyValue(subComponent, "type", null, true, entity));
                    artifactMap.put("url", "");
                    artifactMap.put("version", "");
                    artifacts.add(artifactMap);
                }
                if (APPLICATION_ZIP.equalsIgnoreCase(subComponent.getMimeType())) {
                    String classifier = getPropertyValue(subComponent, "classifier", null, true, entity);
                    String name = subComponent.getName();
                    String version = subComponent.getVersion();
                    if (StringUtils.isNotBlank(classifier)) {
                        tArtifactMap.put(classifier, name + "-" + version + "-" + classifier + ".zip");
                    } else {
                        tArtifactMap.put("ecl", name + "-" + version + ".zip");
                    }
                }
            }
        }
        deployDescParams.put("tArtifactNames", tArtifactMap);
        deployDescParams.put("artifact", primaryArtifactMap);
        deployDescParams.put("artifacts", artifacts);
        deployDescParams.put("build_id_dtrust", getPropertyValue(component, "build_id_dtrust", null, true, entity));
        deployDescParams.put("git_branch", getPropertyValue(component, "git_branch", null, true, entity));
        deployDescParams.put("git_revision", getPropertyValue(component, "git_revision", null, true, entity));
        deployDescParams.put("git_url", getPropertyValue(component, "git_url", null, true, entity));
        deployDescParams.put("maven_repository", getPropertyValue(component, "maven_repository", null, true, entity));
        deployDescParams.put("name", checkIfMandatory(component.getName(), "name", entity));
        deployDescParams.put("service_name", checkIfMandatory(component.getName(), "name", entity));
        deployDescParams.put("version", checkIfMandatory(component.getVersion(), "version", entity));
        populateOptionalParam(deployDescParams, "type", getPropertyValue(component, "type", null, false, entity));

        // Wrap all values in Parameter objects with "sbom" origin when traceability is enabled
        if (enableTraceability && MapUtils.isNotEmpty(deployDescParams)) {
            deployDescParams = wrapMapWithOriginRecursive(deployDescParams, "sbom");
        }

        deployParamsMap.put(component.getName(), deployDescParams);
    }

    private void populateOptionalParam(Map<String, Object> paramsMap, String type, String paramValue) {
        if (paramValue != null) {
            paramsMap.put(type, paramValue);
        }
    }

    private void processImageServiceComponentDeployDescParams(Map<String, Map<String, Object>> deployParamsMap, Component component) {
        Map<String, Object> deployDescParams = new TreeMap<>();
        boolean enableTraceability = sharedData.isEnableTraceability();
        String entity = "service:" + component.getName();
        if (CollectionUtils.isNotEmpty(component.getComponents())) {
            for (Component subComponent : component.getComponents()) {
                entity = "sub component '" + subComponent.getName() + "' of service:" + component.getName();
                if (subComponent.getMimeType().equalsIgnoreCase("application/vnd.docker.image")) {
                    deployDescParams.put("docker_digest", checkIfMandatory(CollectionUtils.isNotEmpty(subComponent.getHashes()) ? subComponent.getHashes().get(0).getValue() : "", "hashes", entity));
                    deployDescParams.put("docker_repository_name", checkIfMandatory(subComponent.getGroup(), "group", entity));
                    deployDescParams.put("docker_tag", checkIfMandatory(subComponent.getVersion(), "version", entity));
                    deployDescParams.put("image_name", checkIfMandatory(subComponent.getName(), "name", entity));
                }
            }
        }
        deployDescParams.put("deploy_param", getPropertyValue(component, "deploy_param", "", true, entity));
        deployDescParams.put("artifacts", new ArrayList<>());
        deployDescParams.put("docker_registry", getPropertyValue(component, "docker_registry", null, true, entity));
        deployDescParams.put("full_image_name", getPropertyValue(component, "full_image_name", null, true, entity));
        deployDescParams.put("git_branch", getPropertyValue(component, "git_branch", null, true, entity));
        deployDescParams.put("git_revision", getPropertyValue(component, "git_revision", null, true, entity));
        deployDescParams.put("git_url", getPropertyValue(component, "git_url", null, true, entity));
        deployDescParams.put("image", getPropertyValue(component, "full_image_name", null, true, entity));
        deployDescParams.put("image_type", getPropertyValue(component, "image_type", null, true, entity));
        deployDescParams.put("name", checkIfMandatory(component.getName(), "name", entity));
        deployDescParams.put("promote_artifacts", getPropertyValue(component, "promote_artifacts", null, true, entity));
        deployDescParams.put("qualifier", getPropertyValue(component, "qualifier", null, true, entity));
        deployDescParams.put("version", checkIfMandatory(component.getVersion(), "version", entity));

        // Wrap all values in Parameter objects with "sbom" origin when traceability is enabled
        if (enableTraceability && MapUtils.isNotEmpty(deployDescParams)) {
            deployDescParams = wrapMapWithOriginRecursive(deployDescParams, "sbom");
        }

        deployParamsMap.put(component.getName(), deployDescParams);
    }

    private String getPropertyValue(Component component, String propertyName, String defaultValue, boolean mandatory, String entity) {
        String result = component.getProperties().stream()
                .filter(property -> propertyName.equals(property.getName()))
                .map(Property::getValue)
                .findFirst()
                .orElse(null);
        if (mandatory && result == null) {
            result = defaultValue;
            return checkIfMandatory(result, propertyName, entity);
        }
        return result;
    }

    private String checkIfMandatory(String value, String propertyName, String entity) {
        if (value == null) {
            throw new MandatoryParameterException(String.format("Mandatory Parameter '%s' is not present in '%s'.", propertyName, entity));
        }
        return value;
    }

    private void getPerServiceEntities(EntitiesMap entitiesMap, List<Component> components, String appName, String baseline, Profile override, Bom bomContent, String overrideProfileName) {
        for (Component component : components) {
            if (IMAGE_SERVICE_MIME_TYPES.contains(component.getMimeType())) {
                processImageServiceComponent(entitiesMap, component, appName, baseline, override, bomContent, overrideProfileName);
            } else if (CONFIG_SERVICE_MIME_TYPES.contains(component.getMimeType())) {
                processConfigServiceComponent(entitiesMap.getPerServiceParams(), component, appName, baseline, override, bomContent, overrideProfileName);
            }
        }
    }

    private void validateAppChart(EntitiesMap entitiesMap, List<Component> components, String appName, String appFileRef) {
        Optional<Component> optional = components.stream().filter(key -> "application/vnd.qubership.app.chart".equalsIgnoreCase(key.getMimeType())).findAny();
        if (sharedData.isAppChartValidation() && !optional.isPresent()) {
            throw new AppChartValidationException(String.format("App chart validation failed: application \"%s\" from SBOM \"%s\" " +
                    "has no component with mime-type \"application/vnd.qubership.app.chart\"", appName, new File(appFileRef).getName()));
        } else if (optional.isPresent()) {
            entitiesMap.setAppChartName(optional.get().getName());
        }
    }

    private void processConfigServiceComponent(Map<String, Map<String, Object>> serviceMap, Component component, String appName, String baseline, Profile override, Bom bomContent, String overrideProfileName) {
        Map<String, Object> profileValues = new TreeMap<>();
        Map<String, Object> serviceParams = new TreeMap<>();
        String entity = "service:" + component.getName();
        boolean enableTraceability = sharedData.isEnableTraceability();
        
        // Wrap SBOM-derived values in Parameter objects with "sbom" origin when traceability is enabled
        // These values come directly from SBOM metadata, not from baseline profile, so they use "sbom" origin
        Object artifactVersion = checkIfMandatory(bomContent.getMetadata().getComponent().getVersion(), "version in metadata", entity);
        Object deploymentResourceName = checkIfMandatory(component.getName(), "name", entity) + "-v1";
        Object deploymentVersion = "v1";
        Object serviceName = checkIfMandatory(component.getName(), "name", entity);
        
        if (enableTraceability) {
            serviceParams.put("ARTIFACT_DESCRIPTOR_VERSION", new Parameter(artifactVersion, "sbom", false));
            serviceParams.put("DEPLOYMENT_RESOURCE_NAME", new Parameter(deploymentResourceName, "sbom", false));
            serviceParams.put("DEPLOYMENT_VERSION", new Parameter(deploymentVersion, "sbom", false));
            serviceParams.put("SERVICE_NAME", new Parameter(serviceName, "sbom", false));
        } else {
            serviceParams.put("ARTIFACT_DESCRIPTOR_VERSION", artifactVersion);
            serviceParams.put("DEPLOYMENT_RESOURCE_NAME", deploymentResourceName);
            serviceParams.put("DEPLOYMENT_VERSION", deploymentVersion);
            serviceParams.put("SERVICE_NAME", serviceName);
        }

        // Extract profile values (from baseline profile) - these will have baseline origin if baseline exists
        if (CollectionUtils.isNotEmpty(component.getComponents())) {
            for (Component subComponent : component.getComponents()) {
                if (subComponent.getMimeType().equalsIgnoreCase("application/vnd.qubership.resource-profile-baseline")) {
                    profileValues = extractProfileValues(subComponent, appName, component.getName(), override, baseline, enableTraceability, overrideProfileName);
                }
            }
        }

        // Profile values (if any) will overwrite direct SBOM values and have their own origin (baseline or override)
        if (MapUtils.isNotEmpty(profileValues)) {
            serviceParams.putAll(profileValues);
        }
        serviceMap.put(component.getName(), serviceParams);
    }

    private void processImageServiceComponent(EntitiesMap entitiesMap, Component component, String appName, String baseline, Profile override, Bom bomContent, String overrideProfileName) {
        Map<String, Map<String, Object>> perServiceMap = entitiesMap.getPerServiceParams();
        Map<String, Object> profileValues = new TreeMap<>();
        Map<String, Object> serviceParams = new TreeMap<>();
        String tag = null;
        String entity = "service:" + component.getName();
        boolean enableTraceability = sharedData.isEnableTraceability();
        
        // Wrap SBOM-derived values in Parameter objects with "sbom" origin when traceability is enabled
        // These values come directly from SBOM metadata, not from baseline profile, so they use "sbom" origin
        Object artifactVersion = checkIfMandatory(bomContent.getMetadata().getComponent().getVersion(), "version in metadata", entity);
        Object deploymentResourceName = checkIfMandatory(component.getName(), "name", entity) + "-v1";
        Object deploymentVersion = "v1";
        Object serviceName = checkIfMandatory(component.getName(), "name", entity);
        String dockerTag = getPropertyValue(component, "full_image_name", null, true, entity);
        Object imageRepository = getImageRepository(dockerTag);
        
        if (enableTraceability) {
            serviceParams.put("ARTIFACT_DESCRIPTOR_VERSION", new Parameter(artifactVersion, "sbom", false));
            serviceParams.put("DEPLOYMENT_RESOURCE_NAME", new Parameter(deploymentResourceName, "sbom", false));
            serviceParams.put("DEPLOYMENT_VERSION", new Parameter(deploymentVersion, "sbom", false));
            serviceParams.put("SERVICE_NAME", new Parameter(serviceName, "sbom", false));
            serviceParams.put("DOCKER_TAG", new Parameter(dockerTag, "sbom", false));
            if (imageRepository != null) {
                serviceParams.put("IMAGE_REPOSITORY", new Parameter(imageRepository, "sbom", false));
            }
        } else {
            serviceParams.put("ARTIFACT_DESCRIPTOR_VERSION", artifactVersion);
            serviceParams.put("DEPLOYMENT_RESOURCE_NAME", deploymentResourceName);
            serviceParams.put("DEPLOYMENT_VERSION", deploymentVersion);
            serviceParams.put("SERVICE_NAME", serviceName);
            serviceParams.put("DOCKER_TAG", dockerTag);
            if (imageRepository != null) {
                serviceParams.put("IMAGE_REPOSITORY", imageRepository);
            }
        }
        addImageParameters(component, entitiesMap.getDeployParams());

        // Extract profile values (from baseline profile) and tag - these will have baseline origin if baseline exists
        if (CollectionUtils.isNotEmpty(component.getComponents())) {
            for (Component subComponent : component.getComponents()) {
                if (subComponent.getMimeType().equalsIgnoreCase("application/vnd.docker.image")) {
                    tag = subComponent.getVersion();
                } else if (subComponent.getMimeType().equalsIgnoreCase("application/vnd.qubership.resource-profile-baseline")) {
                    profileValues = extractProfileValues(subComponent, appName, component.getName(), override, baseline, enableTraceability, overrideProfileName);
                }
            }
            Object tagValue = checkIfMandatory(tag, "TAG", entity);
            if (enableTraceability) {
                serviceParams.put("TAG", new Parameter(tagValue, "sbom", false));
            } else {
                serviceParams.put("TAG", tagValue);
            }
        }
        if (MapUtils.isNotEmpty(profileValues)) {
            serviceParams.putAll(profileValues);
        }
        perServiceMap.put(component.getName(), serviceParams);
    }

    private void addImageParameters(Component component, Map<String, String> serviceParams) {
        if (component.getMimeType().equalsIgnoreCase(APPLICATION_OCTET_STREAM)) {
            String key = getPropertyValue(component, "deploy_param", null, false, component.getName());
            if (StringUtils.isNotEmpty(key)) {
                String value = getPropertyValue(component, "full_image_name", null, false, component.getName());
                serviceParams.put(key, value);
            }
        }
    }

    private String getImageRepository(String dockerTag) {
        if (StringUtils.isNotEmpty(dockerTag)) {
            return dockerTag.substring(0, dockerTag.lastIndexOf(":"));
        }
        return null;
    }

    private Map<String, Object> extractProfileValues(Component dataComponent, String appName, String serviceName,
                                                     Profile overrideProfile, String baseline, boolean enableTraceability, String overrideProfileName) {
        Map<String, Object> profileValues = new TreeMap<>();
        if (baseline == null) {
            profileService.setOverrideProfiles(appName, serviceName, overrideProfile, profileValues);
            // Wrap profile values recursively in Parameter objects with "sbom" origin when traceability is enabled (no baseline)
            if (enableTraceability && MapUtils.isNotEmpty(profileValues)) {
                profileValues = wrapMapWithOriginRecursive(profileValues, "sbom");
            }
        }
        for (ComponentData data : dataComponent.getData()) {
            if (baseline != null && baseline.equals(data.getName().split("\\.")[0])) {
                Content content = data.getContents();
                String encodedText = content.getAttachment().getText();
                profileValues = fileDataConverter.decodeAndParse(encodedText, new TypeReference<TreeMap<String, Object>>() {
                });

                // Track which values exist before override (to detect which ones were overridden)
                Map<String, Object> baselineValuesSnapshot = new TreeMap<>();
                if (enableTraceability && MapUtils.isNotEmpty(profileValues)) {
                    deepCopyMap(profileValues, baselineValuesSnapshot);
                }

                profileService.setOverrideProfiles(appName, serviceName, overrideProfile, profileValues);
                
                // Wrap profile values recursively in Parameter objects with appropriate origin when traceability is enabled
                // Values that were overridden should have override origin (higher priority)
                // Values that were not overridden should have baseline origin
                if (enableTraceability && MapUtils.isNotEmpty(profileValues)) {
                    String baselineOrigin = "sbom:resource-profile-baseline:" + baseline;
                    String overrideOrigin = getOverrideOrigin(overrideProfile, appName, serviceName, overrideProfileName);
                    
                    // If there are overrides, track which values changed and apply override origin to them
                    if (overrideProfile != null && overrideOrigin != null) {
                        profileValues = wrapMapWithOriginSelective(profileValues, baselineValuesSnapshot, baselineOrigin, overrideOrigin);
                    } else {
                        // No overrides, just wrap with baseline origin
                        profileValues = wrapMapWithOriginRecursive(profileValues, baselineOrigin);
                    }
                }
                break;
            }
        }
        return profileValues;
    }
    
    /**
     * Recursively wraps all values in a map (including nested maps and lists) with Parameter objects.
     * This ensures that values added/modified by setOverrideProfiles also get origins.
     */
    private Map<String, Object> wrapMapWithOriginRecursive(Map<String, Object> map, String origin) {
        if (map == null || map.isEmpty()) {
            return map;
        }
        Map<String, Object> wrapped = new TreeMap<>();
        for (Map.Entry<String, Object> entry : map.entrySet()) {
            Object value = entry.getValue();
            if (value instanceof Map) {
                // Recursively wrap nested maps
                Map<String, Object> nestedMap = (Map<String, Object>) value;
                Map<String, Object> wrappedNested = wrapMapWithOriginRecursive(nestedMap, origin);
                wrapped.put(entry.getKey(), wrappedNested);
            } else if (value instanceof List) {
                // Recursively wrap list items
                List<Object> list = (List<Object>) value;
                List<Object> wrappedList = new java.util.ArrayList<>();
                for (Object item : list) {
                    if (item instanceof Map) {
                        wrappedList.add(wrapMapWithOriginRecursive((Map<String, Object>) item, origin));
                    } else if (item instanceof List) {
                        wrappedList.add(wrapListWithOriginRecursive((List<Object>) item, origin));
                    } else {
                        wrappedList.add(new Parameter(item, origin, false));
                    }
                }
                wrapped.put(entry.getKey(), wrappedList);
            } else if (value instanceof Parameter) {
                // If already a Parameter, preserve it but ensure it has an origin
                Parameter param = (Parameter) value;
                if (param.getOrigin() == null || param.getOrigin().isEmpty()) {
                    // Replace with new Parameter if it doesn't have origin
                    Object paramValue = param.getValue();
                    if (paramValue instanceof Map) {
                        wrapped.put(entry.getKey(), wrapMapWithOriginRecursive((Map<String, Object>) paramValue, origin));
                    } else if (paramValue instanceof List) {
                        wrapped.put(entry.getKey(), wrapListWithOriginRecursive((List<Object>) paramValue, origin));
                    } else {
                        wrapped.put(entry.getKey(), new Parameter(paramValue, origin, false, param.isSecured(), null));
                    }
                } else {
                    // Preserve existing Parameter but recursively process its value
                    Object paramValue = param.getValue();
                    if (paramValue instanceof Map) {
                        wrapped.put(entry.getKey(), new Parameter(wrapMapWithOriginRecursive((Map<String, Object>) paramValue, param.getOrigin()), param.getOrigin(), false, param.isSecured(), null));
                    } else if (paramValue instanceof List) {
                        wrapped.put(entry.getKey(), new Parameter(wrapListWithOriginRecursive((List<Object>) paramValue, param.getOrigin()), param.getOrigin(), false, param.isSecured(), null));
                    } else {
                        wrapped.put(entry.getKey(), param);
                    }
                }
            } else {
                // Wrap scalar values
                wrapped.put(entry.getKey(), new Parameter(value, origin, false));
            }
        }
        return wrapped;
    }
    
    private List<Object> wrapListWithOriginRecursive(List<Object> list, String origin) {
        if (list == null || list.isEmpty()) {
            return list;
        }
        List<Object> wrapped = new java.util.ArrayList<>();
        for (Object item : list) {
            if (item instanceof Map) {
                wrapped.add(wrapMapWithOriginRecursive((Map<String, Object>) item, origin));
            } else if (item instanceof List) {
                wrapped.add(wrapListWithOriginRecursive((List<Object>) item, origin));
            } else if (item instanceof Parameter) {
                Parameter param = (Parameter) item;
                Object paramValue = param.getValue();
                if (paramValue instanceof Map) {
                    wrapped.add(new Parameter(wrapMapWithOriginRecursive((Map<String, Object>) paramValue, param.getOrigin()), param.getOrigin(), false, param.isSecured(), null));
                } else if (paramValue instanceof List) {
                    wrapped.add(new Parameter(wrapListWithOriginRecursive((List<Object>) paramValue, param.getOrigin()), param.getOrigin(), false, param.isSecured(), null));
                } else {
                    wrapped.add(param);
                }
            } else {
                wrapped.add(new Parameter(item, origin, false));
            }
        }
        return wrapped;
    }
    
    /**
     * Creates a deep copy of a map for comparison purposes.
     */
    @SuppressWarnings("unchecked")
    private void deepCopyMap(Map<String, Object> source, Map<String, Object> target) {
        if (source == null || target == null) {
            return;
        }
        for (Map.Entry<String, Object> entry : source.entrySet()) {
            Object value = entry.getValue();
            if (value instanceof Map) {
                Map<String, Object> nestedMap = new TreeMap<>();
                deepCopyMap((Map<String, Object>) value, nestedMap);
                target.put(entry.getKey(), nestedMap);
            } else if (value instanceof List) {
                List<Object> nestedList = new java.util.ArrayList<>();
                for (Object item : (List<Object>) value) {
                    if (item instanceof Map) {
                        Map<String, Object> nestedMap = new TreeMap<>();
                        deepCopyMap((Map<String, Object>) item, nestedMap);
                        nestedList.add(nestedMap);
                    } else {
                        nestedList.add(item);
                    }
                }
                target.put(entry.getKey(), nestedList);
            } else {
                target.put(entry.getKey(), value);
            }
        }
    }
    
    /**
     * Gets the origin string for resource-profile-override values.
     * Returns null if no override profile exists for this app/service.
     * If overrideProfileName is provided, includes it in the origin: "resource-profile-override:<name>"
     */
    private String getOverrideOrigin(Profile overrideProfile, String appName, String serviceName, String overrideProfileName) {
        if (overrideProfile == null || overrideProfile.getApplications() == null) {
            return null;
        }
        
        boolean hasOverride = overrideProfile.getApplications().stream()
                .filter(app -> appName.equals(app.getName()))
                .findFirst()
                .filter(app -> app.getServices() != null)
                .flatMap(app -> app.getServices().stream()
                        .filter(service -> serviceName.equals(service.getName()))
                        .findFirst())
                .isPresent();
        
        if (!hasOverride) {
            return null;
        }
        
        // Include profile name if available
        if (overrideProfileName != null && !overrideProfileName.isEmpty()) {
            return "resource-profile-override:" + overrideProfileName;
        }
        
        return "resource-profile-override";
    }
    
    /**
     * Wraps map values with origins, using override origin for values that were changed by setOverrideProfiles,
     * and baseline origin for values that were not changed.
     */
    @SuppressWarnings("unchecked")
    private Map<String, Object> wrapMapWithOriginSelective(Map<String, Object> current, 
                                                             Map<String, Object> baselineSnapshot,
                                                             String baselineOrigin, 
                                                             String overrideOrigin) {
        if (current == null || current.isEmpty()) {
            return current;
        }
        
        Map<String, Object> wrapped = new TreeMap<>();
        for (Map.Entry<String, Object> entry : current.entrySet()) {
            String key = entry.getKey();
            Object currentValue = entry.getValue();
            Object baselineValue = baselineSnapshot != null ? baselineSnapshot.get(key) : null;
            
            // Check if this value was overridden (changed or newly added)
            boolean wasOverridden = !valuesEqual(currentValue, baselineValue);
            String origin = wasOverridden ? overrideOrigin : baselineOrigin;
            
            if (currentValue instanceof Map) {
                Map<String, Object> nestedBaseline = baselineValue instanceof Map ? (Map<String, Object>) baselineValue : null;
                wrapped.put(key, wrapMapWithOriginSelective((Map<String, Object>) currentValue, nestedBaseline, baselineOrigin, overrideOrigin));
            } else if (currentValue instanceof List) {
                List<Object> nestedBaseline = baselineValue instanceof List ? (List<Object>) baselineValue : null;
                wrapped.put(key, wrapListWithOriginSelective((List<Object>) currentValue, nestedBaseline, baselineOrigin, overrideOrigin));
            } else if (currentValue instanceof Parameter) {
                // Already a Parameter, preserve it but update origin if it was overridden
                Parameter param = (Parameter) currentValue;
                if (wasOverridden) {
                    wrapped.put(key, new Parameter(param.getValue(), overrideOrigin, false, param.isSecured(), null));
                } else {
                    wrapped.put(key, param);
                }
            } else {
                wrapped.put(key, new Parameter(currentValue, origin, false));
            }
        }
        return wrapped;
    }
    
    /**
     * Wraps list values with origins, using override origin for values that were changed.
     */
    @SuppressWarnings("unchecked")
    private List<Object> wrapListWithOriginSelective(List<Object> current, 
                                                      List<Object> baselineSnapshot,
                                                      String baselineOrigin, 
                                                      String overrideOrigin) {
        if (current == null || current.isEmpty()) {
            return current;
        }
        
        List<Object> wrapped = new java.util.ArrayList<>();
        for (int i = 0; i < current.size(); i++) {
            Object currentValue = current.get(i);
            Object baselineValue = (baselineSnapshot != null && i < baselineSnapshot.size()) ? baselineSnapshot.get(i) : null;
            
            boolean wasOverridden = !valuesEqual(currentValue, baselineValue);
            String origin = wasOverridden ? overrideOrigin : baselineOrigin;
            
            if (currentValue instanceof Map) {
                Map<String, Object> nestedBaseline = baselineValue instanceof Map ? (Map<String, Object>) baselineValue : null;
                wrapped.add(wrapMapWithOriginSelective((Map<String, Object>) currentValue, nestedBaseline, baselineOrigin, overrideOrigin));
            } else if (currentValue instanceof List) {
                List<Object> nestedBaseline = baselineValue instanceof List ? (List<Object>) baselineValue : null;
                wrapped.add(wrapListWithOriginSelective((List<Object>) currentValue, nestedBaseline, baselineOrigin, overrideOrigin));
            } else if (currentValue instanceof Parameter) {
                Parameter param = (Parameter) currentValue;
                if (wasOverridden) {
                    wrapped.add(new Parameter(param.getValue(), overrideOrigin, false, param.isSecured(), null));
                } else {
                    wrapped.add(param);
                }
            } else {
                wrapped.add(new Parameter(currentValue, origin, false));
            }
        }
        return wrapped;
    }
    
    /**
     * Compares two values for equality, handling nested structures.
     */
    private boolean valuesEqual(Object value1, Object value2) {
        if (value1 == value2) {
            return true;
        }
        if (value1 == null || value2 == null) {
            return false;
        }
        if (value1 instanceof Parameter) {
            value1 = ((Parameter) value1).getValue();
        }
        if (value2 instanceof Parameter) {
            value2 = ((Parameter) value2).getValue();
        }
        // For simple comparison, use equals. For complex nested structures, this is a simplified check.
        // In practice, setOverrideProfiles typically replaces entire values, so this should work.
        return value1.equals(value2);
    }
}
