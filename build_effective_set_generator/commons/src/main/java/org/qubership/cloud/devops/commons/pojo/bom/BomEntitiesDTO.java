package org.qubership.cloud.devops.commons.pojo.bom;

import lombok.Builder;
import lombok.Data;
import com.fasterxml.jackson.annotation.JsonIgnoreProperties;

import java.util.List;

@Data
@Builder
@JsonIgnoreProperties(ignoreUnknown = true)
public class BomEntitiesDTO {

    List<ServiceBomDTO> services;
    List<ConfigDTO> smartlugs;
    List<ConfigDTO> configs;
    List<ConfigDTO> frontEnds;

}
