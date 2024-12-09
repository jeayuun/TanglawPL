import re

# Token definitions
TOKENS = {
    "ALPHABET": r"[a-zA-Z]",
    "UPPERCASE_ALPHABET": r"[A-Z]",
    "LOWERCASE_ALPHABET": r"[a-z]",
    "NON_ZERO": r"[1-9]",
    "ZERO": r"0",

    "IDENTIFIER": r"[a-zA-Z_][a-zA-Z0-9_]*",
    "INTEGER": r"[1-9][0-9]*|0",
    "REAL_NUMBER": r"[1-9][0-9]*\.[0-9]+|0\.[0-9]+",
    "STRING_LITERAL": r'"[^"]*"',  # Double quotes
    "CHARACTER_LITERAL": r"'[a-zA-Z]'",
    "OPERATOR": r"(\+|\-|\*|/|%|\+\+|--|\*\*|<|>|<=|>=|==|!=|&&|\|\||&|\||\^|!|<<|>>)",
    "ASSIGNMENT": r"(=|\+=|-=|\*=|/=|%=|~=|\*\*=|&=|`=|\^=|<<=|>>=)",
    "SEMICOLON": r";",
    "SPECIAL_SYMBOL": r"(:|,|\\|\.|\||&|!)",
    "KEYWORD": r"(if|else|return|main|case|try|catch|do|while|for|each|import|implements|switch|throw|throws|this|public|protected|private|new|package|break|repeat|def|print|input|continue|default|const|extends|finally|static)",
    "RESERVED_WORD": r"(fetch|areaOf|circle|cubic|distance|ft|in|kg|km|l|lbs|m|mg|mm|perimeterOf|repeat|sphere|sq|triangle|rectangle|square|volumeOf|radius|circumference|length|height|width|side)",
    "DATA_TYPE": r"(int|float|double|String|char|boolean|long|short|signed)"
}

# IDENTIFIERS
def is_valid_identifier(token):
    """
    Checks if the given token is a valid identifier.

    Args:
        token (str): The token to check.

    Returns:
        bool: True if the token is a valid identifier, False otherwise.
    """
    # Regular expression pattern for valid identifiers
    identifier_pattern = r"^[a-zA-Z_][a-zA-Z0-9_]*$"

    # Check if the token matches the pattern and isn't a keyword
    return re.match(identifier_pattern, token) and token not in TOKENS["KEYWORD"].split()

# INTEGERS
def is_valid_integer(token):
    """
    Checks if the given token is a valid integer.

    Args:
        token (str): The token to check.

    Returns:
        bool: True if the token is a valid integer, False otherwise.
    """

    integer_pattern = r"^[0-9]+$"
    return bool(re.match(integer_pattern, token))

# REAL NUMBER
def is_valid_real_number(token):
    """
    Checks if the given token is a valid real number.

    Args:
        token (str): The token to check.

    Returns:
        bool: True if the token is a valid real number, False otherwise.
    """
    real_number_pattern = r"^([+-]?(\d+\.\d*|\.\d+))$"
    return bool(re.match(real_number_pattern, token))

# STRING LITERALS
def is_valid_string_literal(token):
    """
    Checks if the given token is a valid string literal.

    Args:
        token (str): The token to check.

    Returns:
        bool: True if the token is a valid string literal, False otherwise.
    """
    string_literal_pattern = r'^"[^"]*"$'
    return bool(re.match(string_literal_pattern, token))

def is_valid_character_literal(token):
    """
    Checks if the given token is a valid character literal.

    Args:
        token (str): The token to check.

    Returns:
        bool: True if the token is a valid character literal, False otherwise.
    """
    # Character literal pattern: must start and end with single quote, containing exactly one character
    character_literal_pattern = r"^'([^'\\]|\\.)'$"
    return bool(re.match(character_literal_pattern, token))


def is_valid_assignment_operator(token):
    """
    Checks if the given token is a valid assignment operator.

    Args:
        token (str): The token to check.

    Returns:
        bool: True if the token is a valid assignment operator, False otherwise.
    """
    # Character literal pattern: must start and end with single quote, containing exactly one character
    assignment_pattern = r"^(?:\+=|-=|\*=|/=|%=|&=|\^=|\|=|<<=|>>=|=)$"
    return bool(re.match(assignment_pattern, token))

def is_valid_operator(token):
    """
    Checks if the given token is a valid operator.

    Args:
        token (str): The token to check.

    Returns:
        bool: True if the token is a valid operator, False otherwise.
    """
    # Character literal pattern: must start and end with single quote, containing exactly one character
    operator_pattern = r"^[+\-*/%<>=!&^|]{1,2}$|^(<=|>=|!=|&&|\|\|)$"
    return bool(re.match(operator_pattern, token))


def error_handler(token):
    """
    Checks if the given token matches one of the defined token patterns.
    If not, it identifies the possible error and returns an appropriate message.

    Args:
        token (str): The token to check.

    Returns:
        str: An error message if the token is invalid, otherwise "Valid <token_type>".
    """

    # Check for valid token types using respective functions
    if is_valid_identifier(token):
        return f"Valid IDENTIFIER."
    
    elif is_valid_integer(token):
        return f"Valid INTEGER."
    
    elif is_valid_real_number(token):
        return f"Valid REAL_NUMBER."
    
    elif is_valid_string_literal(token):
        return f"Valid STRING_LITERAL."
    
    elif is_valid_character_literal(token):
        return f"Valid CHARACER_LITERAL."
    
    elif is_valid_assignment_operator(token):
        return f"Valid ASSIGNMENT_OPERATOR."
    
    elif is_valid_operator(token):
        return f"Valid OPERATOR."
    

    # Check for invalid symbols (anything not allowed in identifiers)
    elif re.search(r"[^a-zA-Z0-9_]", token):
        return f"Error: Invalid symbol in token '{token}'."

    # If token doesn't match any valid pattern
    else:
        return f"Error: Unrecognized token '{token}'."

#TEST CASES FOR ERROR HANDLER ( TOKENS ARE CHECKED)
def test_error_handler():
    """
    Runs a series of test cases to validate the error handler.
    """
    test_tokens = [
        # Identifiers (Valid and Invalid)
        "valid_variable",  # Valid identifier
        "var!able",        # Invalid symbol
        "var@iable",       # Invalid symbol
        "variable123",     # Valid identifier
        "3variable",       # Invalid identifier, starts with a number
        "_valid",          # Valid identifier
        "invalid@symbol",  # Invalid symbol

        #Numbers
        "12345",           # Valid integer
        "34.34",           # Valid real number
        "-34.34",           # Valid real number
        "34.34.34",           # Valid real number
        "0.234",           # Valid real number
        ".789",           # Valid real number
        "456.",           # Valid real number
        
        # String Literals
        '"hello world"',   # Valid string literal
        '"missing quote',   # Invalid string literal (missing closing quote)
        '"string with space"', # Valid string literal with spaces
        '"unterminated_string', # Invalid string literal (missing closing quote)
        
        #CHAR LITERAL
        "'too long char literal'",  # Invalid character literal (too long)
        "'a'",             # Valid character literal
        "'b'",             # Valid character literal
        
        # Operators
        "+",               # Valid operator
        "-",               # Valid operator
        "*",               # Valid operator
        "/",               # Valid operator
        "%",               # Valid operator
        "&&",              # Valid operator
        "||",              # Valid operator
        "++",              # Valid operator
        "---",             # Invalid operator
        "<<",              # Valid operator
        ">>",              # Valid operator
        "^",               # Valid operator
        "invalid++",       # Invalid operator (unrecognized token)
        
        # Assignment Operators
        "=",               # Valid assignment operator
        "+=",              # Valid assignment operator
        "-=",              # Valid assignment operator
        "*=",              # Valid assignment operator
        "====",              # Valid assignment operator
        "%=",              # Valid assignment operator
        "&=",              # Valid assignment operator
        "invalid=+",       # Invalid assignment operator
    ]
    
    for token in test_tokens:
        print(f"Token: {token} => {error_handler(token)}")

# Run the test cases

test_error_handler()