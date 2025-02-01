from tokenizer import Lexer, Token

class ASTNode:
    def __init__(self, type_, value=None, children=None):
        self.type = type_
        self.value = value
        self.children = children or []

    def __repr__(self, level=0, is_last=True):
        indent = "    " * level
        prefix = indent + ("└── " if is_last else "├── ")
        value_str = str(self.value) if self.value is not None else ""
        ret = f"{prefix}{self.type}: {value_str}\n"

        for i, child in enumerate(self.children):
            ret += child.__repr__(level + 1, is_last=(i == len(self.children) - 1))
        return ret
    

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
        return f"Syntax Error: {self.error_name}\n{location}\nDetails: {self.details}"

class UnexpectedTokenError(ParserError):
    def __init__(self, pos_start, pos_end, details="Unexpected token"):
        super().__init__(pos_start, pos_end, "Unexpected Token", details)

class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.current_token = None
        self.pos = -1
        self.had_error = False
        self.advance()

    def synchronize(self):
        while self.current_token and self.current_token.type not in [
            'SEMICOLON', 'R_CURLY', 'KEYWORD', 'DATA_TYPE', 'EOF'
        ]:
            self.advance()
        self.had_error = False

    def advance(self):
        self.pos += 1
        if self.pos < len(self.tokens):
            self.current_token = self.tokens[self.pos]
        else:
            self.current_token = None

    def parse(self):
        if not self.tokens:
            raise ParserError(None, None, "No Tokens", "No tokens provided for parsing.")
        try:
            ast = self.program()
            if self.current_token is not None:
                raise UnexpectedTokenError(
                    self.current_token.pos_start,
                    self.current_token.pos_end,
                    f"Unexpected token: {self.current_token.type}"
                )
            return ast
        except ParserError as e:
            print(e.as_string())
            return None

    def program(self):
        statements = []
        while self.current_token is not None and self.current_token.type != 'EOF':
            statements.append(self.statement())
        return ASTNode(type_="Program", children=statements)

    def statement(self):
        if self.current_token.type == 'DATA_TYPE':
            return self.declaration()
        elif self.current_token.type == 'KEYWORD':
            keyword = self.current_token.value
            if keyword in ('while', 'for', 'repeat'):
                return self.parse_iterative_statement()
            elif keyword == 'if':
                return self.parse_conditional_statement()
            elif keyword == 'print':
                return self.output_statement()
            elif keyword == 'input':
                return self.input_statement()
            else:
                raise UnexpectedTokenError(
                    self.current_token.pos_start,
                    self.current_token.pos_end,
                    f"Unexpected keyword: {keyword}"
                )
        elif self.current_token.type == 'IDENTIFIER':
            return self.assignment_or_function_call()
        else:
            return self.expr()

    def declaration(self, expect_semicolon=True):  # Add optional parameter
        data_type = self.current_token.value
        self.advance()

        declarators = []
        while True:
            identifier = self.expect('IDENTIFIER', "Expected variable name").value
            initializer = None
            if self.current_token and self.current_token.type == 'ASSIGN_OP':
                self.advance()
                initializer = self.expr()

            declarator_node = ASTNode(type_="Declarator", value=identifier)
            if initializer:
                declarator_node.children.append(initializer)
            declarators.append(declarator_node)

            if self.current_token and self.current_token.type == 'SEPARATING_SYMBOL':
                self.advance()
            else:
                break

        if expect_semicolon:  # Only expect semicolon if flagged
            self.expect('SEMICOLON', "Expected ';' after declaration")
        return ASTNode(type_="VariableDeclaration", value=data_type, children=declarators)

    def output_statement(self):
        keyword = self.current_token
        self.advance()
        self.expect('L_PARENTHESIS', "Expected '('")
        expressions = []
        while self.current_token.type != 'R_PARENTHESIS':
            expressions.append(self.expr())
            if self.current_token.type == 'SEPARATING_SYMBOL':
                self.advance()
        self.advance()
        return ASTNode(type_="OutputStatement", value=keyword.value, children=expressions)

    def input_statement(self):
        self.advance()
        self.expect('L_PARENTHESIS', "Expected '('")
        self.expect('R_PARENTHESIS', "Expected ')'")
        self.expect('SEMICOLON', "Expected ';' after input statement")
        return ASTNode(type_="InputStatement")

    def parse_iterative_statement(self):
        keyword = self.current_token.value
        self.advance()

        if keyword == 'while':
            return self.parse_while_loop()
        elif keyword == 'for':
            return self.parse_for_loop()
        elif keyword == 'repeat':
            return self.parse_repeat_loop()
        else:
            raise UnexpectedTokenError(
                self.current_token.pos_start,
                self.current_token.pos_end,
                f"Unsupported loop keyword: {keyword}"
            )

    def parse_while_loop(self):
        self.expect('L_PARENTHESIS', "Expected '(' after 'while'")
        condition = self.expr()
        self.expect('R_PARENTHESIS', "Expected ')' after condition")
        body = self.block()
        return ASTNode(type_="WhileLoop", children=[condition, body])

    def parse_for_loop(self):
        self.expect('L_PARENTHESIS', "Expected '(' after 'for'")
        # Parse initializer without expecting semicolon in declaration
        if self.current_token.type == 'DATA_TYPE':
            initializer = self.declaration(expect_semicolon=False)  # Pass False here
        else:
            initializer = self.assignment_or_function_call()
        self.expect('SEMICOLON', "Expected ';' after initializer")  # Now expects correctly
        condition = self.expr()
        self.expect('SEMICOLON', "Expected ';' after condition")
        update = self.parse_update_expression()
        self.expect('R_PARENTHESIS', "Expected ')' after for clauses")
        body = self.block()
        return ASTNode(type_="ForLoop", children=[initializer, condition, update, body])

    def parse_update_expression(self):
        identifier = self.expect('IDENTIFIER', "Expected identifier in update expression").value
        if self.current_token.type in ('INCREMENT_UNARY_OP', 'DECREMENT_UNARY_OP'):
            op = self.current_token.value
            self.advance()
            return ASTNode(type_="Update", value=op, children=[ASTNode(type_="Identifier", value=identifier)])
        elif self.current_token.type in ('ADD_ASSIGN_OP', 'SUBT_ASSIGN_OP', 'MULTIPLY_ASSIGN_OP', 'DIV_ASSIGN_OP', 'MOD_ASSIGN_OP'):
            op = self.current_token.value
            self.advance()
            value = self.expr()
            return ASTNode(type_="Assignment", value=op, children=[
                ASTNode(type_="Identifier", value=identifier),
                value
            ])
        else:
            raise UnexpectedTokenError(
                self.current_token.pos_start,
                self.current_token.pos_end,
                f"Expected increment/decrement or assignment operator, got {self.current_token.type}"
            )

    def parse_repeat_loop(self):
        times = self.expr()
        if self.current_token and self.current_token.type == 'KEYWORD' and self.current_token.value == 'times':
            self.advance()
        else:
            raise UnexpectedTokenError(
                self.current_token.pos_start if self.current_token else None,
                self.current_token.pos_end if self.current_token else None,
                "Expected 'times' after repeat count"
            )
        body = self.block()
        return ASTNode(type_="RepeatLoop", children=[times, body])

    def block(self):
        self.expect('L_CURLY', "Expected '{' to start block")
        statements = []
        while self.current_token.type != 'R_CURLY':
            statements.append(self.statement())
            if self.current_token and self.current_token.type == 'SEMICOLON':
                self.advance()
        self.expect('R_CURLY', "Expected '}' to end block")
        return ASTNode(type_="Block", children=statements)

    def expect(self, token_type, error_message):
        if self.current_token and self.current_token.type == token_type:
            token = self.current_token
            self.advance()
            return token
        raise UnexpectedTokenError(
            self.current_token.pos_start if self.current_token else None,
            self.current_token.pos_end if self.current_token else None,
            error_message
        )

    def parse_conditional_statement(self):
        self.advance()
        self.expect('L_PARENTHESIS', "Expected '(' after 'if'")
        condition = self.parse_condition()
        self.expect('R_PARENTHESIS', "Expected ')' after condition")
        true_block = self.parse_statement_block()
        false_block = None
        if self.current_token and self.current_token.type == 'KEYWORD':
            if self.current_token.value == 'else':
                self.advance()
                if self.current_token.value == 'if':
                    false_block = self.parse_conditional_statement()
                else:
                    false_block = self.parse_statement_block()
        return ASTNode(type_="ConditionalStatement", children=[
            ASTNode(type_="IfClause", children=[condition, true_block]),
            false_block
        ])

    def parse_statement_block(self):
        if self.current_token.type == 'L_CURLY':
            return self.block()
        else:
            stmt = self.statement()
            return ASTNode(type_="Block", children=[stmt])

    def parse_condition(self):
        return self.logical_expr()

    def logical_expr(self):
        left = self.expr()
        while self.current_token and self.current_token.type == 'LOGICAL_OPERATOR':
            op = self.current_token
            self.advance()
            right = self.expr()
            left = ASTNode(type_="LogicalOp", value=op.value, children=[left, right])
        return left

    def assignment_or_function_call(self):
        identifier = self.expect('IDENTIFIER', "Expected identifier")

        if self.current_token and self.current_token.type == 'L_PARENTHESIS':
            return self.parse_function_call(identifier)

        if self.current_token and self.current_token.type == 'ASSIGN_OP':
            self.advance()
            value = self.expr()
            self.expect('SEMICOLON', "Expected ';' after assignment")
            return ASTNode(type_="Assignment", value=identifier.value, children=[value])

        self.expect('SEMICOLON', "Expected ';' after expression")
        return ASTNode(type_="Identifier", value=identifier.value)

    def parse_function_call(self, identifier):
        self.expect('L_PARENTHESIS', "Expected '(' after function name")
        
        arguments = []
        if self.current_token.type != 'R_PARENTHESIS':
            while True:
                arguments.append(self.expr())
                if self.current_token.type == 'SEPARATING_SYMBOL':
                    self.advance()
                else:
                    break

        self.expect('R_PARENTHESIS', "Expected ')' after function arguments")
        self.expect('SEMICOLON', "Expected ';' after function call")
        
        return ASTNode(type_="FunctionCall", value=identifier.value, children=arguments) # last change yung function


    def expr(self):
        relational_ops = [
            'LESS_THAN', 'GREATER_THAN', 'LESS_THAN_OR_EQUAL_TO',
            'GREATER_THAN_OR_EQUAL_TO', 'EQUAL_TO', 'NOT_EQUAL_TO'
        ]
        left = self.term()
        while self.current_token and (
            self.current_token.type in ['ARITHMETIC_OPERATOR'] + relational_ops or
            (self.current_token.type == 'LOGICAL_OPERATOR' and 
            self.current_token.value in ['&&', '||'])
        ):
            op = self.current_token
            self.advance()
            right = self.term()
            left = ASTNode(type_="BinaryOp", value=op.value, children=[left, right])
        return left

    def term(self):
        left = self.factor()
        while self.current_token and (
            self.current_token.type == 'ARITHMETIC_OPERATOR' and 
            self.current_token.value in ('*', '/', '%')  # Ensure '%' is included
        ):
            op = self.current_token
            self.advance()
            right = self.factor()
            left = ASTNode(type_="BinaryOp", value=op.value, children=[left, right])
        return left

    def factor(self):
        if self.current_token and self.current_token.type == 'LOGICAL_OPERATOR' and self.current_token.value == '!':
            op = self.current_token
            self.advance()
            node = self.factor()
            return ASTNode(type_="UnaryLogicalOp", value=op.value, children=[node])

        token = self.current_token

        if token.type in ('ADD_OPERATOR', 'SUBTRACT_OPERATOR', 'UNARY_OPERATOR'):
            op = token
            self.advance()
            factor_node = self.factor()
            return ASTNode(type_="Unary Operator", value=op.value, children=[factor_node])

        if token.type in ('INTEGER', 'FLOAT', 'STRING_LITERAL', 'CHAR_LITERAL'):
            self.advance()
            return ASTNode(type_="Literal", value=token.value)

        if token.type == 'L_PARENTHESIS':
            self.advance()  # Consume '('
            node = self.expr()
            # Check for closing parenthesis
            if not self.current_token or self.current_token.type != 'R_PARENTHESIS':
                raise UnexpectedTokenError(
                    pos_start=token.pos_start,
                    pos_end=self.current_token.pos_end if self.current_token else token.pos_start,
                    details="Expected closing parenthesis."
                )
            self.advance()  # Consume ')'
            return ASTNode(type_="Parenthesized Expression", children=[node])

        if token.type == 'IDENTIFIER':
            identifier = token.value
            self.advance()
            return ASTNode(type_="Identifier", value=identifier)

        raise UnexpectedTokenError(
            pos_start=token.pos_start if token else None,
            pos_end=token.pos_end if token else None,
            details=f"Unexpected token: {token.type}" if token else "Unexpected end of input."
        )

from prettytable import PrettyTable

def run_parser(input_text):
    lexer = Lexer("input", input_text)
    tokens, errors = lexer.make_tokens()
    if errors:
        print("Lexer Errors:")
        for error in errors:
            print(error.as_string())
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