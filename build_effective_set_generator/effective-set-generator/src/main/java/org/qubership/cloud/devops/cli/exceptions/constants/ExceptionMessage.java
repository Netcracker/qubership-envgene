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

package org.qubership.cloud.devops.cli.exceptions.constants;

public class ExceptionMessage {
    public static final String APP_PARSE_ERROR = "Parsing of application %s from namespace %s failed due to: %s";
    public static final String FILE_READ_ERROR = "Error Reading the file %s due to %s";

    public static final String EFFECTIVE_SET_FAILED = "Generation of effective set failed as %s";

    public static final String REGISTRY_EXTRACT_FAILED = "Could not extract registry information from Application Bom for %s";

    public static final String APP_PROCESS_FAILED = "Failed to process application %s from namespace %s \n Reason: %s";
}
