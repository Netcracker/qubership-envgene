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

package org.qubership.cloud.devops.cli.pojo.dto.input;


import jakarta.enterprise.context.ApplicationScoped;
import lombok.Builder;
import lombok.Getter;
import lombok.Setter;
import org.qubership.cloud.devops.cli.pojo.dto.sd.SolutionBomDTO;
import org.qubership.cloud.devops.commons.pojo.bg.BgDomainEntityDTO;
import org.qubership.cloud.devops.commons.pojo.clouds.dto.CloudDTO;
import org.qubership.cloud.devops.commons.pojo.consumer.ConsumerDTO;
import org.qubership.cloud.devops.commons.pojo.credentials.dto.CredentialDTO;
import org.qubership.cloud.devops.commons.pojo.cs.CompositeStructureDTO;
import org.qubership.cloud.devops.commons.pojo.namespaces.dto.NamespaceDTO;
import org.qubership.cloud.devops.commons.pojo.profile.dto.ProfileFullDto;
import org.qubership.cloud.devops.commons.pojo.registries.dto.RegistryDTO;
import org.qubership.cloud.devops.commons.pojo.tenants.dto.TenantDTO;

import java.util.Collections;
import java.util.Map;
import java.util.Optional;

@Getter
@Setter
@ApplicationScoped
public class InputData {

    private TenantDTO tenantDTO;
    private CloudDTO cloudDTO;
    private CompositeStructureDTO compositeStructureDTO;
    private BgDomainEntityDTO bgDomainEntityDTO;
    @Builder.Default
    private Map<String, ConsumerDTO> consumerDTOMap = Collections.emptyMap();
    @Builder.Default
    private Map<String, NamespaceDTO> namespaceDTOMap = Collections.emptyMap();
    @Builder.Default
    private Map<String, CredentialDTO> credentialDTOMap = Collections.emptyMap();
    @Builder.Default
    private Map<String, ProfileFullDto> profileFullDtoMap = Collections.emptyMap();
    @Builder.Default
    private Map<String, RegistryDTO> registryDTOMap = Collections.emptyMap();
    private Optional<SolutionBomDTO> solutionBomDTO = Optional.empty();
    @Builder.Default
    private Map<String, Object> clusterMap = Collections.emptyMap();
}
