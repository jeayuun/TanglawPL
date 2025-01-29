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
            ast = self.program()
            if self.current_token is not None:
                raise UnexpectedTokenError(self.current_token.pos_start, self.current_token.pos_end, f"Unexpected token: {self.current_token.type}")
            return ast
        except ParserError as e:
            print(e.as_string())
            return None

    def program(self):
        statements = []
        while self.current_token is not None:
            statements.append(self.statement())
        return ASTNode(type_="Program", children=statements)

    def statement(self):
        if self.current_token.type == 'DATA_TYPE':
            return self.declaration()
        elif self.current_token.type == 'KEYWORD':
            if self.current_token.value in ('if', 'while', 'for'):
                return self.control_structure()
            elif self.current_token.value in ('print', 'println'):
                return self.output_statement()
        elif self.current_token.type == 'IDENTIFIER':
            return self.assignment_or_function_call()
        else:
            return self.expr()

    def declaration(self):
        data_type = self.current_token
        self.advance()
        identifier = self.current_token
        self.advance()

        if self.current_token.type == 'ASSIGN_OP':
            self.advance()
            value = self.expr()
            return ASTNode(type_="VariableDeclaration", value=identifier.value, children=[value])
        
        return ASTNode(type_="VariableDeclaration", value=identifier.value)

    def output_statement(self):
        keyword = self.current_token
        self.advance()
        if self.current_token.type != 'L_PARENTHESIS':
            raise UnexpectedTokenError(self.current_token.pos_start, self.current_token.pos_end, "Expected '('")
        self.advance()
        expressions = []
        while self.current_token.type != 'R_PARENTHESIS':
            expressions.append(self.expr())
            if self.current_token.type == 'SEPARATING_SYMBOL':
                self.advance()
        self.advance()
        return ASTNode(type_="OutputStatement", value=keyword.value, children=expressions)

    def control_structure(self):
        keyword = self.current_token
        self.advance()
        if keyword.value == 'if':
            condition = self.expr()
            body = self.block()
            return ASTNode(type_="IfStatement", children=[condition, body])
        elif keyword.value == 'while':
            condition = self.expr()
            body = self.block()
            return ASTNode(type_="WhileStatement", children=[condition, body])
        elif keyword.value == 'for':
            self.advance()
            initializer = self.statement()
            condition = self.expr()
            update = self.statement()
            body = self.block()
            return ASTNode(type_="ForStatement", children=[initializer, condition, update, body])

    def assignment_or_function_call(self):
        identifier = self.current_token
        self.advance()
        if self.current_token.type == 'ASSIGN_OP':
            self.advance()
            value = self.expr()
            return ASTNode(type_="Assignment", value=identifier.value, children=[value])
        elif self.current_token.type == 'L_PARENTHESIS':
            self.advance()
            args = []
            while self.current_token.type != 'R_PARENTHESIS':
                args.append(self.expr())
                if self.current_token.type == 'SEPARATING_SYMBOL':
                    self.advance()
            self.advance()
            return ASTNode(type_="FunctionCall", value=identifier.value, children=args)

    def block(self):
        if self.current_token.type != 'L_CURLY':
            raise UnexpectedTokenError(self.current_token.pos_start, self.current_token.pos_end, "Expected '{'")
        self.advance()
        statements = []
        while self.current_token.type != 'R_CURLY':
            statements.append(self.statement())
        self.advance()
        return ASTNode(type_="Block", children=statements)

    def expr(self):
        """Parse an expression."""
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
        """Parse a term."""
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
        """Parse a factor."""
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

        if token.type in ('INTEGER', 'FLOAT', 'STRING_LITERAL', 'CHAR_LITERAL'):
            self.advance()
            return ASTNode(type_="Literal", value=token.value)

        if token.type == 'L_PARENTHESIS':
            self.advance()
            node = self.expr()
            if self.current_token is None or self.current_token.type != 'R_PARENTHESIS':
                raise UnexpectedTokenError(
                    pos_start=token.pos_start,
                    pos_end=self.current_token.pos_end if self.current_token else token.pos_start,
                    details="Expected closing parenthesis."
                )
            self.advance()
            return ASTNode(type_="Parenthesized Expression", children=[node])

        raise UnexpectedTokenError(
            pos_start=token.pos_start if token else None,
            pos_end=token.pos_end if token else None,
            details=f"Unexpected token: {token.type}" if token else "Unexpected end of input."
        )

#######################################
#                RUN                  #
#######################################

from prettytable import PrettyTable

def run_parser(input_text):
    lexer = Lexer("input", input_text)
    tokens, errors = lexer.make_tokens()
    if errors:
        print("Lexer Errors:")
        return
    parser = Parser(tokens)
    ast = parser.parse()
    if ast:
        print("Abstract Syntax Tree:")
        print(ast)

if __name__ == "__main__":
    while True:
        text = input("parse enter text here> ")
        if text.lower() in {"exit", "quit"}:
            break
        run_parser(text)
