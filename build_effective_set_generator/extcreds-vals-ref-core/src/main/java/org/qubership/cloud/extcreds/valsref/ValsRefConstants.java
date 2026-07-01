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

package org.qubership.cloud.extcreds.valsref;

import java.util.regex.Pattern;

final class ValsRefConstants {

    static final String SECRET_NAME = "Final Normalized Secret Name";
    static final String CREDID = "Credential ID";
    static final Pattern VAULT_PATTERN = Pattern.compile("^[a-zA-Z0-9/_-]+$");
    static final Pattern AZURE_PATTERN = Pattern.compile("^[a-zA-Z0-9-]+$");
    static final Pattern AWS_PATTERN = Pattern.compile("^[a-zA-Z0-9\\-/_+=.@!]+$");
    static final Pattern GCP_PATTERN = Pattern.compile("^[a-zA-Z0-9_-]+$");
    static final int MAX_CRED_ID_LENGTH = 32;
    static final int AZURE_MAX_LENGTH = 127;
    static final int AWS_MAX_LENGTH = 512;
    static final int GCP_MAX_LENGTH = 255;
    static final int AZURE_SEGMENT_MAX = 20;
    static final int AWS_SEGMENT_MAX = 119;
    static final int GCP_SEGMENT_MAX = 53;

    private ValsRefConstants() {
    }
}
