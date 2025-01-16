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

# Language-specific keywords and reserved words
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

# Groups of symbols for easier classification
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
NOISE_WORDS = ['ant', 'ine']

#######################################
#               ERRORS                #
#######################################

#class to represent the errors encountered in the program
class Error:

    #pos_start (Position): The starting position of the error in the input.
    #pos_end (Position): The ending position of the error in the input.
    #error_name (str): The name of the error (e.g., "Illegal Character").
    #details (str): Additional details about the error.
    def __init__(self, pos_start, pos_end, error_name, details):
        self.pos_start = pos_start
        self.pos_end = pos_end
        self.error_name = error_name
        self.details = details

    # Method to format the error as a readable string
    def as_string(self):
        result = f'{self.error_name}: {self.details}\n' # Error type and details
        result += f'File {self.pos_start.fn}, line {self.pos_start.ln + 1}, column {self.pos_start.col + 1}-{self.pos_end.col + 1}'
        # Includes file name, line, and column info for error localization ^
        return result

# Subclass to represent errors caused by illegal characters
class IllegalCharError(Error):
    def __init__(self, pos_start, pos_end, illegal_char):
        super().__init__(pos_start, pos_end, 'Illegal Character', f"'{illegal_char}' is not allowed.")


# Subclass to represent errors due to unclosed string literals
class UnclosedStringError(Error):
    def __init__(self, pos_start, pos_end):
        super().__init__(pos_start, pos_end, 'Unclosed String Literal', 'String literal was not closed.')


# Subclass to represent errors related to invalid number formats
class InvalidNumberError(Error):
    def __init__(self, pos_start, pos_end, details):
        super().__init__(pos_start, pos_end, 'Invalid Number', details)

#######################################
#              POSITION               #
#######################################

# Class to track the current position within the source code
class Position:
    def __init__(self, idx, ln, col, fn, ftxt):
        self.idx = idx # Index of the current character in the source text
        self.ln = ln  #Current line number (0-based)
        self.col = col # Current column number (0-based)
        self.fn = fn # Filename of the source code
        self.ftxt = ftxt # Full text of the source code being processed

    # Advances the position based on the current character
    def advance(self, current_char):
        self.idx += 1 # Move to the next character
        self.col += 1 # Move to the next column

        # If the current character is a newline, update line and reset column
        if current_char == '\n':
            self.ln += 1 # Increment the line number
            self.col = 0 # Reset column to the start

        return self # Return the updated position

    def copy(self):
        return Position(self.idx, self.ln, self.col, self.fn, self.ftxt)

#######################################
#               TOKENS                #
#######################################

# Class representing a token generated during lexical analysis
class Token:
    def __init__(self, type_, value=None):
        # Type of the token (e.g., IDENTIFIER, INTEGER, PLUS)
        self.type = type_
        # Value associated with the token (e.g., the actual number or string)
        self.value = value
    
    # String representation of the token (for debugging purposes)
    def __repr__(self):
        if self.value: return f'{self.type}: {self.value}'
        return f'{self.type}'

#######################################
#               LEXER                 #
#######################################

# Lexer class for converting source code text into tokens
class Lexer:
    def __init__(self, fn, text):
        # Initialize lexer with file name and source text
        self.fn = fn
        self.text = text

        # Position object to track current location in text
        self.pos = Position(-1, 0, -1, fn, text)
        self.current_char = None # Current character being processed
        self.prev_token_type = None  
        self.advance() # Advance to the first character

    # Advances the position to the next character
    def advance(self):
        self.pos.advance(self.current_char)
        self.current_char = self.text[self.pos.idx] if self.pos.idx < len(self.text) else None

    # Main method to tokenize the source text   
    def make_tokens(self):
        tokens = [] # List to store valid tokens
        errors = [] # List to store errors encountered during tokenization

        # Loop until all characters are processed
        while self.current_char is not None:
            # Skips whitespace and escape sequences
            if self.current_char in WHITESPACE or (self.current_char == '\\' and self.peek() in 'tnv'):
                self.advance()

            # Process comments (starting with #)    
            elif self.current_char == '#':
                comment_token = self.make_comment()
                if isinstance(comment_token, Error): # Checks if an error occurred
                    errors.append(comment_token) 
                else:
                    tokens.append(comment_token)

            # Process symbols (operators, punctuation, etc.)        
            elif self.current_char in SYMBOLS: 
                token_or_error = self.make_symbol()
                if isinstance(token_or_error, Error):
                    errors.append(token_or_error) 
                else:
                    tokens.append(token_or_error)

            # Process numbers (digits, including negative numbers)
            elif self.current_char in DIGITS or (self.current_char == '-' and self.is_negative_sign()):
                token_or_error = self.make_number()
                if isinstance(token_or_error, Error):
                    errors.append(token_or_error)  
                else:
                    tokens.append(token_or_error)

            # Process identifiers (variables, keywords) and underscores     
            elif self.current_char in ALPHABETS or self.current_char == '_':
                token_or_tokens = self.make_identifier_or_keyword()
                if isinstance(token_or_tokens, list):  
                    tokens.extend(token_or_tokens)
                elif isinstance(token_or_tokens, Error):
                    errors.append(token_or_tokens)
                else:
                    tokens.append(token_or_tokens)

            # Process strings (enclosed in double quotes)
            elif self.current_char == '"':
                token = self.make_string()
                if isinstance(token, Error):
                    errors.append(token) 
                else:
                    tokens.append(token)

            # Process characters (enclosed in single quotes)
            elif self.current_char == "'":
                token = self.make_character()
                if isinstance(token, Error):
                    errors.append(token) 
                else:
                    tokens.append(token)

            # Handle symbols (operators, punctuation, etc.)
            elif self.current_char in SYMBOLS:
                token_or_error = self.make_symbol()
                if isinstance(token_or_error, Error):
                    errors.append(token_or_error)  
                else:
                    tokens.append(token_or_error)

            # Handles characters in the input text that are not recognized
            else:
                pos_start = self.pos.copy()
                char = self.current_char
                self.advance()
                errors.append(IllegalCharError(pos_start, self.pos, char))

        return tokens, errors # Returning the list of tokens and any encountered errors

    # Peek method for looking ahead one character in the text
    def peek(self):
        peek_pos = self.pos.idx + 1
        return self.text[peek_pos] if peek_pos < len(self.text) else None

    # Method to check if the current character is a negative sign
    def is_negative_sign(self):
        # If the previous token was a real number, integer, identifier, or closing parenthesis, a negative sign is not valid
        if self.prev_token_type in ['REAL_NUMBER', 'INTEGER', 'IDENTIFIER', 'CLOSING_PARENTHESIS']:
            return False
        # Otherwise, the negative sign is valid 
        return True


    #Creates a Token for a number (integer or real).
    # Returns a Token object representing the number, or an InvalidNumberError.
    def make_number(self):
        num_str = ''
        has_decimal = False
        pos_start = self.pos.copy()

        # Handle optional sign (+ or -), If the number starts with a plus or minus sign, add it to num_str
        if self.current_char == '-' or self.current_char == '+':  
            num_str += self.current_char
            self.advance() # Move to the next character

        # Loop to collect digits and the decimal point
        while self.current_char is not None and self.current_char in DIGITS + '.':
            if self.current_char == '.':

                # If a decimal point is encountered again, return an error (only one allowed)
                if has_decimal:
                    return InvalidNumberError(pos_start, self.pos, f"Invalid number '{num_str}'. Multiple decimal points detected.")
                has_decimal = True # Mark that a decimal point has been seen
            num_str += self.current_char
            self.advance()

        # Check for invalid characters after the number
        if self.current_char is not None and self.current_char in ALPHABETS + '_':
            while self.current_char is not None and self.current_char in ALPHABETS + '_':
                num_str += self.current_char
                self.advance()
            # Return an error if the number contains alphabetic characters
            return InvalidNumberError(pos_start, self.pos, f"Invalid number '{num_str}'. Numbers cannot contain alphabetic characters.")

        try:
            # Try converting num_str to an integer or a float based on the presence of a decimal point
            if has_decimal:
                token = Token('REAL_NUMBER', float(num_str)) # Create token for real number
            else:
                token = Token('INTEGER', int(num_str)) # Create token for integer

            self.prev_token_type = token.type  # Update previous token type
            return token # Return the created token
        except ValueError:
            # If conversion fails, return an error for invalid number format
            return InvalidNumberError(pos_start, self.pos, f"Invalid number '{num_str}'")

    # Creates a Token for an identifier, keyword, or reserved word.
    def make_identifier_or_keyword(self):
         # Initialize an empty string to build the identifier/keyword
        id_str = ''

        # Copy the current position to track where the identifier starts for error reporting
        pos_start = self.pos.copy()

        # Check if the current character is invalid for starting an identifier (not a letter)
        if self.current_char is None or self.current_char not in ALPHABETS:
            # If not a valid starting character, process the following characters as part of an identifier
            while self.current_char is not None and self.current_char in ALPHABETS + DIGITS + '_':
                id_str += self.current_char
                self.advance()
            pos_end = self.pos.copy()# Record the end position and return an error for invalid starting characters
            return IllegalCharError(pos_start, pos_end, 
                                    f"Invalid identifier '{id_str}' (Identifiers must begin with a letter).")


        # Process the rest of the identifier, allowing letters, digits, and underscores
        while self.current_char is not None and (
            self.current_char in ALPHABETS + DIGITS + '_' or self.current_char == '.'):

             # Handle dot (.) for object access notation
            if self.current_char == '.':

                # If we encounter a dot, check if the identifier is a reserved word or keyword
                if id_str in RESERVED_WORDS or id_str in KEYWORDS:
                    token = Token('RESERVED_WORD', id_str) # Token for reserved words
                else:
                    token = Token('IDENTIFIER', id_str) # Token for valid identifier
                self.prev_token_type = token.type # Record the type of the previous token and move to the next character
                self.advance()
                return [token, Token('ACCESSOR_SYMBOL', '.')]   # Return both the identifier and the accessor symbol
            
            # Append valid characters to continue building the identifier
            id_str += self.current_char
            self.advance()

        # Identify special types of identifiers
        if id_str in DATA_TYPES:
            return Token('DATA_TYPE', id_str)
        elif id_str in BOOLEAN_VALUES:
            return Token('BOOLEAN', id_str)
        elif id_str in KEYWORDS:
            return Token('KEYWORD', id_str)
        elif id_str in RESERVED_WORDS:
            return Token('RESERVED_WORD', id_str)
        elif id_str in NOISE_WORDS:
            return Token('NOISE_WORD', id_str)
        else:
            return Token('IDENTIFIER', id_str)
    

    #Creates a token for a string literal
    def make_string(self):
        str_val = ''
        pos_start = self.pos.copy()
        self.advance()  # Move past the opening quote ("")

        # Loop through the characters in the string until the closing quotation mark is found
        while self.current_char is not None:
            if self.current_char == '\\':   # Handle escape sequences
                self.advance()
                escape_chars = {
                    'n': '\n', 't': '\t', '"': '"', "'": "'", '\\': '\\'
                }
                str_val += escape_chars.get(self.current_char, self.current_char)
            # If a closing quotation mark is found, finish reading the string
            elif self.current_char == '"':  # End of string literal
                self.advance() # Move past the closing quotation mark
                return Token('STRING_LITERAL', str_val) # Return the string token
            else:
                str_val += self.current_char
            self.advance()

        # If the string doesn't end with a closing quote, return an error indicating the unclosed string
        return UnclosedStringError(pos_start, self.pos)

    # Creates a token for a character literal
    def make_character(self):
        pos_start = self.pos.copy()
        self.advance()  # Move to the next character (after the opening single quote)

        # Checks if the current character is missing or is an empty quote
        if self.current_char is None or self.current_char == "'":
            self.advance() 
            return IllegalCharError(
                pos_start,
                self.pos,
                "Character literal is empty. A character literal must contain exactly one character."
            )

        char_val = self.current_char # Store the character found inside the literal
        self.advance()   # Move past the character after reading it 

        if self.current_char != "'":
            if self.current_char is not None:
                char_val += self.current_char 
                self.advance()

             # Ensure that there is no extra character after the literal (should be exactly one character)
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

        self.advance()   # Move past the closing single quote
        return Token('CHARACTER_LITERAL', char_val) # Return the token representing the character

    #Creates a Token for a symbol (operator, punctuation, etc.). Handles multi-character symbols like '++', '--', '==', etc.
    def make_symbol(self):
        pos_start = self.pos.copy()
        symbol_str = self.current_char # Initialize the symbol string with the current character    
        self.advance()

        # Keep adding characters to symbol_str as long as they form valid symbols
        # The while loop checks if the combined symbol_str is in any of the operator categories
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
            self.advance() # Move to the next character

        # Once a complete symbol is detected, it is categorized
        if symbol_str in ASSIGNMENT_OPERATORS:
            token = Token('ASSIGNMENT_OPERATOR', symbol_str)
        elif symbol_str in ['+', '-']: # Special case for '+' and '-' operators
            # Check the context: if the previous token was an identifier or number, it's arithmetic
            if self.prev_token_type in ['IDENTIFIER', 'INTEGER', 'REAL_NUMBER', 'CLOSING_PARENTHESIS']:
                token = Token('ARITHMETIC_OPERATOR', symbol_str)

            # If the previous token was an operator or unary operator, it's a unary operator    
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
            # Return error if the symbol is unrecognized
            return IllegalCharError(pos_start, self.pos, f"Unknown symbol '{symbol_str}'")


        self.prev_token_type = token.type
        return token # Return the token representing the recognized symbol


    #Creates a Token for a comment. Handles both single-line (`#`) and multi-line (`##`) comments.
    def make_comment(self):
        pos_start = self.pos.copy()

        # Check for a multi-line comment (denoted by '##')
        if self.text[self.pos.idx:self.pos.idx+2] == '##':
            comment_text = ''
            self.advance() # Skip over the first '#'
            self.advance() # Skip over the second '#'

            # Collect characters until the closing '##' is found
            while self.current_char is not None:
                if self.text[self.pos.idx:self.pos.idx+2] == '##': # End of multi-line comment
                    self.advance()
                    self.advance()
                    return Token('COMMENT', comment_text.strip()) # Return the comment token
                comment_text += self.current_char
                self.advance()
            return UnclosedStringError(pos_start, self.pos) # Return error if comment is not closed

        # Check for a single-line comment (denoted by '#')
        elif self.text[self.pos.idx:self.pos.idx+1] == '#':
            comment_text = ''
            self.advance() # Skip over the '#'
             # Collect characters until the end of the line or the end of the comment
            while self.current_char is not None and self.current_char != '#':
                comment_text += self.current_char
                self.advance()
            if self.current_char == '#': # If a closing '#' is found
                self.advance()  
                return Token('COMMENT', comment_text.strip()) # Return the comment token
            return UnclosedStringError(pos_start, self.pos, "Unclosed single-line comment") # Return error if not closed

        else:
             # If the character after '#' is unexpected, return an error    
            char = self.current_char
            self.advance()
            return IllegalCharError(pos_start, self.pos, f"Unexpected character '{char}' after '#'")

    # Skips over a comment in the input text
    def skip_comment(self):
        # Skip over multi-line comments (denoted by '##')
        if self.text[self.pos.idx:self.pos.idx+2] == '##':
            self.advance() # Skip over the first '#'
            self.advance() # Skip over the second    '#'
            # Keep advancing until the closing '##' is found
            while self.current_char is not None and self.text[self.pos.idx:self.pos.idx+2] != '##':
                self.advance()
            self.advance()  
            self.advance()
        else:
            # Skip over a single-line comment (denoted by '#')
            while self.current_char is not None and self.current_char != '\n':
                self.advance()

#######################################
#                RUN                  #
#######################################

import os
from prettytable import PrettyTable 


def run(fn, text):
    """
    Runs the lexer on the given input text and generates an output file.

    Args:
        fn (str): The filename of the input text.
        text (str): The input text to be analyzed.

    Returns:
        tuple: A tuple containing:
            - A list of tokens generated by the lexer.
            - A list of errors encountered during lexing.
    """
    # only .lit files are follow
    if not fn.endswith('.lit'):
        return [], f"Invalid file extension: '{fn}'. Only '.lit' files are allowed."

    lexer = Lexer(fn, text)
    tokens, errors = lexer.make_tokens()

    # Print errors to the console
    for error in errors:
        print(error.as_string())

    # Creates an output file
    output_filepath = f"{fn.replace('.lit', '_output.txt')}"
    with open(output_filepath, "w") as f:
        f.write("--------------- Input ---------------\n")
        f.write(text + "\n\n")

        f.write("----------- Tokens Table ------------\n")
        token_table = PrettyTable()
        token_table.field_names = ["Token Specification", "Tokens"]

        for token in tokens:
            if isinstance(token, Error):  # Skip errors
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