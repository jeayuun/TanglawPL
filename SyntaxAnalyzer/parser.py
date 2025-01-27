from tokenizer import Lexer, Token

class ASTNode:
    def __init__(self, type_, value=None, children=None):
        self.type = type_
        self.value = value
        self.children = children or []

    def __repr__(self, level=0, is_last=True):
        symbol = "└── " if is_last else "├── "
        ret = ("    " * (level - 1) + (symbol if level > 0 else "")) + f"{self.type}: {self.value if self.value is not None else ''}\n"
        for i, child in enumerate(self.children):
            ret += child.__repr__(level + 1, is_last=(i == len(self.children) - 1))
        return ret

class ParserError(Exception):
    def __init__(self, message):
        super().__init__(message)

class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.current_token = None
        self.pos = -1
        self.advance()

    def advance(self):
        self.pos += 1
        self.current_token = self.tokens[self.pos] if self.pos < len(self.tokens) else None

    def parse(self):
        if not self.tokens:
            raise ParserError("No tokens to parse.")
        ast = self.expr()
        if self.current_token is not None:
            raise ParserError(f"Unexpected token: {self.current_token}")
        return ast

    def expr(self):
        left = self.term()
        while self.current_token is not None and self.current_token.type in ('ADD_OPERATOR', 'SUBTRACT_OPERATOR'):
            op = self.current_token
            self.advance()
            right = self.term()
            left = ASTNode(
                type_="Expression",
                children=[
                    left,
                    ASTNode(type_="Operator", value=op.value),
                    right
                ]
            )
        return left

    def term(self):
        left = self.factor()
        while self.current_token is not None and self.current_token.type in ('MULTIPLY_OP', 'DIVIDE_OP', 'MODULO_OP'):
            op = self.current_token
            self.advance()
            right = self.factor()
            left = ASTNode(
                type_="Term",
                children=[
                    left,
                    ASTNode(type_="Operator", value=op.value),
                    right
                ]
            )
        return left

    def factor(self):
        token = self.current_token

        if token.type in ('INTEGER', 'FLOAT'):
            self.advance()
            return ASTNode(type_="Number", value=token.value)

        if token.type == 'L_PARENTHESIS':
            self.advance()
            node = self.expr()
            if self.current_token.type != 'R_PARENTHESIS':
                raise ParserError("Expected closing parenthesis.")
            self.advance()
            return ASTNode(type_="Parenthesized Expression", children=[node])

        raise ParserError(f"Unexpected token: {token}")

def run_parser(input_text):
    lexer = Lexer("input", input_text)
    tokens, errors = lexer.make_tokens()

    if errors:
        for error in errors:
            print(error.as_string())
        return

    parser = Parser(tokens)

    try:
        ast = parser.parse()
        print("Abstract Syntax Tree:")
        print(ast)
    except ParserError as e:
        print(f"Parser Error: {e}")

if __name__ == "__main__":
    while True:
        text = input("calc> ")
        if text.lower() in {"exit", "quit"}:
            break
        run_parser(text)
