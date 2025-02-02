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
            elif keyword in ('print', 'println'):
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
        

    def declaration(self, expect_semicolon=True):
        # First token is the data type
        data_type = self.current_token.value
        self.advance()
        declarators = []
        while True:
            # Expect a variable name (identifier)
            identifier_token = self.expect('IDENTIFIER', "Expected variable name")
            identifier_value = identifier_token.value

            # NEW: Check for a unit specifier immediately after the identifier.
            unit = None
            if self.current_token and self.current_token.type == 'L_PARENTHESIS':
                unit = self.parse_unit_specifier()

            initializer = None
            if self.current_token and self.current_token.type == 'ASSIGN_OP':
                self.advance()
                initializer = self.expr()

            # Create a Declarator node.
            declarator_node = ASTNode(type_="Declarator", value=identifier_value)
            if unit:
                # Add a UnitSpecifier as the first child.
                declarator_node.children.append(ASTNode(type_="UnitSpecifier", value=unit))
            if initializer:
                declarator_node.children.append(initializer)
            declarators.append(declarator_node)

            if self.current_token and self.current_token.type == 'SEPARATING_SYMBOL':
                self.advance()
            else:
                break

        if expect_semicolon:
            self.expect('SEMICOLON', "Expected ';' after declaration")
        return ASTNode(type_="VariableDeclaration", value=data_type, children=declarators)


    def parse_unit_specifier(self):
        """
        This method is called when the parser has just seen an L_PARENTHESIS after an identifier.
        It now handles the case where the lexer returns a unit token that already includes a trailing
        right parenthesis AND then an extra R_PARENTHESIS token.
        """
        # Consume the '(' token (caller already checked for it).
        self.advance()
        if self.current_token is None:
            raise UnexpectedTokenError(None, None, "Unexpected end of input while parsing unit specifier")
        
        # Get the unit token.
        unit_token_value = self.current_token.value
        if unit_token_value.endswith(")"):
            # If the unit token ends with ")", strip it.
            unit = unit_token_value[:-1]
            self.advance()  # Consume the token with the trailing ")"
            # If the very next token is an extra R_PARENTHESIS, consume it.
            if self.current_token and self.current_token.type == 'R_PARENTHESIS':
                self.advance()
        else:
            # Otherwise, take the token as the unit.
            unit = unit_token_value
            self.advance()  # Consume the unit token.
            # Now expect an explicit right parenthesis.
            self.expect('R_PARENTHESIS', "Expected ')' after unit specifier")
        return unit
    
    def output_statement(self):
        """
        Parses an output statement: println("Text {identifier}");
        Handles replacement fields inside strings.
        """
        self.consume("KEYWORD", "println")  # Expecting println keyword
        self.consume("L_PARENTHESIS")       # Expecting '('

        # Check for a string literal
        if self.match("STRING_LITERAL"):
            raw_string = self.previous().value  # Get the actual string value
            parts = self.process_string_with_replacements(raw_string)

            # Build the AST node
            output_node = OutputStatementNode(parts)

        else:
            raise SyntaxError("Expected a string literal in println().")

        self.consume("R_PARENTHESIS")  # Expecting ')'
        self.consume("SEMICOLON")      # Expecting ';'
        return output_node
    
    def process_string_with_replacements(self, raw_string):
        """
        Processes a string containing {identifier} and splits it into:
        - Literal Nodes for plain text.
        - Replacement Field Nodes for {identifier}.
        """
        import re
        pattern = r'\{([a-zA-Z_][a-zA-Z0-9_]*)\}'  # Matches {identifier}

        parts = []
        last_index = 0

        for match in re.finditer(pattern, raw_string):
            start, end = match.span()
            identifier = match.group(1)

            # Add preceding text as a Literal Node
            if start > last_index:
                parts.append(LiteralNode(raw_string[last_index:start]))

            # Add identifier as a Replacement Field Node
            parts.append(ReplacementFieldNode(identifier))

            last_index = end

        # Add any remaining text after the last match
        if last_index < len(raw_string):
            parts.append(LiteralNode(raw_string[last_index:]))

        return parts

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
        identifier = self.parse_member_access()  # Get member access chain

        # Check if this is a function call after member access
        if self.current_token and self.current_token.type == 'L_PARENTHESIS':
            return self.parse_function_call(identifier)

        # Handle assignment if needed
        if self.current_token and self.current_token.type == 'ASSIGN_OP':
            self.advance()
            value = self.expr()
            self.expect('SEMICOLON', "Expected ';' after assignment")
            return ASTNode(type_="Assignment", value=identifier.value, children=[value])

        # For simple identifier expressions
        self.expect('SEMICOLON', "Expected ';' after expression")
        return identifier  # Return the member access node directly

    def parse_member_access(self):
        # Accept tokens if type is IDENTIFIER, KEYWORD, or RESERVED_WORD.
        if self.current_token.type in ('IDENTIFIER', 'KEYWORD', 'RESERVED_WORD'):
            token = self.current_token
            self.advance()
        else:
            raise UnexpectedTokenError(
                self.current_token.pos_start if self.current_token else None,
                self.current_token.pos_end if self.current_token else None,
                "Expected identifier"
            )
        current_node = ASTNode(type_="Identifier", value=token.value)
        while self.current_token and self.current_token.type == 'ACCESSOR_SYMBOL':
            self.advance()  # Consume the '.' token
            if self.current_token.type not in ('IDENTIFIER', 'KEYWORD', 'RESERVED_WORD'):
                raise UnexpectedTokenError(
                    self.current_token.pos_start if self.current_token else None,
                    self.current_token.pos_end if self.current_token else None,
                    "Expected identifier after '.'"
                )
            member = self.current_token
            self.advance()
            current_node = ASTNode(
                type_="MemberAccess",
                value=member.value,
                children=[current_node]
            )
        return current_node

    def parse_function_call(self, identifier_node):
        self.expect('L_PARENTHESIS', "Expected '(' after function name")
        
        arguments = []
        if self.current_token.type != 'R_PARENTHESIS':
            while True:
                arguments.append(self.expr())
                if self.current_token.type != 'SEPARATING_SYMBOL':
                    break
                self.advance()

        self.expect('R_PARENTHESIS', "Expected ')' after function arguments")
        
        # Remove semicolon expectation here, let caller handle it
        return ASTNode(
            type_="FunctionCall",
            children=[identifier_node] + arguments
        )


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

    def parse_geometric_calculation(self, calculation_type):
        # Expect a dot and a shape identifier
        self.expect('ACCESSOR_SYMBOL', f"Expected '.' after '{calculation_type}'")
        
        # Allow RESERVED_WORD tokens as shape identifiers
        if self.current_token.type in ('IDENTIFIER', 'RESERVED_WORD'):
            shape = self.current_token.value
            self.advance()
        else:
            raise UnexpectedTokenError(
                self.current_token.pos_start,
                self.current_token.pos_end,
                f"Expected shape identifier after '{calculation_type}.'"
            )
        
        # Expect parentheses and parameters
        self.expect('L_PARENTHESIS', "Expected '(' after shape identifier")
        
        # Parse parameters
        parameters = []
        while self.current_token.type != 'R_PARENTHESIS':
            parameters.append(self.expr())
            if self.current_token.type == 'SEPARATING_SYMBOL':
                self.advance()
        
        self.expect('R_PARENTHESIS', "Expected ')' after parameters")
        
        # Return an AST node for the calculation
        return ASTNode(
            type_=f"{calculation_type.capitalize()}Calculation",
            value=shape,
            children=parameters
        )
    
    def parse_shape_expression(self, shape_type):
        # Expect parentheses and parameters
        self.expect('L_PARENTHESIS', f"Expected '(' after '{shape_type}'")
        
        # Parse parameters
        parameters = []
        while self.current_token.type != 'R_PARENTHESIS':
            parameters.append(self.expr())
            if self.current_token.type == 'SEPARATING_SYMBOL':
                self.advance()
        
        self.expect('R_PARENTHESIS', "Expected ')' after parameters")
        
        # Return an AST node for the shape
        return ASTNode(
            type_="Shape",
            value=shape_type,
            children=parameters
        )
    

    def parse_measurement_expression(self, measurement_type):
        # NEW: Check if the next token is an L_PARENTHESIS. If not, treat it as a simple identifier.
        if self.current_token and self.current_token.type != 'L_PARENTHESIS':
            # Not followed by '('; return as an Identifier node.
            return ASTNode(type_="Identifier", value=measurement_type)
        # Otherwise, parse it as a measurement expression.
        self.expect('L_PARENTHESIS', f"Expected '(' after '{measurement_type}'")
        parameters = []
        while self.current_token.type != 'R_PARENTHESIS':
            parameters.append(self.expr())
            if self.current_token.type == 'SEPARATING_SYMBOL':
                self.advance()
        self.expect('R_PARENTHESIS', "Expected ')' after parameters")
        return ASTNode(type_="Measurement", value=measurement_type, children=parameters)
    
    
    def parse_unit_expression(self, unit_type):
        # Expect a value to apply the unit to
        value = self.expr()
        
        # Return an AST node for the unit
        return ASTNode(
            type_="Unit",
            value=unit_type,
            children=[value]
        )
    
    def parse_fetch_expression(self):
        # Expect parentheses and parameters
        self.expect('L_PARENTHESIS', "Expected '(' after 'fetch'")
        
        # Parse parameters
        parameters = []
        while self.current_token.type != 'R_PARENTHESIS':
            parameters.append(self.expr())
            if self.current_token.type == 'SEPARATING_SYMBOL':
                self.advance()
        
        self.expect('R_PARENTHESIS', "Expected ')' after parameters")
        
        # Return an AST node for the fetch operation
        return ASTNode(
            type_="FetchOperation",
            children=parameters
        )

    def parse_setprecision_expression(self):
        # Expect parentheses and precision value
        self.expect('L_PARENTHESIS', "Expected '(' after 'setprecision'")
        precision = self.expr()
        self.expect('R_PARENTHESIS', "Expected ')' after precision value")
        
        # Return an AST node for the setprecision operation
        return ASTNode(
            type_="SetPrecision",
            children=[precision]
        )

    def parse_cubic_expression(self):
        # Expect parentheses and parameters
        self.expect('L_PARENTHESIS', "Expected '(' after 'cubic'")
        
        # Parse parameters
        parameters = []
        while self.current_token.type != 'R_PARENTHESIS':
            parameters.append(self.expr())
            if self.current_token.type == 'SEPARATING_SYMBOL':
                self.advance()
        
        self.expect('R_PARENTHESIS', "Expected ')' after parameters")
        
        # Return an AST node for the cubic operation
        return ASTNode(
            type_="CubicOperation",
            children=parameters
        )

    def factor(self):   
        token = self.current_token

        # Handle built-in or function call: if an identifier is immediately followed by '('
        if token.type in ('IDENTIFIER', 'KEYWORD', 'RESERVED_WORD'):
            nxt = self.peek()
            if nxt and nxt.type == 'L_PARENTHESIS':
                # Create a node for the function name and parse the function call.
                func_node = ASTNode(type_="Identifier", value=token.value)
                self.advance()  # consume the function name token
                return self.parse_function_call(func_node)
            else:
                return self.parse_member_access()
    
        # Handle reserved words
        if self.current_token and self.current_token.type == 'RESERVED_WORD':
            reserved_word = self.current_token.value
            
            # Geometric calculations
            if reserved_word in ('areaOf', 'perimeterOf', 'volumeOf'):
                self.advance()  # Consume the reserved word
                return self.parse_geometric_calculation(reserved_word)
            
            # Shapes
            elif reserved_word in ('circle', 'rectangle', 'square', 'triangle', 'sphere'):
                self.advance()  # Consume the reserved word
                return self.parse_shape_expression(reserved_word)
            
            # Measurements
            elif reserved_word in ('radius', 'height', 'width', 'length', 'side', 'distance', 'circumference'):
                self.advance()  # Consume the reserved word
                return self.parse_measurement_expression(reserved_word)
            
            # Units
            elif reserved_word in ('cm', 'ft', 'in', 'kg', 'km', 'l', 'lbs', 'm', 'mg', 'mm', 'sq'):
                self.advance()  # Consume the reserved word
                return self.parse_unit_expression(reserved_word)
            
            # Other operations
            elif reserved_word == 'fetch':
                self.advance()  # Consume the reserved word
                return self.parse_fetch_expression()
            elif reserved_word == 'setprecision':
                self.advance()  # Consume the reserved word
                return self.parse_setprecision_expression()
            elif reserved_word == 'cubic':
                self.advance()  # Consume the reserved word
                return self.parse_cubic_expression()
            
            else:
                raise UnexpectedTokenError(
                    self.current_token.pos_start,
                    self.current_token.pos_end,
                    f"Unsupported reserved word: {reserved_word}"
                )
        
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
            if not self.current_token or self.current_token.type != 'R_PARENTHESIS':
                raise UnexpectedTokenError(
                    pos_start=token.pos_start,
                    pos_end=self.current_token.pos_end if self.current_token else token.pos_start,
                    details="Expected closing parenthesis."
                )
            self.advance()  # Consume ')'
            return ASTNode(type_="Parenthesized Expression", children=[node])

        if token.type in ('IDENTIFIER', 'KEYWORD', 'RESERVED_WORD'):
            return self.parse_member_access()

        raise UnexpectedTokenError(
            pos_start=token.pos_start if token else None,
            pos_end=token.pos_end if token else None,
            details=f"Unexpected token: {token.type}" if token else "Unexpected end of input."
        )

    def peek(self):
        if self.pos + 1 < len(self.tokens):
            return self.tokens[self.pos + 1]
        return None
    
    def consume(self, expected_type, expected_value=None):
        """
        Consumes the current token if it matches the expected type (and value, if specified).
        Otherwise, raises an error indicating an unexpected token.
        """
        if self.current_token is None:
            raise SyntaxError("Unexpected end of input")
        
        # Change 'self.current_token.token' to 'self.current_token.type' (or the correct attribute name)
        if self.current_token.type != expected_type:
            raise SyntaxError(f"Unexpected token: {self.current_token.type}. Expected {expected_type}.")
        
        if expected_value and self.current_token.value != expected_value:
            raise SyntaxError(f"Unexpected token value: {self.current_token.value}. Expected {expected_value}.")
        
        # If we match the expected token, advance to the next one
        self.next_token()

        
class ReplacementFieldNode(ASTNode):
    def __init__(self, identifier):
        self.identifier = identifier

    def __repr__(self):
        return f"ReplacementField({self.identifier})"
        
class OutputStatementNode(ASTNode):
    def __init__(self, parts):
            self.parts = parts  # A mix of LiteralNode and ReplacementFieldNode

    def __repr__(self):
            return f"OutputStatement({self.parts})"

class LiteralNode(ASTNode):
    def __init__(self, value):
        self.value = value  # The string value of the literal

    def __repr__(self):
        return f"Literal({self.value})"


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