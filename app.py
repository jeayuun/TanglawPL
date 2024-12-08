import re

class TokenType:
    IDENTIFIER = "IDENTIFIER"
    NUMBER = "NUMBER"
    OPERATOR = "OPERATOR"
    SEPARATOR = "SEPARATOR"
    KEYWORD = "KEYWORD"
    STRING = "STRING"
    COMMENT = "COMMENT"
    UNKNOWN = "UNKNOWN"

class Token:
    def __init__(self, type, value, line, column):
        self.type = type
        self.value = value
        self.line = line
        self.column = column

    def __str__(self):
        return f"Token(type={self.type}, value={self.value}, line={self.line}, column={self.column})"

class LexicalAnalyzer:
    def __init__(self, source_code):
        self.source_code = source_code
        self.tokens = []
        self.current_line = 1
        self.current_column = 1

    def analyze(self):
        position = 0
        length = len(self.source_code)

        patterns = {
            "KEYWORD": r"\b(if|else|while|for|return|int|float|char|void)\b",
            "IDENTIFIER": r"\b[a-zA-Z_][a-zA-Z0-9_]*\b",
            "NUMBER": r"\b\d+(\.\d+)?\b",
            "OPERATOR": r"[+\-*/=<>!&|]+",
            "SEPARATOR": r"[(){}[\],;]",
            "STRING": r"\".*?\"|\'.*?\'",
            "COMMENT": r"//.*?$|/\*.*?\*/",
        }

        # Merge patterns into one regex
        combined_pattern = "|".join(f"(?P<{name}>{pattern})" for name, pattern in patterns.items())

        while position < length:
            # Match the combined regex pattern
            match = re.match(combined_pattern, self.source_code[position:], re.DOTALL)

            if match:
                for name, pattern in patterns.items():
                    token_value = match.group(name)
                    if token_value:
                        token_type = name
                        token_length = len(token_value)

                        if token_type == "COMMENT":
                            # Skip comments
                            break

                        token = Token(token_type, token_value, self.current_line, self.current_column)
                        self.tokens.append(token)

                        # Update position and column
                        position += token_length
                        self.current_column += token_length

                        # Handle new lines in strings or multi-line comments
                        if "\n" in token_value:
                            lines = token_value.split("\n")
                            self.current_line += len(lines) - 1
                            self.current_column = len(lines[-1]) + 1

                        break
                else:
                    # Unknown token, consume one character
                    unknown_char = self.source_code[position]
                    self.tokens.append(Token(TokenType.UNKNOWN, unknown_char, self.current_line, self.current_column))
                    position += 1
                    self.current_column += 1
            else:
                # Skip whitespace
                if self.source_code[position].isspace():
                    if self.source_code[position] == '\n':
                        self.current_line += 1
                        self.current_column = 1
                    else:
                        self.current_column += 1
                    position += 1
                else:
                    # Handle unknown characters
                    unknown_char = self.source_code[position]
                    self.tokens.append(Token(TokenType.UNKNOWN, unknown_char, self.current_line, self.current_column))
                    position += 1
                    self.current_column += 1

    def get_tokens(self):
        return self.tokens

# Example usage
if __name__ == "__main__":
    code = """
    int main() {
        // This is a comment
        int x = 10;
        if (x > 5) {
            x = x + 1;
        }
        return x;
    }
    """

    analyzer = LexicalAnalyzer(code)
    analyzer.analyze()

    for token in analyzer.get_tokens():
        print(token)