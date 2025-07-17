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

package org.qubership.cloud.devops.gstringtojinjavatranslator.jinjava;

import com.hubspot.jinjava.tree.parse.TokenScannerSymbols;

public class LessThanTokenScannerSymbols extends TokenScannerSymbols {
    char TOKEN_PREFIX = '<';
    char TOKEN_POSTFIX = '>';
    char TOKEN_FIXED = 0;
    char TOKEN_NOTE = '#';
    char TOKEN_TAG = '%';
    char TOKEN_EXPR_START = '<';
    char TOKEN_EXPR_END = '>';
    char TOKEN_NEWLINE = '\n';
    char TOKEN_TRIM = '-';

    public LessThanTokenScannerSymbols() {
    }

    public char getPrefixChar() {
        return this.TOKEN_PREFIX;
    }

    public char getPostfixChar() {
        return this.TOKEN_POSTFIX;
    }

    public char getFixedChar() {
        return this.TOKEN_FIXED;
    }

    public char getNoteChar() {
        return this.TOKEN_NOTE;
    }

    public char getTagChar() {
        return this.TOKEN_TAG;
    }

    public char getExprStartChar() {
        return this.TOKEN_EXPR_START;
    }

    public char getExprEndChar() {
        return this.TOKEN_EXPR_END;
    }

    public char getNewlineChar() {
        return this.TOKEN_NEWLINE;
    }

    public char getTrimChar() {
        return this.TOKEN_TRIM;
    }
}
