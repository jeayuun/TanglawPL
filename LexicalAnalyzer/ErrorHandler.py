import re

# Define the token sets for keyword comparison
KEYWORDS = {
    "if", "else", "return", "main", "case", "try", "catch", "do", "while", "for", "each",
    "import", "implements", "switch", "throw", "throws", "this", "public", "protected", 
    "private", "new", "package", "break", "repeat", "def", "print", "input", "continue", 
    "default", "const", "extends", "finally", "static"
}

RESERVED_WORDS = {
    "fetch", "areaOf", "circle", "cubic", "distance", "ft", "in", "kg", "km", "l", "lbs",
    "m", "mg", "mm", "perimeterOf", "repeat", "sphere", "sq", "triangle", "rectangle", 
    "square", "volumeOf", "radius", "circumference", "length", "height", "width", "side", 
    "solve"
}

# Update functions with fixes

def is_valid_identifier(token):
    identifier_pattern = r"^[a-zA-Z_][a-zA-Z0-9_]*$"
    return bool(re.match(identifier_pattern, token)) and token not in KEYWORDS

def is_valid_integer(token):
    integer_pattern = r"^-?[0-9]+$"
    return bool(re.match(integer_pattern, token))

def is_valid_real_number(token):
    real_number_pattern = r"^-?([0-9]*\.[0-9]+)$"
    return bool(re.match(real_number_pattern, token))

def is_valid_string_literal(token):
    string_literal_pattern = r'^".*"$'
    return bool(re.match(string_literal_pattern, token))

def is_valid_character_literal(token):
    character_literal_pattern = r"^'([^'\\]|\\.)'$"
    return bool(re.match(character_literal_pattern, token))

def is_valid_assignment_operator(token):
    assignment_pattern = r"^(=|\+=|-=|\*=|/=|%=|&=|\|=|\^=|<<=|>>=)$"
    return bool(re.match(assignment_pattern, token))

def is_valid_operator(token):
    operator_pattern = r"^[+\-*/%<>=!&^|]{1,2}$|^(<=|>=|!=|&&|\|\|)$"
    return bool(re.match(operator_pattern, token))

def error_handler(token):
    if is_valid_identifier(token):
        return "Valid IDENTIFIER."
    elif is_valid_integer(token):
        return "Valid INTEGER."
    elif is_valid_real_number(token):
        return "Valid REAL_NUMBER."
    elif is_valid_string_literal(token):
        return "Valid STRING_LITERAL."
    elif is_valid_character_literal(token):
        return "Valid CHARACTER_LITERAL."
    elif is_valid_assignment_operator(token):
        return "Valid ASSIGNMENT_OPERATOR."
    elif is_valid_operator(token):
        return "Valid OPERATOR."
    elif re.search(r"[^a-zA-Z0-9_.,;:+*/%<>=!&^|@#$~\s]", token):
        return f"Error: Invalid symbol in token '{token}'."
    else:
        return f"Error: Unrecognized token '{token}'."

# Test function
def test_error_handler():
    test_tokens = [
        "valid_variable", "var!able", "var@iable", "variable123", "3variable", "_valid", "invalid@symbol",
        "12345", "-123", "34.34", "-34.34", "34.34.34", ".789", "456.", '"hello world"', '"missing quote',
        "'a'", "'\\n'", "'too long char'", "+", "-", "++", "--", "<<", ">>", "&&", "||", "====", "=+", "%="
    ]
    for token in test_tokens:
        print(f"Token: {token} => {error_handler(token)}")

# Run the test
test_error_handler()
