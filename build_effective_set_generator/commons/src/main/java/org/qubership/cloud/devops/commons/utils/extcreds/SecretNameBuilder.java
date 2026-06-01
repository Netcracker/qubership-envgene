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

package org.qubership.cloud.devops.commons.utils.extcreds;


import org.apache.commons.codec.digest.DigestUtils;
import org.qubership.cloud.devops.commons.exceptions.ExternalCredProcessingException;
import org.qubership.cloud.devops.commons.pojo.extcreds.SecretStoreType;

import java.util.regex.Pattern;

import static org.qubership.cloud.devops.commons.exceptions.constant.ExternalCredExceptionMessages.*;
import static org.qubership.cloud.devops.commons.utils.constant.ExternalCredConstants.*;

public class SecretNameBuilder {

    public static String buildNormalizedSecretName(String remoteRefPath, String credId, SecretStoreType secretStoreType) {
        if (isNullOrBlank(remoteRefPath) || isNullOrBlank(credId) || secretStoreType == null) {
            throw new ExternalCredProcessingException
                    (String.format(NORMALIZATION_INPUT_ERROR,  remoteRefPath, credId, secretStoreType));
        }
        remoteRefPath = remoteRefPath.trim();
        credId = credId.trim();
        String type = secretStoreType.name();
        if (secretStoreType != SecretStoreType.vault) {
            validateLength(credId, MAX_CRED_ID_LENGTH, CREDID, type);
        }
        switch (secretStoreType) {
            case vault:
                String result = remoteRefPath + "/" + credId;
                validate(result, VAULT_PATTERN, type);
                return result;
            case azure:
                String azurePath = normalizePath(remoteRefPath, AZURE_SEGMENT_MAX, 4, "--");
                String azureResult = azurePath + "--" + credId;

                validate(azureResult, AZURE_PATTERN, type);
                validateLength(azureResult, AZURE_MAX_LENGTH, SECRET_NAME, type);
                return azureResult;
            case aws:
                String awsPath = normalizePath(remoteRefPath, AWS_SEGMENT_MAX, Integer.MAX_VALUE, "/");
                String awsResult = awsPath + "/" + credId;

                validate(awsResult, AWS_PATTERN, type);
                validateLength(awsResult, AWS_MAX_LENGTH, SECRET_NAME, type);
                return awsResult;
            case gcp:
                String gcpPath = normalizePath(remoteRefPath, GCP_SEGMENT_MAX, Integer.MAX_VALUE, "--");
                String gcpResult = gcpPath + "--" + credId;

                validate(gcpResult, GCP_PATTERN, type);
                validateLength(gcpResult, GCP_MAX_LENGTH, SECRET_NAME, type);
                return gcpResult;
            default:
                throw new ExternalCredProcessingException(String.format(
                        UNSUPPORTED_SECRET_TYPE,
                        type, credId, remoteRefPath
                ));
        }
    }

    private static void validate(String input, Pattern pattern, String type) {
        if (!pattern.matcher(input).matches()) {
            throw new ExternalCredProcessingException(String.format(INVALID_CHARACTER, SECRET_NAME, input, type, pattern));
        }
    }

    private static void validateLength(String input, int max, String fieldLabel, String type) {
        int length = input.length();
        if (length > max) {
            throw new ExternalCredProcessingException(String.format(INVALID_LENGTH, fieldLabel, input, type, max, length));
        }
    }

    private static String normalizePath(String path, int maxSegmentLength, int maxSegments, String delimiter) {
        String[] segments = path.split("/");
        StringBuilder result = new StringBuilder();
        for (int i = 0; i < segments.length && i < maxSegments; i++) {
            if (i > 0) result.append(delimiter);
            result.append(truncateSegment(segments[i], maxSegmentLength));
        }
        return result.toString();
    }

    private static String truncateSegment(String segment, int maxLen) {
        if (segment.length() <= maxLen) {
            return segment;
        }
        // rules:
        // Azure: 14 + "-" + 5 hash
        // AWS: 113 + "-" + 5 hash
        // GCP: 47 + "-" + 5 hash
        //prefixLen = totalLength - (dash [which is 1 character] + hash [is 5 characters]).
        int prefixLen = maxLen - 6;
        if (prefixLen <= 0) {
            throw new ExternalCredProcessingException("Invalid maxLen: " + maxLen);
        }
        return segment.substring(0, prefixLen)  + "-" + DigestUtils.sha256Hex(segment).substring(0, 5);
    }
    private static boolean isNullOrBlank(String s) {
        return s == null || s.isBlank();
    }
}

