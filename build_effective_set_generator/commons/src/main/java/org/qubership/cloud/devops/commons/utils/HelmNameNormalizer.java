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

import java.util.ArrayList;
import java.util.List;

public class HelmNameNormalizer {

    private static final String ENCODE_SYMBOLS = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ";

    public static String normalize(String name, String originalNamespace) {
        int limit = 63-originalNamespace.length()-1;
        return normalizeNameForHelm(name, limit);
    }


    private static String normalizeNameForHelm(String name, int limit) {
        String lowerName = name.toLowerCase();

        if (lowerName.equals(name)) {
            // Optional check: if (lowerName.length() < limit) { ... }
            return lowerName.replace('_', '-');
        }

        // Create binary mask
        StringBuilder mask = new StringBuilder("0");
        for (int i = 0; i < lowerName.length(); i++) {
            mask.append(lowerName.charAt(i) != name.charAt(i) ? '1' : '0');
        }

        // Convert binary mask to decimal
        int decimalMask = Integer.parseInt(mask.toString(), 2);

        // Encode decimal mask in base-36 using custom symbols
        List<Integer> base36Digits = numberToBase(decimalMask, 36);
        StringBuilder encodedMask = new StringBuilder();
        for (int index : base36Digits) {
            encodedMask.append(ENCODE_SYMBOLS.charAt(index));
        }

        // Final name
        String finalName = lowerName.replace('_', '-') + "-" + encodedMask.toString();
        if (finalName.length() >= limit) {
            return normalizeNameForHelm(name.substring(0, name.length() - 1), limit);
        }

        return finalName;
    }

    private static List<Integer> numberToBase(int number, int base) {
        List<Integer> digits = new ArrayList<>();
        if (number == 0) {
            digits.add(0);
            return digits;
        }
        while (number > 0) {
            digits.add(0, number % base);
            number /= base;
        }
        return digits;
    }

}
