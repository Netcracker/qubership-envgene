lexer grammar ParameterLexer;

LINE_COMMENT: '//' .*? '\n' -> skip ;
BLOCK_COMMENT: '/*' .*? '*/' -> skip ;
NL: '\r'? '\n' ;

GSTRING_START: DQ_STRING_ELEMENT*? '$' -> pushMode(GSTRING_MODE), pushMode(GSTRING_TYPE_SELECTOR_MODE) ;
OTHER: (ESC_SEQUENCE | ~'$' )+ ;

mode GSTRING_MODE ;
    GSTRING_PART: '$' -> pushMode(GSTRING_TYPE_SELECTOR_MODE) ;
    GSTRING_ELEMENT: (ESC_SEQUENCE | ~('$')) -> more ;

mode GSTRING_TYPE_SELECTOR_MODE ;
    GSTRING_BRACE_L: '{' -> type(LCURVE), popMode, pushMode(D_MODE) ;
    GSTRING_ID: [A-Za-z_][A-Za-z0-9_]* -> type(IDENTIFIER), popMode, pushMode(GSTRING_PATH) ;
    OTHER_PART: NON_GSTRING_SYMBOL -> type(NON_GSTRING_SYMBOL), popMode, popMode;

mode GSTRING_PATH ;
    GSTRING_PATH_PART: '.' [A-Za-z_][A-Za-z0-9_]*;
    ROLLBACK_ONE: . -> popMode, channel(HIDDEN) ;

mode D_MODE ;
WS: [ \t]+ -> skip ;
LPAREN: '(' -> pushMode(D_MODE) ;
RPAREN: ')' -> popMode ;
LBRACK: '[' -> pushMode(D_MODE) ;
RBRACK: ']' -> popMode ;
LCURVE: '{' -> pushMode(D_MODE) ;
RCURVE: '}' -> popMode ;

SLASHY_STRING: '/' SLASHY_STRING_ELEMENT*? '/' ;
IDENT_STRING: '"' [A-Za-z_.][A-Za-z0-9_.]* '"' ;
STRING: '"' EXTENDED_DQ_STRING_ELEMENT*? '"'  | '\'' QUOTED_STRING_ELEMENT*? '\'' ;

fragment SLASHY_STRING_ELEMENT: SLASHY_ESCAPE | ~('/') ;
fragment DQ_STRING_ELEMENT: ESC_SEQUENCE | ~('$'|'}') ;
fragment EXTENDED_DQ_STRING_ELEMENT: ESC_SEQUENCE | ~('}') ;
fragment QUOTED_STRING_ELEMENT: ESC_SEQUENCE | ~('\'') ;
fragment SLASHY_ESCAPE: '\\' '/' ;

fragment ESC_SEQUENCE: '\\' [btnfr"'$\\] | OCTAL_ESC_SEQ ;
fragment OCTAL_ESC_SEQ: '\\' [0-3]? [0-7]? [0-7] ;
NON_GSTRING_SYMBOL: (~([A-Za-z_ .(){}+-[]))+ ;
// Numbers
DECIMAL: SIGN? DIGITS ('.' DIGITS EXP_PART? | EXP_PART) DECIMAL_TYPE_MODIFIER? ;
INTEGER: SIGN? (('0x' | '0X') HEX_DIGITS | '0' OCT_DIGITS | DEC_DIGITS) INTEGER_TYPE_MODIFIER? ;

fragment DIGITS: [0-9] | [0-9][0-9_]*[0-9] ;
fragment DEC_DIGITS: [0-9] | [1-9][0-9_]*[0-9] ;
fragment OCT_DIGITS: [0-7] | [0-7][0-7_]*[0-7] ;
fragment HEX_DIGITS: HEX_DIGIT | HEX_DIGIT HEX_DIGIT_WITH_UNDERSCORE* HEX_DIGIT ;
fragment HEX_DIGIT: [0-9abcdefABCDEF] ;
fragment HEX_DIGIT_WITH_UNDERSCORE: [0-9abcdefABCDEF_] ;

fragment SIGN: ('-'|'+') ;
fragment EXP_PART: ([eE] SIGN? [0-9]+) ;

fragment INTEGER_TYPE_MODIFIER: ('G' | 'L' | 'I' | 'g' | 'l' | 'i') ;
fragment DECIMAL_TYPE_MODIFIER: ('G' | 'D' | 'F' | 'g' | 'd' | 'f') ;

RUSHIFT_ASSIGN: '>>>=' ;
RSHIFT_ASSIGN: '>>=' ;
LSHIFT_ASSIGN: '<<=' ;
SPACESHIP: '<=>' ;
ELVIS: '?:' ;
SAFE_DOT: '?.' ;
STAR_DOT: '*.' ;
ATTR_DOT: '.@' ;
RANGE: '..' ;
EQUAL: '==' ;
UNEQUAL: '!=' ;
AND: '&&' ;
OR: '||' ;
PLUS_ASSIGN: '+=' ;
MINUS_ASSIGN: '-=' ;
MULT_ASSIGN: '*=' ;
DIV_ASSIGN: '/=' ;
MOD_ASSIGN: '%=' ;
BAND_ASSIGN: '&=' ;
XOR_ASSIGN: '^=' ;
BOR_ASSIGN: '|=' ;

SEMICOLON: ';' ;
DOT: '.' ;
COMMA: ',' ;
ASSIGN: '=' ;
COLON: ':' ;
PLUS: '+' ;
MINUS: '-' ;
QUESTION: '?' ;
KW_NULL: 'null' ;
KW_TRUE: 'true' ;
KW_FALSE: 'false' ;

KW_IF: 'if' ;
KW_ELSE: 'else' ;

NEW: 'new';

IDENTIFIER: [A-Za-z_$#][A-Za-z0-9_$]* ;
