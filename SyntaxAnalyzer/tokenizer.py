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
    
    def get_location(self):
        if self.pos_start and self.pos_end:
            return f"Line {self.pos_start.ln + 1}, Column {self.pos_start.col + 1}-{self.pos_end.col + 1}"
        elif self.pos_start:
            return f"Line {self.pos_start.ln + 1}, Column {self.pos_start.col + 1}"
        return "Unknown"


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
    def __init__(self, type_, value=None, pos_start=None, pos_end=None):
        self.type = type_
        self.value = value
        self.pos_start = pos_start
        self.pos_end = pos_end

    def __repr__(self):
        if self.type == "ERROR":
            return f'ErrorToken: {self.value}'
        return f'{self.type}: {self.value}'


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
            pos_start = self.pos.copy()

            if self.current_char in WHITESPACE:
                self.advance()
                continue

            elif self.current_char in DIGITS or (self.current_char == '-' and self.is_negative_sign()):
                token_or_error = self.make_number()
                if isinstance(token_or_error, Error):
                    errors.append(token_or_error)  # ✅ Store errors separately
                else:
                    token_or_error.pos_start = pos_start
                    token_or_error.pos_end = self.pos.copy()
                    tokens.append(token_or_error)
                continue

            elif self.current_char in ALPHABETS or self.current_char == '_':
                token_or_tokens = self.make_identifier_or_keyword()
                if isinstance(token_or_tokens, list):
                    for token in token_or_tokens:
                        token.pos_start = pos_start
                        token.pos_end = self.pos.copy()
                    tokens.extend(token_or_tokens)
                elif isinstance(token_or_tokens, Error):
                    errors.append(token_or_tokens)  # ✅ Store errors separately
                else:
                    token_or_tokens.pos_start = pos_start
                    token_or_tokens.pos_end = self.pos.copy()
                    tokens.append(token_or_tokens)
                continue

            elif self.current_char == '"':
                tokens_or_error = self.make_string()
                if isinstance(tokens_or_error, Error):
                    errors.append(tokens_or_error)  # ✅ Store errors separately
                else:
                    for token in tokens_or_error:
                        token.pos_start = pos_start
                        token.pos_end = self.pos.copy()
                    tokens.extend(tokens_or_error)
                continue

            elif self.current_char == "'":
                token_or_error = self.make_character()
                if isinstance(token_or_error, Error):
                    errors.append(token_or_error)  # ✅ Store errors separately
                else:
                    token_or_error.pos_start = pos_start
                    token_or_error.pos_end = self.pos.copy()
                    tokens.append(token_or_error)
                continue

            else:
                if self.current_char in [';', '(', ')', '{', '}', '=']:
                    tokens.append(Token("SYMBOL", self.current_char, pos_start, self.pos.copy()))
                else:
                    errors.append(IllegalCharError(pos_start, self.pos, self.current_char))
                self.advance()



        return tokens, errors  # ✅ Ensure tokens and errors are returned separately


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
        decimal_count = 0
        pos_start = self.pos.copy()

        if self.current_char == '-' or self.current_char == '+':  
            num_str += self.current_char
            self.advance()

        while self.current_char is not None and self.current_char in DIGITS + '.':
            if self.current_char == '.':
                if has_decimal:
                    return InvalidNumberError(pos_start, self.pos, f"Invalid number '{num_str}'. Multiple decimal points detected.")
                has_decimal = True
            else:
                if has_decimal:
                    decimal_count += 1
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
                if decimal_count > 7:  #
                    token = Token('DOUBLE', real_number)
                else:  
                    token = Token('FLOAT', real_number)
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

        tokens = [] 

        while self.current_char is not None and (
            self.current_char in ALPHABETS + DIGITS + '_' or self.current_char == '.'):
            if self.current_char == '.':
                if id_str in RESERVED_WORDS or id_str in KEYWORDS:
                    token = Token('RESERVED_WORD', id_str)
                else:
                    token = Token('IDENTIFIER', id_str)
                self.prev_token_type = token.type
                self.advance()
                tokens.append(token)
                tokens.append(Token('ACCESSOR_SYMBOL', '.'))
                return tokens
            id_str += self.current_char
            self.advance()

        for noise_word in NOISE_WORDS:
            if noise_word in id_str:
                tokens.append(Token('NOISE_WORD', noise_word))

        normalized = NOISE_WORD_RULES.get(id_str, id_str)
        if normalized in DATA_TYPES:
            tokens.append(Token('DATA_TYPE', normalized))
        elif normalized in BOOLEAN_VALUES:
            tokens.append(Token('BOOLEAN', normalized))
        elif normalized in KEYWORDS:
            tokens.append(Token('KEYWORD', normalized))
        elif normalized in RESERVED_WORDS:
            tokens.append(Token('RESERVED_WORD', normalized))
        else:
            tokens.append(Token('IDENTIFIER', id_str))

        return tokens
    
    def make_tokens(self):
        tokens = []
        errors = []

        while self.current_char is not None:
            pos_start = self.pos.copy()  # Ensure we track position

            if self.current_char in WHITESPACE:
                self.advance()
                continue

            elif self.current_char in DIGITS or (self.current_char == '-' and self.is_negative_sign()):
                token_or_error = self.make_number()
                if isinstance(token_or_error, Error):
                    errors.append(token_or_error)
                else:
                    token_or_error.pos_start = pos_start
                    token_or_error.pos_end = self.pos.copy()
                    tokens.append(token_or_error)
                continue

            elif self.current_char in ALPHABETS or self.current_char == '_':
                token_or_tokens = self.make_identifier_or_keyword()
                if isinstance(token_or_tokens, list):
                    for token in token_or_tokens:
                        token.pos_start = pos_start
                        token.pos_end = self.pos.copy()
                    tokens.extend(token_or_tokens)
                elif isinstance(token_or_tokens, Error):
                    errors.append(token_or_tokens)
                else:
                    token_or_tokens.pos_start = pos_start
                    token_or_tokens.pos_end = self.pos.copy()
                    tokens.append(token_or_tokens)
                continue

            elif self.current_char == '"':
                tokens_or_error = self.make_string()
                if isinstance(tokens_or_error, Error):
                    errors.append(tokens_or_error)
                else:
                    for token in tokens_or_error:
                        token.pos_start = pos_start
                        token.pos_end = self.pos.copy()
                    tokens.extend(tokens_or_error)
                continue

            elif self.current_char == "'":
                token_or_error = self.make_character()
                if isinstance(token_or_error, Error):
                    errors.append(token_or_error)
                else:
                    token_or_error.pos_start = pos_start
                    token_or_error.pos_end = self.pos.copy()
                    tokens.append(token_or_error)
                continue

            else:
                if self.current_char in [';', '(', ')', '{', '}', '=']:
                    tokens.append(Token("SYMBOL", self.current_char, pos_start, self.pos.copy()))
                else:
                    errors.append(IllegalCharError(pos_start, self.pos, self.current_char))
                self.advance()

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
                    return UnclosedStringError(pos_start, self.pos, "String literal was not closed.")
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

        if (symbol_str in ['++', '--'] and 
            (self.current_char == '+' or self.current_char == '-')):
            return IllegalCharError(pos_start, self.pos, f"Unexpected trailing '{self.current_char}' after unary operator '{symbol_str}'.")

        if symbol_str in ASSIGNMENT_OPERATORS:
            if symbol_str == '=':
                token = Token('ASSIGN_OP', symbol_str) 
            elif symbol_str == '+=':
                token = Token('ADD_ASSIGN_OP', symbol_str)
            elif symbol_str == '-=':
                token = Token('SUBT_ASSIGN_OP', symbol_str)
            elif symbol_str == '*=':
                token = Token('MULTIPLY_ASSIGN_OP', symbol_str)
            elif symbol_str == '/=':
                token = Token('DIV_ASSIGN_OP', symbol_str)
            elif symbol_str == '%=':
                token = Token('MOD_ASSIGN_OP', symbol_str)
            elif symbol_str in '^=': 
                token = Token('XOR_ASSIGN_OP', symbol_str) 
            elif symbol_str in '~=': 
                token = Token('INT_DIV_ASSIGN_OP', symbol_str)
            elif symbol_str == '**=':
                token = Token('EXPONENTIAL_ASSIGN_OP', symbol_str)
            elif symbol_str == '&=':
                token = Token('BITWISE_AND_ASSIGN_OP', symbol_str)
            elif symbol_str == '`=': 
                token = Token('BITWISE_OR_ASSIGN_OP', symbol_str) 
            elif symbol_str == '<<=':
                token = Token('L_SHIFT_ASSIGN_OP', symbol_str)
            elif symbol_str == '>>=':
                token = Token('R_SHIFT_ASSIGN_OP', symbol_str)

        elif symbol_str in ['+', '-']:
            if self.prev_token_type in ['IDENTIFIER', 'INTEGER', 'REAL_NUMBER', 'CLOSING_PARENTHESIS']:
                if symbol_str == '+':
                    token = Token('ADD_OPERATOR', symbol_str)
                elif symbol_str == '-':
                    token = Token('SUBTRACT_OPERATOR', symbol_str)
            elif self.prev_token_type in ['ARITHMETIC_OPERATOR', 'UNARY_OPERATOR', None]:
                token = Token('UNARY_OPERATOR', symbol_str)
            else:
                token = Token('ARITHMETIC_OPERATOR', symbol_str)  

        elif symbol_str == '++':
            token = Token('INCREMENT_UNARY_OP', '++')
        elif symbol_str == '--':
            token = Token('DECREMENT_UNARY_OP', '--')

        elif symbol_str in ARITHMETIC_OPERATORS:
            if symbol_str == '*':
                token = Token('MULTIPLY_OP', symbol_str)
            elif symbol_str == '/':
                token = Token('DIVIDE_OP', symbol_str)
            elif symbol_str == '%':
                token = Token('MODULO_OP', symbol_str)
            elif symbol_str == '**':
                token = Token('EXPONENTIATION_OP', symbol_str) 
            else:
                token = Token('ARITHMETIC_OPERATOR', symbol_str)

        elif symbol_str in RELATIONAL_OPERATORS:
            if symbol_str == '<':
                token = Token('LESS_THAN', symbol_str) 
            elif symbol_str == '>':
                token = Token('GREATER_THAN', symbol_str) 
            elif symbol_str == '<=':
                token = Token('LESS_THAN_OR_EQUAL_TO', symbol_str) 
            elif symbol_str == '>=':
                token = Token('GREATER_THAN_OR_EQUAL_TO', symbol_str) 
            elif symbol_str == '==':
                token = Token('EQUAL_TO', symbol_str) 
            elif symbol_str == '!=':
                token = Token('NOT_EQUAL_TO', symbol_str) 
            else:
                token = Token('RELATIONAL_OPERATOR', symbol_str) 

        elif symbol_str in LOGICAL_OPERATORS:
            token = Token('LOGICAL_OPERATOR', symbol_str)
            if symbol_str == '!':
                token = Token('NOT_LOGICAL_OP', symbol_str) 
            elif symbol_str == '&&':
                token = Token('AND_LOGICAL_OP', symbol_str)  
            elif symbol_str == '||':
                token = Token('OR_LOGICAL_OP', symbol_str)

        elif symbol_str in BITWISE_OPERATORS:
            if symbol_str == '&':
                token = Token('BITWISE_AND_OP', symbol_str)
            elif symbol_str == '`': 
                token = Token('BITWISE_OR_OP', symbol_str)
            elif symbol_str == '^':
                token = Token('BITWISE_XOR_OP', symbol_str)
            elif symbol_str == '<<':
                token = Token('LEFT_SHIFT_OP', symbol_str)
            elif symbol_str == '>>':
                token = Token('RIGHT_SHIFT_OP', symbol_str)
            elif symbol_str == '~':
                token = Token('BITWISE_NOT_OP', symbol_str) # to be changed 
            else:
                token = Token('BITWISE_OP', symbol_str) 

        elif symbol_str in SPECIAL_SYMBOLS:
            if symbol_str == '|':
                token = Token('PIPE_SYMBOL', symbol_str)
            elif symbol_str == ':':
                token = Token('COLON_SYMBOL', symbol_str)
            elif symbol_str == '`':
                token = Token('BACKTICK_SYMBOL', symbol_str)
            elif symbol_str == '\\':
                token = Token('BACKSLASH_SYMBOL', symbol_str)
            elif symbol_str == '@':
                token = Token('AT_SYMBOL', symbol_str)
            elif symbol_str == '#':
                token = Token('HASH_SYMBOL', symbol_str)
            elif symbol_str == '$':
                token = Token('DOLLAR_SYMBOL', symbol_str)
            elif symbol_str == '~':
                token = Token('TILDE_SYMBOL', symbol_str)
            elif symbol_str == '"':
                token = Token('DOUBLE_QUOTE_SYMBOL', symbol_str)
            elif symbol_str == "'":
                token = Token('SINGLE_QUOTE_SYMBOL', symbol_str)
            else:
                token = Token('SPECIAL_SYMBOL', symbol_str) 

        elif symbol_str in TERMINATING_SYMBOLS:
            if symbol_str == ';':
                token = Token('SEMICOLON', symbol_str)
            else:
                token = Token('TERMINATING_SYMBOL', symbol_str) 
        elif symbol_str in SEPARATING_SYMBOLS:
            token = Token('SEPARATING_SYMBOL', symbol_str)
            
        elif symbol_str in PARENTHESIS:
            if symbol_str == '(':
                token = Token('L_PARENTHESIS', symbol_str) 
            elif symbol_str == ')':
                token = Token('R_PARENTHESIS', symbol_str)
            elif symbol_str == '{':
                token = Token('L_CURLY', symbol_str) 
            elif symbol_str == '}':
                token = Token('R_CURLY', symbol_str) 
            elif symbol_str == '[':
                token = Token('L_BRACKET', symbol_str)
            elif symbol_str == ']':
                token = Token('R_BRACKET', symbol_str)
            else:
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
        token_table.field_names = ["Lexeme", "Token Specification"]

        for token in tokens:
            if isinstance(token, Error): 
                continue
            token_table.add_row([token.value, token.type])

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