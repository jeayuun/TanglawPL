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
    'extends', 'finally', 'static'
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
BITWISE_OPERATORS = ['&', '`', '^', '<<', '>>', '!']
SPECIAL_SYMBOLS = ['|', ':', '`', '\\', '@', '#', '$', '~']
ACCESSOR_SYMBOL = ['.']
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

            elif self.current_char == '#':
                comment_token = self.make_comment()
                if isinstance(comment_token, Error):
                    errors.append(comment_token)  # Collect errors
                else:
                    tokens.append(comment_token)

            elif self.current_char in DIGITS or (self.current_char == '-' and self.is_negative_sign()):
                token_or_error = self.make_number()
                if isinstance(token_or_error, Error):
                    errors.append(token_or_error)  # Collect errors
                else:
                    tokens.append(token_or_error)

            elif self.current_char in ALPHABETS or self.current_char == '_':
                token = self.make_identifier_or_keyword()
                if isinstance(token, Error):
                    errors.append(token)  # Collect errors
                else:
                    tokens.append(token)

            elif self.current_char == '"':
                token = self.make_string()
                if isinstance(token, Error):
                    errors.append(token)  # Collect errors
                else:
                    tokens.append(token)

            elif self.current_char == "'":
                token = self.make_character()
                if isinstance(token, Error):
                    errors.append(token)  # Collect errors
                else:
                    tokens.append(token)

            elif self.current_char in SYMBOLS:
                token_or_error = self.make_symbol()
                if isinstance(token_or_error, Error):
                    errors.append(token_or_error)  # Collect errors
                else:
                    tokens.append(token_or_error)

            else:
                pos_start = self.pos.copy()
                char = self.current_char
                self.advance()
                errors.append(IllegalCharError(pos_start, self.pos, char))

        return tokens, errors

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
            invalid_token = num_str + self.current_char
            self.advance()
            while self.current_char is not None and (self.current_char in ALPHABETS + DIGITS + '_'):
                invalid_token += self.current_char
                self.advance()
            return IllegalCharError(pos_start, self.pos, f"Invalid number or identifier '{invalid_token}'")

        try:
            if has_decimal:
                token = Token('REAL_NUMBER', float(num_str))
            else:
                token = Token('INTEGER', int(num_str))

            self.prev_token_type = token.type  
            return token
        except ValueError:
            return InvalidNumberError(pos_start, self.pos, f"Invalid number '{num_str}'")

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
        
        if self.current_char == '.':
            return Token('RESERVED_WORDS', id_str) if id_str in RESERVED_WORDS else Token('IDENTIFIER', id_str)
    
        if not all(char in ALPHABETS + DIGITS + '_' for char in id_str):
            return IllegalCharError(pos_start, self.pos, 
                f"Invalid identifier '{id_str}' (Identifiers can only include letters, digits, and underscores).")

        if id_str in DATA_TYPES:
            return Token('DATA_TYPE', id_str)
        elif id_str in BOOLEAN_VALUES:
            return Token('BOOLEAN', id_str)
        elif id_str in KEYWORDS:
            return Token('KEYWORD', id_str)
        elif id_str in RESERVED_WORDS:
            return Token('RESERVED_WORDS', id_str)
        else:
            return Token('IDENTIFIER', id_str)
    
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
                return Token('STRING_LITERAL', str_val)
            else:
                str_val += self.current_char
            self.advance()

        return UnclosedStringError(pos_start, self.pos)

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
        return Token('CHARACTER_LITERAL', char_val)

    def make_symbol(self):
        pos_start = self.pos.copy()
        symbol_str = self.current_char
        self.advance()

        if symbol_str == '+' or symbol_str == '-':
            if self.current_char == symbol_str: 
                symbol_str += self.current_char
                self.advance()

        # Handle other symbols normally
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
        
        if symbol_str == '.' and self.prev_token_type in ['RESERVED_WORD', 'IDENTIFIER']:
            return Token('ACCESSOR_SYMBOL', symbol_str)
        if symbol_str == '++':
            token = Token('UNARY_OPERATOR', '++')
        elif symbol_str == '--':
            token = Token('UNARY_OPERATOR', '--')
        elif symbol_str == '-':
            token = Token('ARITHMETIC_OPERATOR', symbol_str)
        elif symbol_str == '+':
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

        self.prev_token_type = token.type  # Update `prev_token_type`
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

import os
from prettytable import PrettyTable 


def run(fn, text):
    if not fn.endswith('.lit'):
        return [], f"Invalid file extension: '{fn}'. Only '.lit' files are allowed."

    lexer = Lexer(fn, text)
    tokens, errors = lexer.make_tokens()

    for error in errors:
        print(error.as_string())

    # if error:
    #     return [], error.as_string()

    # symbol_table = {}
    

    # for token in tokens:
    #     if isinstance(token, Error):  # Skip errors
    #         continue
    #     if token.type not in symbol_table:
    #         symbol_table[token.type] = []
    #     symbol_table[token.type].append(token.value)

    output_filepath = f"{fn.replace('.lit', '_output.txt')}"
    with open(output_filepath, "w") as f:
        f.write("--------------- Input ---------------\n")
        f.write(text + "\n\n")

        # Tokens Table
        f.write("----------- Tokens Table ------------\n")
        token_table = PrettyTable()
        token_table.field_names = ["Token Specification", "Tokens"]

        for token in tokens:
            if isinstance(token, Error):  # Skip errors
                continue
            token_table.add_row([token.type, token.value])

        f.write(token_table.get_string())
        f.write("\n\n")

        # Errors Table
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