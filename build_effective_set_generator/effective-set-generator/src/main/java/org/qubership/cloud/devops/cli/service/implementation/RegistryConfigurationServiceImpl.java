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

package org.qubership.cloud.devops.cli.service.implementation;

import io.quarkus.arc.Unremovable;
import jakarta.enterprise.context.ApplicationScoped;
import lombok.extern.slf4j.Slf4j;
import org.qubership.cloud.devops.cli.pojo.dto.input.InputData;
import org.qubership.cloud.devops.commons.pojo.registries.dto.DockerDTO;
import org.qubership.cloud.devops.commons.pojo.registries.dto.MavenDTO;
import org.qubership.cloud.devops.commons.pojo.registries.dto.RegistryDTO;
import org.qubership.cloud.devops.commons.pojo.registries.dto.RegistrySummaryDTO;
import org.qubership.cloud.devops.commons.service.interfaces.RegistryConfigurationService;

import java.util.Optional;


@ApplicationScoped
@Unremovable
@Slf4j
public class RegistryConfigurationServiceImpl implements RegistryConfigurationService {

    private final InputData inputData;

    public RegistryConfigurationServiceImpl(InputData inputData) {
        this.inputData = inputData;
    }
    @Override
    public Optional<RegistryDTO> getRegistry(String registryName) {
        return Optional.ofNullable(inputData.getRegistryDTOMap().get(registryName));
    }

    @Override
    public String getMavenRepoForApp(RegistrySummaryDTO registry) {
        if (registry != null) {
            String registryName = registry.getName();
            String appMavenRepo = registry.getRepoId();
            if (registryName != null && !registryName.isEmpty()) {
                Optional<RegistryDTO> registryDTO = getRegistry(registryName);
                if (registryDTO.isPresent() && registryDTO.get().getMavenConfig() != null) {
                    MavenDTO mavenDTO = registryDTO.get().getMavenConfig();
                    return String.format("%s/%s", mavenDTO.getFullRepositoryUrl(), mapAndGetMavenRepo(mavenDTO, appMavenRepo));
                }
            }
        }
        return null;
    }

    @Override
    public String getDockerRepoForService(RegistrySummaryDTO registry) {
        if (registry != null) {
            String registryName = registry.getName();
            String appDockerRepo = registry.getRepoId();
            if (registryName != null && !registryName.isEmpty()) {
                Optional<RegistryDTO> registryDTO = getRegistry(registryName);
                if (registryDTO.isPresent() && registryDTO.get().getDockerConfig() != null) {
                    return mapAndGetDockerRepo(registryDTO.get().getDockerConfig(), appDockerRepo);
                }
            }
        }
        return null;
    }

    private String mapAndGetDockerRepo(DockerDTO dockerDTO, String repoName) {

        switch (repoName) {
            case "snapshotUri":
                return dockerDTO.getSnapshotUri();

            case "stagingUri":
                return dockerDTO.getStagingUri();

            case "releaseUri":
                return dockerDTO.getReleaseUri();

            case "groupUri":
                return dockerDTO.getGroupUri();

            default:
                return null;
        }
    }


    private String mapAndGetMavenRepo(MavenDTO mavenDTO, String repoName) {
        switch (repoName) {
            case "targetSnapshot":
                return mavenDTO.getTargetSnapshot();

            case "targetStaging":
                return mavenDTO.getTargetStaging();

            case "targetRelease":
                return mavenDTO.getTargetRelease();

            case "snapshotGroup":
                return mavenDTO.getSnapshotGroup();

            case "releaseGroup":
                return mavenDTO.getReleaseGroup();

            default:
                return null;
        }
    }


}
