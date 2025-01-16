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
    'repeat', 'def', 'print', 'println', 'input', 'continue', 'default', 'const',
    'extends', 'finally', 'static', 'class'
]
RESERVED_WORDS = [
    'fetch', 'areaOf', 'circle', 'cubic', 'distance', 'ft', 'in', 'kg', 'km',
    'l', 'lbs', 'm', 'mg', 'mm', 'perimeterOf', 'repeat', 'sphere', 'sq',
    'triangle', 'rectangle', 'square', 'volumeOf', 'radius', 'circumference',
    'length', 'height', 'width', 'side', 'setprecision', 'cm', 'base', 'cube', 
]
ARITHMETIC_OPERATORS = ['+', '-', '*', '/', '%', '**']
UNARY_OPERATORS = ['+', '-', '++', '--']
RELATIONAL_OPERATORS = ['<', '>', '<=', '>=', '==', '!=']
ASSIGNMENT_OPERATORS = ['=', '+=', '-=', '*=', '/=', '%=', '~=', '**=', '&=', '`=', '^=', '<<=', '>>=']
LOGICAL_OPERATORS = ['!', '&&', '||']
BITWISE_OPERATORS = ['&', '`', '^', '<<', '>>', '~']
SPECIAL_SYMBOLS = ['|', ':', '`', '\\', '@', '#', '$', '~', '"', "'", '']
ACCESSOR_SYMBOL = ['.']
TERMINATING_SYMBOLS = [';']
SEPARATING_SYMBOLS = [',']
WHITESPACE = [' ', '\t', '\n', '\v']
PARENTHESIS = ['(', ')', '[', ']', '{', '}']
UNDERSCORE = ['_']
NOISE_WORDS = ['ant', 'ine', 'eger', 'acter']

NOISE_WORD_RULES = {
    'constant': 'const',
    'const': 'const',  
    'integer': 'int',
    'int': 'int',    
    'character': 'char',
    'char': 'char',      
    'define': 'def',
    'def': 'def'      
}
CONSTANTS = {
    '0': 'INTEGER',
    '3.14': 'FLOAT',
    '2.718281828459045': 'DOUBLE',
    '"infinity"': 'STRING_LITERAL',
    "'i'": 'CHARACTER_LITERAL',
    'true': 'BOOLEAN'
}

#######################################
#               ERRORS                #
#######################################

class Error:
    def __init__(self, pos_start, pos_end, error_name, details):
        self.pos_start = pos_start
        self.pos_end = pos_end
        self.error_name = error_name
        self.details = details

    def as_string(self):
        result = f'{self.error_name}: {self.details}\n'
        result += f'File {self.pos_start.fn}, line {self.pos_start.ln + 1}, column {self.pos_start.col + 1}-{self.pos_end.col + 1}'
        return result

class IllegalCharError(Error):
    def __init__(self, pos_start, pos_end, illegal_char):
        super().__init__(pos_start, pos_end, 'Illegal Character', f"'{illegal_char}' is not allowed.")


class UnclosedStringError(Error):
    def __init__(self, pos_start, pos_end):
        super().__init__(pos_start, pos_end, 'Unclosed String Literal', 'String literal was not closed.')


class InvalidNumberError(Error):
    def __init__(self, pos_start, pos_end, details):
        super().__init__(pos_start, pos_end, 'Invalid Number', details)

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
    def __init__(self, type_, value=None):
        self.type = type_
        self.value = value
    
    def __repr__(self):
        if self.value: return f'{self.type}: {self.value}'
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
        errors = []

        while self.current_char is not None:
            if self.current_char in WHITESPACE or (self.current_char == '\\' and self.peek() in 'tnv'):
                self.advance()

            elif self.current_char in CONSTANTS.keys():  
                const_value = self.match_constant()
                if const_value:
                    tokens.append(Token(CONSTANTS[const_value], const_value))
                    continue

            elif self.current_char == '#': 
                comment_token = self.make_comment()
                if isinstance(comment_token, Error):
                    errors.append(comment_token)
                else:
                    tokens.append(comment_token)

            elif self.current_char in SYMBOLS:  
                token_or_error = self.make_symbol()
                if isinstance(token_or_error, Error):
                    errors.append(token_or_error)
                else:
                    tokens.append(token_or_error)

            elif self.current_char in DIGITS or (self.current_char == '-' and self.is_negative_sign()):
                token_or_error = self.make_number()
                if isinstance(token_or_error, Error):
                    errors.append(token_or_error)
                else:
                    tokens.append(token_or_error)

            elif self.current_char in ALPHABETS or self.current_char == '_':  
                token_or_tokens = self.make_identifier_or_keyword()
                if isinstance(token_or_tokens, list): 
                    tokens.extend(token_or_tokens)  
                elif isinstance(token_or_tokens, Error):
                    errors.append(token_or_tokens)
                else:
                    tokens.append(token_or_tokens)

            elif self.current_char == '"':  
                tokens_or_error = self.make_string()
                if isinstance(tokens_or_error, Error): 
                    errors.append(tokens_or_error)
                else:
                    tokens.extend(tokens_or_error)  

            elif self.current_char == "'":  
                token_or_error = self.make_character()
                if isinstance(token_or_error, Error):
                    errors.append(token_or_error)
                else:
                    tokens.append(token_or_error)

            else: 
                pos_start = self.pos.copy()
                char = self.current_char
                self.advance()
                errors.append(IllegalCharError(pos_start, self.pos, char))

        return tokens, errors

    def match_constant(self):
        """Matches predefined constants."""
        for const in CONSTANTS.keys():
            if self.text[self.pos.idx:self.pos.idx + len(const)] == const:
                self.advance_by(len(const))
                return const
        return None

    def advance_by(self, count):
        """Advances the position by a specific count."""
        for _ in range(count):
            self.advance()

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
                    return InvalidNumberError(pos_start, self.pos, f"Invalid number '{num_str}'. Multiple decimal points detected.")
                has_decimal = True
            num_str += self.current_char
            self.advance()

        if self.current_char is not None and self.current_char in ALPHABETS + '_':
            while self.current_char is not None and self.current_char in ALPHABETS + '_':
                num_str += self.current_char
                self.advance()
            return InvalidNumberError(pos_start, self.pos, f"Invalid number '{num_str}'. Numbers cannot contain alphabetic characters.")

        try:
            if has_decimal:
                real_number = float(num_str)
                if abs(real_number) <= 3.4e38:  
                    token = Token('FLOAT', real_number)
                else:
                    token = Token('DOUBLE', real_number)
            else:
                integer_number = int(num_str)
                if -32768 <= integer_number <= 32767: 
                    token = Token('INTEGER', integer_number)
                else:
                    token = Token('LONG', integer_number)

            self.prev_token_type = token.type  
            return token
        except ValueError:
            return InvalidNumberError(pos_start, self.pos, f"Invalid number '{num_str}'")


    def make_identifier_or_keyword(self):
        id_str = ''
        pos_start = self.pos.copy()

        if self.current_char is None or self.current_char not in ALPHABETS:
            while self.current_char is not None and self.current_char in ALPHABETS + DIGITS + '_':
                id_str += self.current_char
                self.advance()
            pos_end = self.pos.copy()
            return IllegalCharError(pos_start, pos_end, 
                                    f"Invalid identifier '{id_str}' (Identifiers must begin with a letter).")
   
        while self.current_char is not None and (
            self.current_char in ALPHABETS + DIGITS + '_' or self.current_char == '.'):
            if self.current_char == '.':
                if id_str in RESERVED_WORDS or id_str in KEYWORDS:
                    token = Token('RESERVED_WORD', id_str)
                else:
                    token = Token('IDENTIFIER', id_str)
                self.prev_token_type = token.type
                self.advance()
                return [token, Token('ACCESSOR_SYMBOL', '.')]  
            id_str += self.current_char
            self.advance()

        normalized = NOISE_WORD_RULES.get(id_str, id_str)

        if normalized in DATA_TYPES:
            return Token('DATA_TYPE', normalized)
        elif normalized in BOOLEAN_VALUES:
            return Token('BOOLEAN', normalized)
        elif normalized in KEYWORDS:
            return Token('KEYWORD', normalized)
        elif normalized in RESERVED_WORDS:
            return Token('RESERVED_WORD', normalized)
        elif normalized in NOISE_WORDS:
            return Token('NOISE_WORD', normalized)
        else:
            return Token('IDENTIFIER', normalized)
    
    def make_tokens(self):
        tokens = []
        errors = []

        while self.current_char is not None:
            if self.current_char in WHITESPACE or (self.current_char == '\\' and self.peek() in 'tnv'):
                self.advance()

            elif self.current_char == '#':
                comment_token = self.make_comment()
                if isinstance(comment_token, Error):
                    errors.append(comment_token)
                else:
                    tokens.append(comment_token)

            elif self.current_char in SYMBOLS:
                token_or_error = self.make_symbol()
                if isinstance(token_or_error, Error):
                    errors.append(token_or_error)
                else:
                    tokens.append(token_or_error)

            elif self.current_char in DIGITS or (self.current_char == '-' and self.is_negative_sign()):
                token_or_error = self.make_number()
                if isinstance(token_or_error, Error):
                    errors.append(token_or_error)
                else:
                    tokens.append(token_or_error)

            elif self.current_char in ALPHABETS or self.current_char == '_':
                token_or_tokens = self.make_identifier_or_keyword()
                if isinstance(token_or_tokens, list):
                    tokens.extend(token_or_tokens)
                elif isinstance(token_or_tokens, Error):
                    errors.append(token_or_tokens)
                else:
                    tokens.append(token_or_tokens)

            elif self.current_char == '"':
                tokens_or_error = self.make_string()  
                if isinstance(tokens_or_error, Error): 
                    errors.append(tokens_or_error)
                else:
                    tokens.extend(tokens_or_error) 

            elif self.current_char == "'":
                token = self.make_character()
                if isinstance(token, Error):
                    errors.append(token)
                else:
                    tokens.append(token)

            else:
                pos_start = self.pos.copy()
                char = self.current_char
                self.advance()
                errors.append(IllegalCharError(pos_start, self.pos, char))

        return tokens, errors
    
    def make_string(self):
        str_val = ''
        pos_start = self.pos.copy()
        tokens = []
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
                if str_val:  
                    tokens.append(Token('STRING_LITERAL', str_val))
                return tokens
            elif self.current_char == '{': 
                if str_val: 
                    tokens.append(Token('STRING_LITERAL', str_val))
                    str_val = ''
                tokens.append(Token('PARENTHESIS', '{'))
                self.advance()  
                embedded_val = ''
                while self.current_char is not None and self.current_char != '}':
                    embedded_val += self.current_char
                    self.advance()
                if self.current_char == '}': 
                    tokens.append(Token('IDENTIFIER', embedded_val.strip()))  
                    tokens.append(Token('PARENTHESIS', '}'))  
                    self.advance()
                else:
                    return UnclosedStringError(pos_start, self.pos)  
            else:
                str_val += self.current_char  
            self.advance()

        if str_val:  
            tokens.append(Token('STRING_LITERAL', str_val))
        return tokens

    def make_character(self):
        pos_start = self.pos.copy()
        self.advance() 

        if self.current_char is None or self.current_char == "'":
            self.advance() 
            return IllegalCharError(
                pos_start,
                self.pos,
                "Character literal is empty. A character literal must contain exactly one character."
            )

        char_val = self.current_char
        self.advance()  

        if self.current_char != "'":
            if self.current_char is not None:
                char_val += self.current_char 
                self.advance()

            if self.current_char != "'":
                while self.current_char is not None and self.current_char != "'":
                    self.advance()
                return IllegalCharError(
                    pos_start,
                    self.pos,
                    f"Unclosed character literal starting with '{char_val}'."
                )
            else:
                self.advance()  
                return IllegalCharError(
                    pos_start,
                    self.pos,
                    f"Character literal '{char_val}' is invalid. A character literal must contain exactly one character."
                )

        self.advance()  
        return Token('CHARACTER_LITERAL', char_val)

    def make_symbol(self):
        pos_start = self.pos.copy()
        symbol_str = self.current_char
        self.advance()

        while self.current_char is not None and (
            symbol_str + self.current_char
        ) in (
            ARITHMETIC_OPERATORS
            + RELATIONAL_OPERATORS
            + ASSIGNMENT_OPERATORS
            + BITWISE_OPERATORS
            + LOGICAL_OPERATORS
            + UNARY_OPERATORS
        ):
            symbol_str += self.current_char
            self.advance()

        if symbol_str in ASSIGNMENT_OPERATORS:
            token = Token('ASSIGNMENT_OPERATOR', symbol_str)
        elif symbol_str in ['+', '-']:
            if self.prev_token_type in ['IDENTIFIER', 'INTEGER', 'REAL_NUMBER', 'CLOSING_PARENTHESIS']:
                token = Token('ARITHMETIC_OPERATOR', symbol_str)
            elif self.prev_token_type in ['ARITHMETIC_OPERATOR', 'UNARY_OPERATOR', None]:
                token = Token('UNARY_OPERATOR', symbol_str)
            else:
                token = Token('ARITHMETIC_OPERATOR', symbol_str)  
        elif symbol_str in ARITHMETIC_OPERATORS:
            token = Token('ARITHMETIC_OPERATOR', symbol_str)
        elif symbol_str in RELATIONAL_OPERATORS:
            token = Token('RELATIONAL_OPERATOR', symbol_str)
        elif symbol_str in LOGICAL_OPERATORS:
            token = Token('LOGICAL_OPERATOR', symbol_str)
        elif symbol_str in BITWISE_OPERATORS:
            token = Token('BITWISE_OPERATOR', symbol_str)
        elif symbol_str in SPECIAL_SYMBOLS:
            token = Token('SPECIAL_SYMBOL', symbol_str)
        elif symbol_str in TERMINATING_SYMBOLS:
            token = Token('TERMINATING_SYMBOL', symbol_str)
        elif symbol_str in SEPARATING_SYMBOLS:
            token = Token('SEPARATING_SYMBOL', symbol_str)
        elif symbol_str in PARENTHESIS:
            token = Token('PARENTHESIS', symbol_str)
        elif symbol_str == '.' and self.prev_token_type in ['RESERVED_WORD', 'IDENTIFIER']:
            token = Token('ACCESSOR_SYMBOL', symbol_str)
        else:
            return IllegalCharError(pos_start, self.pos, f"Unknown symbol '{symbol_str}'")

        self.prev_token_type = token.type
        return token

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
                    return Token('COMMENT', comment_text.strip())
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
                return Token('COMMENT', comment_text.strip())
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
#                RUN                  #
#######################################

from prettytable import PrettyTable 


def run(fn, text):
    if not fn.endswith('.lit'):
        return [], f"Invalid file extension: '{fn}'. Only '.lit' files are allowed."

    lexer = Lexer(fn, text)
    tokens, errors = lexer.make_tokens()

    for error in errors:
        print(error.as_string())

    output_filepath = f"{fn.replace('.lit', '_output.txt')}"
    with open(output_filepath, "w") as f:
        f.write("--------------- Input ---------------\n")
        f.write(text + "\n\n")

        f.write("----------- Tokens Table ------------\n")
        token_table = PrettyTable()
        token_table.field_names = ["Token Specification", "Tokens"]

        for token in tokens:
            if isinstance(token, Error): 
                continue
            token_table.add_row([token.type, token.value])

        f.write(token_table.get_string())
        f.write("\n\n")

        f.write("----------- Errors Table ------------\n")
        if errors:
            error_table = PrettyTable()
            error_table.field_names = ["Error Type", "Details", "Location"]
            for error in errors:
                error_table.add_row([
                    error.error_name,
                    error.details,
                    f"Line {error.pos_start.ln + 1}, Column {error.pos_start.col + 1}"
                ])
            f.write(error_table.get_string())
        else:
            f.write("No errors found.\n")

    return tokens, errors