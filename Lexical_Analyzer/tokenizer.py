#######################################
# CONSTANTS
#######################################

DIGITS = '0123456789'
LOWERCASE_LETTERS = 'abcdefghijklmnopqrstuvwxyz'
UPPERCASE_LETTERS = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
LETTERS = LOWERCASE_LETTERS + UPPERCASE_LETTERS
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
ARITHMETIC_OPERATORS = ['+', '-', '*', '/', '%', '++', '--', '**']
RELATIONAL_OPERATORS = ['<', '>', '<=', '>=', '==', '!=']
ASSIGNMENT_OPERATORS = ['=', '+=', '-=', '*=', '/=', '%=', '~=', '**=', '&=', '`=', '^=', '<<=', '>>=']
BITWISE_OPERATORS = ['&', '`', '^', '<<', '>>']
LOGICAL_OPERATORS = ['!', '&&', '||']
SPECIAL_SYMBOLS = ['|', ':', '`', '\\', '@', '#', '$', '~']
TERMINATING_SYMBOLS = [';']
SEPARATING_SYMBOLS = [',']
WHITESPACE = [' ', '\t', '\n', '\v']
PARENTHESIS = ['(', ')', '[', ']', '{', '}']

#######################################
# ERRORS
#######################################

class Error:
    def __init__(self, pos_start, pos_end, error_name, details):
        self.pos_start = pos_start
        self.pos_end = pos_end
        self.error_name = error_name
        self.details = details
    
    def as_string(self):
        result  = f'{self.error_name}: {self.details}\n'
        result += f'File {self.pos_start.fn}, line {self.pos_start.ln + 1}'
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

#######################################
# POSITION
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
# TOKENS
#######################################

class Token:
    def __init__(self, type_, value=None):
        self.type = type_
        self.value = value
    
    def __repr__(self):
        if self.value: return f'{self.type}:{self.value}'
        return f'{self.type}'

#######################################
# LEXER
#######################################

class Lexer:
    def __init__(self, fn, text):
        self.fn = fn
        self.text = text
        self.pos = Position(-1, 0, -1, fn, text)
        self.current_char = None
        self.prev_token_type = None  # Track the type of the last token
        self.advance()
    
    def advance(self):
        self.pos.advance(self.current_char)
        self.current_char = self.text[self.pos.idx] if self.pos.idx < len(self.text) else None

    def make_tokens(self):
        tokens = []

        while self.current_char is not None:
            if self.current_char in WHITESPACE:
                self.advance()
            elif self.current_char in DIGITS or (self.current_char == '-' and self.is_negative_sign()):
                tokens.append(self.make_number())
            elif self.current_char in LETTERS or self.current_char == '_':
                tokens.append(self.make_identifier_or_keyword())
            elif self.current_char == '"':
                tokens.append(self.make_string())
            elif self.current_char == "'":
                tokens.append(self.make_character())
            elif self.current_char in SYMBOLS:
                tokens.append(self.make_symbol())
            elif self.current_char == '#':  # Comments
                self.skip_comment()
            else:
                pos_start = self.pos.copy()
                char = self.current_char
                self.advance()
                return [], IllegalCharError(pos_start, self.pos, f"'{char}'")
        
        return tokens, None

    def is_negative_sign(self):
        # Determine if '-' is part of a negative number
        if self.prev_token_type in ['REAL_NUMBER', 'SIGNED_INTEGER', 'IDENTIFIER', 'CLOSING_PARENTHESIS']:
            return False
        return True

    def make_number(self):
        num_str = ''
        has_decimal = False
        pos_start = self.pos.copy()

        if self.current_char == '-':  # Handle negative sign
            num_str += self.current_char
            self.advance()

        while self.current_char is not None and (self.current_char in DIGITS or self.current_char == '.'):
            if self.current_char == '.':
                if has_decimal:
                    return InvalidNumberError(pos_start, self.pos, f"Invalid number '{num_str + self.current_char}'")
                has_decimal = True
            num_str += self.current_char
            self.advance()

        try:
            if has_decimal:
                token = Token('REAL_NUMBER', float(num_str))
            else:
                token = Token('SIGNED_INTEGER', int(num_str))
            self.prev_token_type = token.type  # Update previous token type
            return token
        except ValueError:
            return InvalidNumberError(pos_start, self.pos, f"Invalid number '{num_str}'")


    def make_identifier_or_keyword(self):
        id_str = ''
        while self.current_char is not None and (self.current_char in LETTERS + DIGITS + '_'):
            id_str += self.current_char
            self.advance()

        if id_str in DATA_TYPES:
            return Token('DATA_TYPE', id_str)
        elif id_str in BOOLEAN_VALUES:
            return Token('BOOLEAN', id_str)
        elif id_str in KEYWORDS:
            return Token('KEYWORD', id_str)
        elif id_str in RESERVED_WORDS:
            return Token('RESERVED_WORD', id_str)
        else:
            return Token('IDENTIFIER', id_str)

    def make_string(self):
        str_val = ''
        pos_start = self.pos.copy()
        self.advance()  # Skip opening quote

        while self.current_char is not None:
            if self.current_char == '\\':  # Handle escape sequences
                self.advance()
                escape_chars = {
                    'n': '\n', 't': '\t', '"': '"', "'": "'", '\\': '\\'
                }
                str_val += escape_chars.get(self.current_char, self.current_char)
            elif self.current_char == '"':  # Closing quote
                self.advance()
                return Token('STRING_LITERAL', str_val)
            else:
                str_val += self.current_char
            self.advance()

        return UnclosedStringError(pos_start, self.pos)


    def make_character(self):
        pos_start = self.pos.copy()
        self.advance()  # Skip opening single quote
        if self.current_char is None or self.current_char == "'":
            return IllegalCharError(pos_start, self.pos, "Empty character literal")
        
        char_val = self.current_char
        self.advance()

        if self.current_char != "'":
            return IllegalCharError(pos_start, self.pos, "Unclosed character literal")
        
        self.advance()
        return Token('CHARACTER_LITERAL', char_val)

    def make_symbol(self):
        pos_start = self.pos.copy()
        symbol_str = self.current_char
        self.advance()

        while self.current_char is not None and (symbol_str + self.current_char) in (
            ARITHMETIC_OPERATORS + RELATIONAL_OPERATORS + ASSIGNMENT_OPERATORS +
            BITWISE_OPERATORS + LOGICAL_OPERATORS
        ):
            symbol_str += self.current_char
            self.advance()

        if symbol_str == '-':
            token = Token('ARITHMETIC_OPERATOR', symbol_str)
        elif symbol_str in ARITHMETIC_OPERATORS:
            token = Token('ARITHMETIC_OPERATOR', symbol_str)
        elif symbol_str in RELATIONAL_OPERATORS:
            token = Token('RELATIONAL_OPERATOR', symbol_str)
        elif symbol_str in ASSIGNMENT_OPERATORS:
            token = Token('ASSIGNMENT_OPERATOR', symbol_str)
        elif symbol_str in BITWISE_OPERATORS:
            token = Token('BITWISE_OPERATOR', symbol_str)
        elif symbol_str in LOGICAL_OPERATORS:
            token = Token('LOGICAL_OPERATOR', symbol_str)
        elif symbol_str in SPECIAL_SYMBOLS:
            token = Token('SPECIAL_SYMBOL', symbol_str)
        elif symbol_str in TERMINATING_SYMBOLS:
            token = Token('TERMINATING_SYMBOL', symbol_str)
        elif symbol_str in SEPARATING_SYMBOLS:
            token = Token('SEPARATING_SYMBOL', symbol_str)
        elif symbol_str in PARENTHESIS:
            token = Token('PARENTHESIS', symbol_str)
        else:
            return IllegalCharError(pos_start, self.pos, f"Unknown symbol '{symbol_str}'")

        self.prev_token_type = token.type  # Update previous token type
        return token



    def skip_comment(self):
        if self.text[self.pos.idx:self.pos.idx+2] == '##':
            self.advance()
            self.advance()
            while self.current_char is not None and self.text[self.pos.idx:self.pos.idx+2] != '##':
                self.advance()
            self.advance()  # Skip ##
            self.advance()
        else:
            while self.current_char is not None and self.current_char != '\n':
                self.advance()

#######################################
# RUN
#######################################

def run(fn, text):
    lexer = Lexer(fn, text)
    tokens, error = lexer.make_tokens()

    if error:
        return [], error.as_string()
    return tokens, None