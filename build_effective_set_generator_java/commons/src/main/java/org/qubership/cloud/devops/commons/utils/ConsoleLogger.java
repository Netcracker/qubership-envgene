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

package org.qubership.cloud.devops.commons.utils;

import lombok.extern.slf4j.Slf4j;


@Slf4j
public class ConsoleLogger {
    private static final String RED = "\u001B[31m"; // Red color for errors
    private static final String YELLOW = "\u001B[33m"; // Yellow for warnings
    private static final String GREEN = "\u001B[32m"; // Green for success
    private static final String RESET = "\u001B[0m"; // Reset color

    public static void logError(String message) {
        log.error(RED + "ERROR: " + message + RESET);
    }

    public static void logWarning(String message) {
        log.warn(YELLOW + "WARNING: " + message + RESET);
    }

    public static void logSuccess(String message) {
        log.info(GREEN + "SUCCESS: " + message + RESET);
    }

    public static void logInfo(String message) {
        log.info(RESET + "INFO: " + message + RESET);
    }
}

