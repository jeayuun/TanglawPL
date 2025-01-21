#######################################
#              CONSTANTS              #
#######################################

DIGITS = '0123456789'
LOWERCASE_LETTERS = 'abcdefghijklmnopqrstuvwxyz'
UPPERCASE_LETTERS = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
ALPHABETS = LOWERCASE_LETTERS + UPPERCASE_LETTERS
SYMBOLS = "+-*/%|:&=<>!@#$~`^;,()[]{}"
DATA_TYPES = ['int', 'String', 'char', 'boolean', 'float', 'double', 'long', 'short', 'void', 'byte']
BOOLEAN_VALUES = ['true', 'false']
KEYWORDS = [
    'if', 'else', 'return', 'main', 'case', 'try', 'catch', 'do', 'while',
    'for', 'each', 'import', 'implements', 'switch', 'throw', 'throws',
    'this', 'public', 'protected', 'private', 'new', 'package', 'break',
    'repeat', 'def', 'print', 'input', 'continue', 'default', 'const',
    'extends', 'finally', 'static'
]
RESERVED_WORDS = [
    'fetch', 'areaOf', 'circle', 'cubic', 'distance', 'ft', 'in', 'kg', 'km',
    'l', 'lbs', 'm', 'mg', 'mm', 'perimeterOf', 'repeat', 'sphere', 'sq',
    'triangle', 'rectangle', 'square', 'volumeOf', 'radius', 'circumference',
    'length', 'height', 'width', 'side', 'solve'
]
ARITHMETIC_OPERATORS = ['+', '-', '*', '/', '%', '**']
UNARY_OPERATORS = ['+', '-', '++', '--']
RELATIONAL_OPERATORS = ['<', '>', '<=', '>=', '==', '!=']
ASSIGNMENT_OPERATORS = ['=', '+=', '-=', '*=', '/=', '%=', '~=', '**=', '&=', '`=', '^=', '<<=', '>>=']
LOGICAL_OPERATORS = ['!', '&&', '||']
BITWISE_OPERATORS = ['&', '`', '^', '<<', '>>', '!']
SPECIAL_SYMBOLS = ['|', ':', '`', '\\', '@', '#', '$', '~']
TERMINATING_SYMBOLS = [';']
SEPARATING_SYMBOLS = [',']
WHITESPACE = [' ', '\t', '\n', '\v']
PARENTHESIS = ['(', ')', '[', ']', '{', '}']
UNDERSCORE = ['_']
NOISE_WORDS = ['ant', 'ine']

#######################################
#               ERRORS                #
#######################################

class Error:
    def as_string(self):
        result = f'{self.error_name}: {self.details}\n'
        if self.pos_start and self.pos_end:
            result += (
                f'File {getattr(self.pos_start, "fn", "Unknown")}, '
                f'line {getattr(self.pos_start, "ln", -1) + 1}, '
                f'column {getattr(self.pos_start, "col", -1) + 1}-'
                f'{getattr(self.pos_end, "col", -1)}'
            )
        else:
            result += "Location unknown"
        return result


class IllegalCharError(Error):
    def __init__(self, pos_start, pos_end, details):
        super().__init__(pos_start, pos_end, 'Illegal Character', details)

class UnclosedStringError(Error):
    def __init__(self, pos_start, pos_end):
        super().__init__(pos_start, pos_end, 'Unclosed String Literal', 'String literal was not closed.')

class InvalidNumberError(Error):
    def __init__(self, pos_start, pos_end, details):
        super().__init__(pos_start, pos_end, 'Invalid Number', details)
        self.type = 'ERROR' 

#######################################
#              POSITION               #
#######################################

class Position:
    def __init__(self, idx, ln, col, fn, ftxt):
        self.idx = idx
        self.ln = ln
        self.col = col
        self.fn = fn
        self.ftxt = ftxt

    def advance(self, current_char):
        self.idx += 1
        self.col += 1

        if current_char == '\n':
            self.ln += 1
            self.col = 0

        return self

    def copy(self):
        return Position(self.idx, self.ln, self.col, self.fn, self.ftxt)

#######################################
#               TOKENS                #
#######################################

class Token:
    def __init__(self, type_, value=None, pos_start=None, pos_end=None):
        self.type = type_
        self.value = value

        # Initialize positional attributes
        self.pos_start = pos_start.copy() if pos_start else None
        self.pos_end = pos_end.copy() if pos_end else None

    def __repr__(self):
        if self.value:
            return f'{self.type}: {self.value}'
        return f'{self.type}'

#######################################
#               LEXER                 #
#######################################

class Lexer:
    def __init__(self, fn, text):
        self.fn = fn
        self.text = text
        self.pos = Position(-1, 0, -1, fn, text)
        self.current_char = None
        self.prev_token_type = None  
        self.advance()

    def advance(self):
        self.pos.advance(self.current_char)
        self.current_char = self.text[self.pos.idx] if self.pos.idx < len(self.text) else None

    def make_tokens(self):
        tokens = []

        while self.current_char is not None:
            if self.current_char in WHITESPACE or (self.current_char == '\\' and self.peek() in 'tnv'):
                self.advance()
                if self.current_char == '\\' and self.peek() in 'tnv':
                    self.advance()
                    self.advance()

            elif self.current_char == '#':
                comment_token = self.make_comment()
                if isinstance(comment_token, Error):
                    return [], comment_token

            elif self.current_char in DIGITS or (self.current_char == '-' and self.is_negative_sign()):
                try:
                    tokens.append(self.make_number())
                except InvalidNumberError as e:
                    return [], e

            elif self.current_char in ALPHABETS or self.current_char == '_':
                tokens.append(self.make_identifier_or_keyword())

            elif self.current_char == '"':
                tokens.append(self.make_string())

            elif self.current_char == "'":
                tokens.append(self.make_character())

            elif self.current_char in SYMBOLS:
                tokens.append(self.make_symbol())

            else:
                pos_start = self.pos.copy()
                char = self.current_char
                self.advance()
                return [], IllegalCharError(pos_start, self.pos, f"'{char}'")

        tokens.append(Token('EOF', pos_start=self.pos.copy(), pos_end=self.pos.copy()))  # Ensure EOF token includes positions
        return tokens, None

    def peek(self):
        peek_pos = self.pos.idx + 1
        return self.text[peek_pos] if peek_pos < len(self.text) else None

    def is_negative_sign(self):
        if self.prev_token_type in ['REAL_NUMBER', 'INTEGER', 'IDENTIFIER', 'CLOSING_PARENTHESIS']:
            return False
        return True

    def make_number(self):
        num_str = ''
        has_decimal = False
        pos_start = self.pos.copy()

        if self.current_char == '-' or self.current_char == '+':  
            num_str += self.current_char
            self.advance()

        while self.current_char is not None and self.current_char in DIGITS + '.':
            if self.current_char == '.':
                if has_decimal:
                    return InvalidNumberError(pos_start, self.pos.copy(), f"Invalid number '{num_str + self.current_char}'")
                has_decimal = True
            num_str += self.current_char
            self.advance()

        if self.current_char is not None and self.current_char in ALPHABETS + '_':
            invalid_token = num_str + self.current_char
            self.advance()
            while self.current_char is not None and (self.current_char in ALPHABETS + DIGITS + '_'):
                invalid_token += self.current_char
                self.advance()
            return IllegalCharError(pos_start, self.pos.copy(), f"Invalid number or identifier '{invalid_token}'")

        try:
            if has_decimal:
                token = Token('REAL_NUMBER', float(num_str), pos_start, self.pos.copy())
            else:
                token = Token('INTEGER', int(num_str), pos_start, self.pos.copy())
            self.prev_token_type = token.type  
            return token
        except ValueError:
            return InvalidNumberError(pos_start, self.pos.copy(), f"Invalid number '{num_str}'")


    def make_identifier_or_keyword(self):
        id_str = ''
        pos_start = self.pos.copy()

        if self.current_char is not None and self.current_char in ALPHABETS:
            id_str += self.current_char
            self.advance()
        else:
            pos_end = self.pos.copy()
            return IllegalCharError(pos_start, pos_end, 
                f"Invalid identifier '{id_str}' (Identifiers must begin with a letter).")

        while self.current_char is not None and self.current_char not in set(WHITESPACE).union(set(SYMBOLS)):
            id_str += self.current_char
            self.advance()
        
        if not all(char in ALPHABETS + DIGITS + '_' for char in id_str):
            return IllegalCharError(pos_start, self.pos.copy(), 
                f"Invalid identifier '{id_str}' (Identifiers can only include letters, digits, and underscores).")

        if id_str in DATA_TYPES:
            return Token('DATA_TYPE', id_str, pos_start, self.pos.copy())
        elif id_str in BOOLEAN_VALUES:
            return Token('BOOLEAN', id_str, pos_start, self.pos.copy())
        elif id_str in KEYWORDS:
            return Token('KEYWORD', id_str, pos_start, self.pos.copy())
        elif id_str in RESERVED_WORDS:
            return Token('RESERVED_WORDS', id_str, pos_start, self.pos.copy())
        else:
            return Token('IDENTIFIER', id_str, pos_start, self.pos.copy())

    def make_string(self):
        str_val = ''
        pos_start = self.pos.copy()
        self.advance()  

        while self.current_char is not None:
            if self.current_char == '\\':  
                self.advance()
                escape_chars = {
                    'n': '\n', 't': '\t', '"': '"', "'": "'", '\\': '\\'
                }
                str_val += escape_chars.get(self.current_char, self.current_char)
            elif self.current_char == '"': 
                self.advance()
                return Token('STRING_LITERAL', str_val, pos_start, self.pos.copy())
            else:
                str_val += self.current_char
            self.advance()

        return UnclosedStringError(pos_start, self.pos.copy())

    def make_character(self):
        pos_start = self.pos.copy()
        self.advance()  

        if self.current_char is None or self.current_char == "'":
            return IllegalCharError(pos_start, self.pos, "Empty character literal")

        char_val = self.current_char  

        self.advance()  
        if self.current_char != "'":  
            return IllegalCharError(pos_start, self.pos, "Unclosed character literal")

        self.advance() 
        return Token('CHARACTER_LITERAL', char_val, pos_start, self.pos.copy())

    def make_symbol(self):
        pos_start = self.pos.copy()
        symbol_str = self.current_char
        self.advance()

        if symbol_str == '+' or symbol_str == '-':
            if self.current_char == symbol_str: 
                symbol_str += self.current_char
                self.advance()

        while self.current_char is not None and (symbol_str + self.current_char) in (
            ARITHMETIC_OPERATORS + RELATIONAL_OPERATORS + ASSIGNMENT_OPERATORS +
            BITWISE_OPERATORS + LOGICAL_OPERATORS + UNARY_OPERATORS
        ):
            symbol_str += self.current_char
            self.advance()

        token_type = (
            'UNARY_OPERATOR' if symbol_str in ['++', '--'] else
            'ARITHMETIC_OPERATOR' if symbol_str in ARITHMETIC_OPERATORS else
            'RELATIONAL_OPERATOR' if symbol_str in RELATIONAL_OPERATORS else
            'ASSIGNMENT_OPERATOR' if symbol_str in ASSIGNMENT_OPERATORS else
            'BITWISE_OPERATOR' if symbol_str in BITWISE_OPERATORS else
            'LOGICAL_OPERATOR' if symbol_str in LOGICAL_OPERATORS else
            'SPECIAL_SYMBOL' if symbol_str in SPECIAL_SYMBOLS else
            'TERMINATING_SYMBOL' if symbol_str in TERMINATING_SYMBOLS else
            'SEPARATING_SYMBOL' if symbol_str in SEPARATING_SYMBOLS else
            'PARENTHESIS' if symbol_str in PARENTHESIS else
            None
        )

        if token_type:
            return Token(token_type, symbol_str, pos_start, self.pos.copy())
        else:
            return IllegalCharError(pos_start, self.pos.copy(), f"Unknown symbol '{symbol_str}'")

    def make_comment(self):
        pos_start = self.pos.copy()

        if self.text[self.pos.idx:self.pos.idx+2] == '##':
            comment_text = ''
            self.advance()
            self.advance()
            while self.current_char is not None:
                if self.text[self.pos.idx:self.pos.idx+2] == '##':
                    self.advance()
                    self.advance()
                    return Token('COMMENT', comment_text.strip(), pos_start, self.pos.copy())
                comment_text += self.current_char
                self.advance()
            return UnclosedStringError(pos_start, self.pos)

        elif self.text[self.pos.idx:self.pos.idx+1] == '#':
            comment_text = ''
            self.advance()  
            while self.current_char is not None and self.current_char != '#':
                comment_text += self.current_char
                self.advance()
            if self.current_char == '#':
                self.advance()  
                return Token('COMMENT', comment_text.strip(), pos_start, self.pos.copy())
            return UnclosedStringError(pos_start, self.pos, "Unclosed single-line comment")

        else:
            char = self.current_char
            self.advance()
            return IllegalCharError(pos_start, self.pos, f"Unexpected character '{char}' after '#'")

    def skip_comment(self):
        if self.text[self.pos.idx:self.pos.idx+2] == '##':
            self.advance()
            self.advance()
            while self.current_char is not None and self.text[self.pos.idx:self.pos.idx+2] != '##':
                self.advance()
            self.advance()  
            self.advance()
        else:
            while self.current_char is not None and self.current_char != '\n':
                self.advance()

#######################################
# VALIDATE IN PARSER
#######################################

class Parser:
    def advance(self):
        self.current_token_index += 1
        if self.current_token_index < len(self.tokens):
            self.current_token = self.tokens[self.current_token_index]
            if not self.current_token.pos_start or not self.current_token.pos_end:
                raise AttributeError(
                    f"Token {self.current_token} is missing pos_start or pos_end attributes"
                )
        return self.current_token

    def parse(self):
        result = self.expr()
        if not result.error and self.current_token.type != 'EOF':
            return result.failure(InvalidSyntaxError(
                self.current_token.pos_start,
                self.current_token.pos_end,
                "Expected an operator or end of input"
            ))
        return result

#######################################
#                RUN                  #
#######################################

import os
from prettytable import PrettyTable 

def run(fn, text):
    if not fn.endswith('.lit'):
