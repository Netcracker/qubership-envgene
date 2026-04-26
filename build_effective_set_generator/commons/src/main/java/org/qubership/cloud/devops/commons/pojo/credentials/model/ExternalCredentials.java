package org.qubership.cloud.devops.commons.pojo.credentials.model;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;
import org.qubership.cloud.devops.commons.pojo.credentials.dto.CredentialDTO;

import java.util.List;

@Data
@NoArgsConstructor
@AllArgsConstructor
public class ExternalCredentials implements Credential {
    private  Boolean create;
    private  String secretStore;
    private  List<CredentialDTO.Property> properties;
    private  String remoteRefPath;
}
