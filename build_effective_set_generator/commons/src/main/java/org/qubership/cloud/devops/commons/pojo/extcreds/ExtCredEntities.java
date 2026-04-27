package org.qubership.cloud.devops.commons.pojo.extcreds;

import com.fasterxml.jackson.annotation.JsonPropertyOrder;
import lombok.Builder;
import lombok.Data;
import lombok.extern.jackson.Jacksonized;
import org.qubership.cloud.devops.commons.pojo.credentials.dto.CredentialDTO;

import javax.annotation.Nonnull;
import java.util.Map;

@Data
@Builder
@JsonPropertyOrder
@Jacksonized
@Nonnull
public class ExtCredEntities {
    public Map<String, CredentialDTO> extCredentials;
    public Map<String, SecretStoreDTO> secretStores;
    public String refShape;
    public boolean isExternalOnly;
}
