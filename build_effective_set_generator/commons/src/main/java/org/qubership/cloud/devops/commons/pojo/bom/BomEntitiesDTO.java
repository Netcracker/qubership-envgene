package org.qubership.cloud.devops.commons.pojo.bom;

import lombok.Builder;
import lombok.Data;

import java.util.List;

@Data
@Builder
public class BomEntitiesDTO {

    List<ServiceBomDTO> services;
    List<ConfigDTO> smartlugs;
    List<ConfigDTO> configs;
    List<ConfigDTO> frontEnds;

}
