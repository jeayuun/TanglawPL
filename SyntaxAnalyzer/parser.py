from tokenizer import Lexer, Token

class ASTNode:
    def __init__(self, type_, value=None, children=None):
        self.type = type_
        self.value = value
        self.children = children or []

    def __repr__(self, level=0, is_last=True):
        indent = "    " * level
        prefix = indent + ("└── " if is_last else "├── ")
        ret = f"{prefix}{self.type}: {self.value if self.value else ''}\n"

        for i, child in enumerate(self.children):
            ret += child.__repr__(level + 1, is_last=(i == len(self.children) - 1))
        return ret

#######################################
#               ERRORS                #
#######################################

class ParserError(Exception):
    def __init__(self, pos_start, pos_end, error_name, details):
        self.pos_start = pos_start
        self.pos_end = pos_end
        self.error_name = error_name
        self.details = details

    def get_location(self):
        if self.pos_start and self.pos_end:
            return f"Line {self.pos_start.ln + 1}, Column {self.pos_start.col + 1}-{self.pos_end.col + 1}"
        elif self.pos_start:
            return f"Line {self.pos_start.ln + 1}, Column {self.pos_start.col + 1}"
        return "Unknown location"

    def as_string(self):
        location = self.get_location()
        return f"{self.error_name}: {self.details}\n{location}"

class UnexpectedTokenError(ParserError):
    def __init__(self, pos_start, pos_end, details="Unexpected token"):
        super().__init__(pos_start, pos_end, "Unexpected Token", details)

class MissingParenthesisError(ParserError):
    def __init__(self, pos_start, pos_end):
        super().__init__(pos_start, pos_end, "Missing Parenthesis", "Expected closing parenthesis.")
    
#######################################
#               PARSER                #
#######################################

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
            raise ParserError(None, None, "No Tokens", "No tokens provided for parsing.")
        try:
            ast = self.expr()
            if self.current_token is not None:
                raise UnexpectedTokenError(self.current_token.pos_start, self.current_token.pos_end, f"Unexpected token: {self.current_token.type}")
            return ast
        except ParserError as e:
            self.display_error_table([e])
            return None

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
        if self.current_token is None:
            raise UnexpectedTokenError(
                pos_start=self.tokens[self.pos - 1].pos_start if self.pos > 0 else None,
                pos_end=self.tokens[self.pos - 1].pos_end if self.pos > 0 else None,
                details="Unexpected end of input; expected a number, parenthesis, or unary operator."
            )

        token = self.current_token

        if token.type in ('ADD_OPERATOR', 'SUBTRACT_OPERATOR', 'UNARY_OPERATOR'):
            op = token
            self.advance()
            factor_node = self.factor()
            return ASTNode(
                type_="Unary Operator",
                value=op.value,
                children=[factor_node]
            )

        if token.type in ('INTEGER', 'FLOAT'):
            self.advance()
            return ASTNode(type_="Number", value=token.value)

        if token.type == 'L_PARENTHESIS':
            start_pos = token.pos_start
            self.advance()
            node = self.expr()
            if self.current_token is None or self.current_token.type != 'R_PARENTHESIS':
                raise MissingParenthesisError(
                    pos_start=start_pos,
                    pos_end=self.current_token.pos_end if self.current_token else start_pos
                )
            self.advance()
            return ASTNode(type_="Parenthesized Expression", children=[node])

        raise UnexpectedTokenError(
            pos_start=token.pos_start if token else None,
            pos_end=token.pos_end if token else None,
            details=f"Unexpected token: {token.type}" if token else "Unexpected end of input."
        )

    def display_error_table(self, errors):
        error_table = PrettyTable()
        error_table.field_names = ["Error Type", "Details", "Location"]

        for error in errors:
            location = error.get_location() if error.pos_start else "Unknown location"
            error_table.add_row([
                error.error_name,
                error.details,
                location
            ])

        print(error_table)

#######################################
#                RUN                  #
#######################################

from prettytable import PrettyTable

def run_parser(input_text):
    lexer = Lexer("input", input_text)
    tokens, errors = lexer.make_tokens()

    if errors:
        print("Lexer Errors:")
        error_table = PrettyTable()
        error_table.field_names = ["Error Type", "Details", "Location"]
        for error in errors:
            error_table.add_row([
                error.error_name,
                error.details,
                f"Line {error.pos_start.ln + 1}, Column {error.pos_start.col + 1}"
            ])
        print(error_table)
        return

    parser = Parser(tokens)

    try:
        ast = parser.parse()
        if ast:
            print("Abstract Syntax Tree:")
            print(ast)
    except ParserError as e:
        print(e.as_string())

if __name__ == "__main__":
    while True:
        text = input("parse> ")
        if text.lower() in {"exit", "quit"}:
            break
        run_parser(text)
