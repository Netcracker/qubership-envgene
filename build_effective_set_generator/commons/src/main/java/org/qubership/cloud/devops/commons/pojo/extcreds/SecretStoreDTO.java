package org.qubership.cloud.devops.commons.pojo.extcreds;

import lombok.Builder;
import lombok.Data;
import lombok.extern.jackson.Jacksonized;

@Data
@Builder
@Jacksonized
public class SecretStoreDTO {
    private SecretStoreType type;
    private String url;
    private String mountPath; // Required when type is VAULT
    private String vaultName; // Required when type is AZURE
    private String region; // Required when type is AWS
    private String projectId;
}
