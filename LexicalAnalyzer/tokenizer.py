import sys

# Ensure exactly one argument (file path) is provided
if len(sys.argv) != 2:
    print("Usage: python tokenizer.py <file_path>")
    sys.exit()

# Open the input file
file_path = sys.argv[1]
try:
    with open(file_path, 'r') as file:
        file_content = file.read()
except FileNotFoundError:
    print(f"File not found: {file_path}")
    sys.exit()

# Define constants
DIGITS = set("0123456789")
LETTERS = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ")
WHITESPACE = set(" \t\n\v")
SYMBOLS = set("~@#$%^&?!|\\.:")
ARITHMETIC_OPERATORS = set("+-*/%")
RELATIONAL_OPERATORS = set("<>!=")
ASSIGNMENT_OPERATORS = set("=+-*/%~^")
LOGICAL_OPERATORS = set("!&|")
PARENS = set("()[]{}")
TERMINATING_SYMBOLS = set(";")
SEPARATING_SYMBOLS = set(",")

DATA_TYPES = {"int", "String", "char", "boolean", "float", "double", "long", "short", "void", "byte"}
KEYWORDS = {"if", "else", "return", "main", "case", "try", "catch", "do", "while", "for", "each", "import", "implements",
            "switch", "throw", "throws", "this", "public", "protected", "private", "new", "package", "break", "repeat",
            "def", "print", "input", "continue", "default", "const", "extends", "finally", "static"}
RESERVED_WORDS = {"fetch", "areaOf", "circle", "cubic", "distance", "ft", "in", "kg", "km", "l", "lbs", "m", "mg", "mm",
                  "perimeterOf", "repeat", "sphere", "sq", "triangle", "rectangle", "square", "volumeOf", "radius",
                  "circumference", "length", "height", "width", "side", "solve"}

# DFA-based token classification
def is_data_type(token):
    return token in DATA_TYPES

def is_keyword(token):
    return token in KEYWORDS

def is_reserved_word(token):
    return token in RESERVED_WORDS

def is_identifier(token):
    if token[0] not in LETTERS and token[0] != "_":
        return False
    return all(char in LETTERS.union(DIGITS).union({"_"}) for char in token)

def is_signed_integer(token):
    if token[0] == "-":
        token = token[1:]
    return token.isdigit()

def is_real_number(token):
    if token[0] == "-":
        token = token[1:]
    if "." in token:
        left, _, right = token.partition(".")
        return left.isdigit() and right.isdigit()
    return False

def is_string_literal(token):
    return token.startswith('"') and token.endswith('"') and '"' not in token[1:-1]

def is_character_literal(token):
    return len(token) == 3 and token.startswith("'") and token.endswith("'") and token[1] not in {"'", "\\"}

def is_boolean(token):
    return token in {"true", "false"}

def is_operator(token):
    if token in ARITHMETIC_OPERATORS:
        return "ARITHMETIC_OPERATOR"
    if token in RELATIONAL_OPERATORS:
        return "RELATIONAL_OPERATOR"
    if token in ASSIGNMENT_OPERATORS:
        return "ASSIGNMENT_OPERATOR"
    if token in LOGICAL_OPERATORS:
        return "LOGICAL_OPERATOR"
    return None

def is_symbol(token):
    if token in SYMBOLS:
        return "SPECIAL_SYMBOL"
    if token in PARENS:
        return "PARENTHESIS"
    if token in TERMINATING_SYMBOLS:
        return "TERMINATING_SYMBOL"
    if token in SEPARATING_SYMBOLS:
        return "SEPARATING_SYMBOL"
    return None

# Tokenizer function
def tokenize(input_string):
    tokens = []
    current_token = ""
    for char in input_string:
        if char in WHITESPACE:
            if current_token:
                tokens.append(current_token)
                current_token = ""
        elif char in SYMBOLS.union(ARITHMETIC_OPERATORS, RELATIONAL_OPERATORS, ASSIGNMENT_OPERATORS, LOGICAL_OPERATORS,
                                   PARENS, TERMINATING_SYMBOLS, SEPARATING_SYMBOLS):
            if current_token:
                tokens.append(current_token)
                current_token = ""
            tokens.append(char)
        else:
            current_token += char
    if current_token:
        tokens.append(current_token)
    return tokens

# Classify tokens
def classify_tokens(tokens):
    classified_tokens = []
    for token in tokens:
        if is_data_type(token):
            classified_tokens.append(("DATA_TYPE", token))
        elif is_keyword(token):
            classified_tokens.append(("KEYWORD", token))
        elif is_reserved_word(token):
            classified_tokens.append(("RESERVED_WORD", token))
        elif is_identifier(token):
            classified_tokens.append(("IDENTIFIER", token))
        elif is_signed_integer(token):
            classified_tokens.append(("SIGNED_INTEGER", token))
        elif is_real_number(token):
            classified_tokens.append(("REAL_NUMBER", token))
        elif is_string_literal(token):
            classified_tokens.append(("STRING_LITERAL", token))
        elif is_character_literal(token):
            classified_tokens.append(("CHARACTER_LITERAL", token))
        elif is_boolean(token):
            classified_tokens.append(("BOOLEAN", token))
        elif operator_type := is_operator(token):
            classified_tokens.append((operator_type, token))
        elif symbol_type := is_symbol(token):
            classified_tokens.append((symbol_type, token))
        else:
            raise ValueError(f"Unrecognized token: {token}")
    return classified_tokens

# Tokenize and classify the input
tokens = tokenize(file_content)
try:
    classified_tokens = classify_tokens(tokens)
except ValueError as e:
    print(f"Error during classification: {e}")
    sys.exit()

# Output results
output_file = file_path + "_tokens.txt"
with open(output_file, 'w') as out_file:
    for token_type, lexeme in classified_tokens:
        out_file.write(f"<{token_type}, {lexeme}>\n")

print(f"Tokenization complete. Results saved to {output_file}.")