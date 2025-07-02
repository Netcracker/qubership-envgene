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

package org.qubership.cloud.devops.gstringtojinjavatranslator.translator.error;

import org.antlr.v4.runtime.DefaultErrorStrategy;
import org.antlr.v4.runtime.InputMismatchException;
import org.antlr.v4.runtime.NoViableAltException;
import org.antlr.v4.runtime.Parser;
import org.antlr.v4.runtime.RecognitionException;

public class ExceptionErrorStrategy extends DefaultErrorStrategy {
    @Override
    public void recover(Parser recognizer, RecognitionException e) {
        throw new TranslationException(e);
    }

    @Override
    public void sync(Parser recognizer) {
        // Make sure we don't attempt to recover from problems in subrules.
    }

    @Override
    public void reportNoViableAlternative(Parser recognizer, NoViableAltException e) {
        String message = "No viable alternative: " + getTokenErrorDisplay(e.getOffendingToken());
        message += " expecting one of " + e.getExpectedTokens().toString(recognizer.getVocabulary());
        handleException(message, recognizer, e);
    }

    @Override
    public void reportInputMismatch(Parser recognizer, InputMismatchException e) {
        String message = "mismatched input "+getTokenErrorDisplay(e.getOffendingToken())+
                " expecting "+e.getExpectedTokens().toString(recognizer.getVocabulary());
        handleException(message, recognizer, e);
    }

    private void handleException(String message,
                                 Parser recognizer,
                                 RecognitionException e) {
        RecognitionException exception = new RecognitionException(message, recognizer, recognizer.getInputStream(), recognizer.getContext());
        e.setStackTrace(new StackTraceElement[]{});
        exception.initCause(e);
        exception.setStackTrace(new StackTraceElement[]{
                new StackTraceElement("Class", "Method", "File",
                        recognizer.getCurrentToken().getLine())
        });
        throw exception;
    }
}
