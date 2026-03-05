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

package org.qubership.cloud.devops.gstringtojinjavatranslator.translator;

import org.qubership.cloud.devops.gstringtojinjavatranslator.ParameterParser;
import org.qubership.cloud.devops.gstringtojinjavatranslator.translator.error.ExceptionErrorStrategy;
import org.qubership.cloud.devops.gstringtojinjavatranslator.translator.error.ExceptionStrategyLexer;
import org.qubership.cloud.devops.gstringtojinjavatranslator.translator.error.TranslationException;

import org.antlr.v4.runtime.CharStreams;
import org.antlr.v4.runtime.CommonTokenStream;
import org.antlr.v4.runtime.tree.ParseTree;
import org.antlr.v4.runtime.tree.ParseTreeWalker;

public class GStringToJinJavaTranslator implements Translator {
    public String translate(String text) throws TranslationException {
        return translate(prepareParameterParser(text));
    }

    private String translate(ParameterParser parser) {
        ParseTree tree = parser.parameter();
        ParseTreeWalker walker = new ParseTreeWalker();
        ParameterTranslatorListener translator = new ParameterTranslatorListener();
        walker.walk(translator, tree);
        return translator.getJinJava(tree);
    }

    private ParameterParser prepareParameterParser(String text) {
        ParameterParser parser = new ParameterParser(
                new CommonTokenStream(new ExceptionStrategyLexer(CharStreams.fromString(text))));
        parser.setBuildParseTree(true);
        parser.setErrorHandler(new ExceptionErrorStrategy());
        return parser;
    }
}
