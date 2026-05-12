parser grammar ParameterParser;

options {
    tokenVocab = ParameterLexer;
}

parameter
    : gstring
    | other
    | nothing
    ;

gstring: gstring_start (gstringPathExpression | gstringExpression) (GSTRING_PART (gstringPathExpression | gstringExpression))* EOF ;
gstring_start: OTHER? (GSTRING_START NON_GSTRING_SYMBOL)* GSTRING_START ;
other: (OTHER | GSTRING_START | NON_GSTRING_SYMBOL)+ ;
nothing: EOF ;

gstringPathExpression: IDENTIFIER (GSTRING_PATH_PART)* ;
gstringExpression: LCURVE expr? RCURVE ;

expr
    : NEW expr #javaExpr
    | KW_IF LPAREN expr RPAREN NL* statementBlock NL* (KW_ELSE NL* statementBlock)? #ifExpression
    | closureExpressionRule #closureExpression
    | expr QUESTION NL* expr NL* COLON NL* expr #ternaryExpression
    | expr ELVIS NL* expr #elvisExpression
    | LBRACK (expr (COMMA expr)*)? RBRACK #listConstructor
    | expr annotationParameter #annotationExpression
    | IDENTIFIER ((LPAREN argumentList? RPAREN)|closureExpressionRule) #simpleCallExpression
    | expr dot=(DOT | SAFE_DOT | STAR_DOT) IDENTIFIER ((LPAREN argumentList? RPAREN)|closureExpressionRule) #methodCallExpression
    | expr dot=(DOT | SAFE_DOT | STAR_DOT | ATTR_DOT) IDENTIFIER #fieldAccessExpression
    | pathExpression closureExpressionRule* #callExpression
    | expr op=(PLUS | MINUS) expr #binaryExpression
    | expr op=(EQUAL | UNEQUAL | SPACESHIP) expr #binaryExpression
    | expr op=AND expr #binaryExpression
    | expr op=OR expr #binaryExpression
    | expr op=(ASSIGN | PLUS_ASSIGN | MINUS_ASSIGN | MULT_ASSIGN | DIV_ASSIGN | MOD_ASSIGN | BAND_ASSIGN | XOR_ASSIGN | BOR_ASSIGN | LSHIFT_ASSIGN | RSHIFT_ASSIGN | RUSHIFT_ASSIGN) expr #binaryExpression
    | IDENT_STRING #literalExpression
    | STRING #literalExpression
    | SLASHY_STRING #literalSlashyStringExpression
    | DECIMAL #literalExpression
    | INTEGER #literalExpression
    | KW_NULL #literalExpression
    | (KW_TRUE | KW_FALSE) #literalExpression
    | IDENTIFIER #literalExpression
    ;

annotationParameter
    : LBRACK (annotationParameter (COMMA annotationParameter)*)? RBRACK #annotationParamArrayExpression
    | LBRACK (annotationParameter RANGE annotationParameter) RBRACK #annotationRangeArrayExpression
    | pathExpression #annotationParam
    | STRING #annotationParam
    | SLASHY_STRING #annotationSlashyStringParam
    | DECIMAL #annotationParam
    | INTEGER #annotationParam
    | KW_NULL #annotationParam
    | (KW_TRUE | KW_FALSE) #annotationParam
    ;

pathExpression: (IDENTIFIER DOT)* (IDENTIFIER|IDENT_STRING) ;
argumentList: argument (COMMA argument)* ;
argument: expr ;
closureExpressionRule: LCURVE  blockStatement? RCURVE ;
blockStatement: (statement | NL | SEMICOLON)+ ;

statement
    : expr #expressionStatement
    | KW_IF LPAREN expr RPAREN NL* statementBlock NL* (KW_ELSE NL* statementBlock)? #ifStatement
    ;

statementBlock
    : LCURVE blockStatement? RCURVE
    | statement ;
