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
import org.qubership.cloud.devops.gstringtojinjavatranslator.ParameterParserBaseListener;
import org.qubership.cloud.devops.gstringtojinjavatranslator.translator.error.TranslationException;

import org.antlr.v4.runtime.ParserRuleContext;
import org.antlr.v4.runtime.tree.ParseTree;
import org.antlr.v4.runtime.tree.ParseTreeProperty;

import java.util.ArrayDeque;
import java.util.Deque;
import java.util.List;

public class ParameterTranslatorListener extends ParameterParserBaseListener {
    private static final String TRANSLATION_ERROR_FORMAT = "Can't translate: %s";
    private final ParseTreeProperty<String> jj = new ParseTreeProperty<>();
    private final Deque<ContextState> contextStack = new ArrayDeque<>();

    public String getJinJava(ParseTree ctx) {
        return jj.get(ctx);
    }

    private void setJinJava(ParseTree ctx, String s) {
        jj.put(ctx, s);
    }

    @Override
    public void exitAnnotationParam(ParameterParser.AnnotationParamContext ctx) {
        setJinJava(ctx, ctx.getText());
    }

    @Override
    public void exitAnnotationRangeArrayExpression(ParameterParser.AnnotationRangeArrayExpressionContext ctx) {
        String jinJavaRangeSlice = String.format("[%s:%s]",
                getJinJava(ctx.annotationParameter(0)),
                increaseStringInt(getJinJava(ctx.annotationParameter(1))));
        setJinJava(ctx, jinJavaRangeSlice);
    }

    private String increaseStringInt(String stringInt) {
        int increasedInt = Integer.parseInt(stringInt);
        return String.valueOf(++increasedInt);
    }

    @Override
    public void exitCallExpression(ParameterParser.CallExpressionContext ctx) {
        setJinJava(ctx, getJinJava(ctx.pathExpression()));
    }

    @Override
    public void exitJavaExpr(ParameterParser.JavaExprContext ctx) {
        contextStack.push(ContextState.JAVA);

        setJinJava(ctx, ctx.NEW() + " " + ctx.expr().getText());
    }

    @Override
    public void exitPathExpression(ParameterParser.PathExpressionContext ctx) {
        if (ctx.IDENTIFIER().isEmpty() && ctx.IDENT_STRING() != null) {
            setJinJava(ctx, ctx.getText());
            return;
        }
        StringBuilder stringBuilder = new StringBuilder(ctx.IDENTIFIER(0).getText());
        for (int i = 1; i < ctx.IDENTIFIER().size(); i++) {
            stringBuilder.append(".");
            stringBuilder.append(ctx.IDENTIFIER(i).getText());
        }
        if (ctx.IDENT_STRING() != null) {
            String str = ctx.IDENT_STRING().getText();
            stringBuilder.append(".");
            stringBuilder.append(str, 1, str.length() - 1);
        }
        setJinJava(ctx, stringBuilder.toString());
    }

    @Override
    public void exitMethodCallExpression(ParameterParser.MethodCallExpressionContext ctx) {
        if (ctx.getText().equals("Math.random()")) {
            setJinJava(ctx, "random()");
            return;
        }

        StringBuilder stringBuilder = new StringBuilder(String.format("%s", getJinJava(ctx.expr())));

        String identifier = ctx.IDENTIFIER().getText();

        switch (identifier) {
            case "get":
                stringBuilder.append(formatStringFromJinJava("[%s]", ctx.argumentList()));
                break;
            case "tokenize":
                stringBuilder.append(formatStringFromJinJava(".split(%s)", ctx.argumentList()));
                break;
            case "gsub":
                stringBuilder.append(formatStringFromJinJava(".replaceAll(%s)", ctx.argumentList()));
                break;
            case "findResult":
                processFindResultMethod(ctx, stringBuilder);
                contextStack.push(ContextState.FIND_RESULT);
                break;
            default:
                processDefaultMethod(ctx, stringBuilder, identifier);
        }

        setJinJava(ctx, stringBuilder.toString());
    }

    @Override
    public void exitIfExpression(ParameterParser.IfExpressionContext ctx) {
        if (ctx.statementBlock().size() == 1) {
            setJinJava(ctx, String.format("%s ? %s : 'null'",
                    getJinJava(ctx.expr()),
                    getJinJava(ctx.statementBlock(0))));
            return;
        }
        throw new TranslationException(String.format(TRANSLATION_ERROR_FORMAT, ctx.getText()));
    }

    @Override public void exitStatementBlock(ParameterParser.StatementBlockContext ctx) {
        setJinJava(ctx, ctx.getText());
    }

    private void processDefaultMethod(
            ParameterParser.MethodCallExpressionContext ctx,
            StringBuilder stringBuilder,
            String identifier) {
        String jinJavaValue;
        if (getJinJava(ctx.argumentList()) == null) {
            jinJavaValue = String.format(".%s()", identifier);
        } else {
            jinJavaValue = String.format(".%s(%s)", identifier, getJinJava(ctx.argumentList()));
        }

        stringBuilder.append(jinJavaValue);
    }

    private void processFindResultMethod(ParameterParser.MethodCallExpressionContext ctx, StringBuilder stringBuilder) {
        if (!contextStack.isEmpty()) {
            switch (contextStack.pop()) {
                case FIRST_ARG_IS_ZERO:
                    stringBuilder.append(" | envPrefix");
                    break;
                case FIRST_ARG_IS_INDEX_OF_IT:
                    stringBuilder.append(" | envSuffix");
                    break;
                default:
                    throw new TranslationException(String.format(TRANSLATION_ERROR_FORMAT, ctx.getText()));
            }
        }
    }

    @Override
    public void exitArgumentList(ParameterParser.ArgumentListContext ctx) {
        StringBuilder stringBuilder = new StringBuilder();

        if (ctx.argument(0) != null) {
            String firstArg = getJinJava(ctx.argument(0));

            updateContextStateWithFirstArg(firstArg);

            stringBuilder.append(firstArg);
            formatListStringFromListAndJinJavaMap(ctx.argument(), stringBuilder);
        }

        setJinJava(ctx, stringBuilder.toString());
    }

    private void updateContextStateWithFirstArg(String firstArg) {
        if (firstArg.equals("0")) {
            contextStack.push(ContextState.FIRST_ARG_IS_ZERO);
        } else if (firstArg.equals("NAMESPACE.indexOf(it) + it.length()")) {
            contextStack.push(ContextState.FIRST_ARG_IS_INDEX_OF_IT);
        }
    }

    @Override
    public void exitArgument(ParameterParser.ArgumentContext ctx) {
        setJinJava(ctx, getJinJava(ctx.expr()));
    }

    @Override
    public void exitLiteralExpression(ParameterParser.LiteralExpressionContext ctx) {
        setJinJava(ctx, ctx.getText());
    }

    @Override
    public void exitBinaryExpression(ParameterParser.BinaryExpressionContext ctx) {
        setJinJava(ctx, String.format("%s %s %s",
                getJinJava(ctx.expr(0)),
                ctx.op.getText(),
                getJinJava(ctx.expr(1))));
    }

    @Override
    public void exitFieldAccessExpression(ParameterParser.FieldAccessExpressionContext ctx) {
        setJinJava(ctx, String.format("%s%s%s",
                getJinJava(ctx.expr()),
                ctx.DOT().getText(),
                ctx.IDENTIFIER().getText()));
    }

    @Override
    public void exitSimpleCallExpression(ParameterParser.SimpleCallExpressionContext ctx) {
        if (ctx.IDENTIFIER().getText().equals("lower")) {
            setJinJava(ctx, String.format("%s | lower", getJinJava(ctx.argumentList())));
        }
    }

    @Override
    public void exitAnnotationExpression(ParameterParser.AnnotationExpressionContext ctx) {
        setJinJava(ctx, getJinJava(ctx.expr()) + getJinJava(ctx.annotationParameter()));
    }

    @Override
    public void exitTernaryExpression(ParameterParser.TernaryExpressionContext ctx) {
        setJinJava(ctx, String.format("%s ? %s : %s",
                getJinJava(ctx.expr(0)),
                getJinJava(ctx.expr(1)),
                getJinJava(ctx.expr(2))));
    }

    @Override
    public void exitAnnotationParamArrayExpression(ParameterParser.AnnotationParamArrayExpressionContext ctx) {
        StringBuilder stringBuilder = new StringBuilder(formatStringFromJinJava("[%s", ctx.annotationParameter(0)));
        formatListStringFromListAndJinJavaMap(ctx.annotationParameter(), stringBuilder);
        stringBuilder.append("]");
        setJinJava(ctx, stringBuilder.toString());
    }

    private String formatStringFromJinJava(String formatString, ParserRuleContext context) {
        return String.format(formatString, getJinJava(context));
    }

    @Override
    public void exitLiteralSlashyStringExpression(ParameterParser.LiteralSlashyStringExpressionContext ctx) {
        setJinJava(ctx, String.format("\"%s\"", removeFirstAndLastCharacter(ctx.getText())));
    }

    @Override
    public void exitAnnotationSlashyStringParam(ParameterParser.AnnotationSlashyStringParamContext ctx) {
        setJinJava(ctx, String.format("\"%s\"", removeFirstAndLastCharacter(ctx.getText())));
    }

    private String removeFirstAndLastCharacter(String text) {
        return text.substring(1, text.length()-1);
    }

    @Override
    public void exitListConstructor(ParameterParser.ListConstructorContext ctx) {
        StringBuilder stringBuilder = new StringBuilder("[");

        if (ctx.expr(0) != null) {
            stringBuilder.append(getJinJava(ctx.expr(0)));
            formatListStringFromListAndJinJavaMap(ctx.expr(), stringBuilder);
        }

        stringBuilder.append("]");
        setJinJava(ctx, stringBuilder.toString());
    }

    private void formatListStringFromListAndJinJavaMap(List<? extends ParseTree> ruleContext, StringBuilder stringBuilder) {
        for (int i = 1; i < ruleContext.size(); i++) {
            stringBuilder.append(",");
            stringBuilder.append(getJinJava(ruleContext.get(i)));
        }
    }

    @Override
    public void exitElvisExpression(ParameterParser.ElvisExpressionContext ctx) {
        String a = getJinJava(ctx.expr(0));
        String b = getJinJava(ctx.expr(1));

        if (!contextStack.isEmpty() && contextStack.pop().equals(ContextState.FIND_RESULT)) {
            setJinJava(ctx, String.format("%s(%s)", a, b));
            return;
        }

        setJinJava(ctx, String.format("%s ? %s : %s", a, a, b));
    }

    @Override
    public void exitGstringExpression(ParameterParser.GstringExpressionContext ctx) {
        setJinJava(ctx, getJinJava(ctx.expr()));
    }

    @Override
    public void exitGstring(ParameterParser.GstringContext ctx) {
        StringBuilder stringBuilder = new StringBuilder(removeLastCharacter(ctx.gstring_start().getText()));

        if (ctx.gstringPathExpression().isEmpty()) {
            for (int i = 0; i < ctx.gstringExpression().size(); i++) {
                stringBuilder.append(String.format("<<%s>>", getJinJava(ctx.gstringExpression(i))));
                if (ctx.GSTRING_PART(i) != null) {
                    stringBuilder.append(removeLastCharacter(ctx.GSTRING_PART(i).getText()));
                }
            }
        } else {
            stringBuilder.append(String.format("<<%s>>", getJinJava(ctx.gstringPathExpression(0))));
        }

        String restText = ctx.EOF().getText();
        if (!restText.equals("<EOF>")) {
            stringBuilder.append(restText);
        }
        setJinJava(ctx, stringBuilder.toString());
    }

    @Override
    public void exitGstringPathExpression(ParameterParser.GstringPathExpressionContext ctx) {
        StringBuilder stringBuilder = new StringBuilder(ctx.IDENTIFIER().getText());
        for (int i = 0; i < ctx.GSTRING_PATH_PART().size(); i++) {
            stringBuilder.append(".");
            stringBuilder.append(getJinJava(ctx.GSTRING_PATH_PART(i)));
        }
        setJinJava(ctx, stringBuilder.toString());
    }

    private String removeLastCharacter(String string) {
        return string.substring(0, string.length() - 1);
    }

    @Override
    public void exitParameter(ParameterParser.ParameterContext ctx) {
        if (isOther(ctx)) {
            setJinJava(ctx, ctx.getText());
        } else if (isNothing(ctx)) {
            setJinJava(ctx, "");
        } else {
            setJinJava(ctx, getJinJava(ctx.gstring()));
        }
    }

    private boolean isOther(ParameterParser.ParameterContext ctx) {
        return ctx.other() != null;
    }

    private  boolean isNothing(ParameterParser.ParameterContext ctx) {
        return ctx.nothing() != null;
    }
}
