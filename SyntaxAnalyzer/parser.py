from tokenizer import Lexer, Token

class ASTNode:
    def __init__(self, type_, value=None, children=None, pos_start=None, pos_end=None):
        self.type = type_
        self.value = value
        self.children = children or []
        self.pos_start = pos_start  # Track start position
        self.pos_end = pos_end      # Track end position

    def __repr__(self, level=0, is_last=True):
        indent = "    " * level
        prefix = indent + ("└── " if is_last else "├── ")
        value_str = str(self.value) if self.value is not None else ""
        ret = f"{prefix}{self.type}: {value_str}\n"

        for i, child in enumerate(self.children):
            ret += child.__repr__(level + 1, is_last=(i == len(self.children) - 1))
        return ret

###########################################
#            ERROR HANDLER                #
###########################################

class ParserError(Exception):
    def __init__(self, pos_start, pos_end, error_name, details):
        self.pos_start = pos_start
        self.pos_end = pos_end
        self.error_name = error_name
        self.details = details

    #method that will report where the errors line is
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
    def __init__(self, pos_start, pos_end, details="Syntax Error"):
        super().__init__(pos_start, pos_end, "Syntax Error", details)

#error handling stuff
class TypeError(ParserError):
    def __init__(self, pos_start, pos_end, details):
        super().__init__(pos_start, pos_end, "Type Mismatch", details)
    
##################################
#            PARSER              #
##################################

class ReplacementFieldNode(ASTNode):
    def __init__(self, identifier):
        super().__init__(type_="ReplacementField", value=identifier)

class LiteralNode(ASTNode):
    def __init__(self, value):
        super().__init__(type_="Literal", value=value)

class OutputStatementNode(ASTNode):
    def __init__(self, parts):
        super().__init__(type_="OutputStatement", children=parts)
        self.parts = parts  # Redundant but kept for clarity

class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.current_token = None
        self.pos = -1
        self.had_error = False
        self.syntax_errors = []  # Initialize syntax_errors list
        self.previous_token = None  # Track previous token
        self.advance()

    def advance(self):
            self.pos += 1
            if self.pos < len(self.tokens):
                self.current_token = self.tokens[self.pos]
            else:
                self.current_token = None
                
    def parse(self):
        self.had_error = False
        ast = self.program()
        # Check for unexpected tokens at the end (if recovery left some)
        if self.current_token is not None and self.current_token.type != 'EOF':
            self.syntax_errors.append({
                "Error Type": "Unexpected Token",
                "Details": f"Unexpected token: {self.current_token.type}",
                "Location": self.current_token.pos_start.get_location() if self.current_token.pos_start else "Unknown"
            })
            
        
        # Return AST only if no errors were flagged.
        return ast if not self.syntax_errors else None
        

    def program(self):
        statements = []
        while self.current_token is not None and self.current_token.type != 'EOF':
            try:
                statements.append(self.statement())
            except ParserError as e:
                # Add error to syntax_errors list
                self.syntax_errors.append({
                    "Error Type": e.error_name,
                    "Details": e.details,
                    "Location": e.get_location()
                })
                # Recover by synchronizing to the next statement
                self.synchronize()
        return ASTNode(type_="Program", children=statements)
    
    def synchronize(self):
        # Skip tokens until a statement boundary is found (e.g., ';', '}', or keywords)
        while self.current_token is not None:
            if self.current_token.type in ('SEMICOLON', 'R_CURLY'):
                self.advance()
                break
            # Check if the next token is a statement starter (e.g., 'if', 'while', etc.)
            if self.current_token.type in ('KEYWORD', 'DATA_TYPE', 'IDENTIFIER'):
                break
            self.advance()

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
        data_type_pos = self.current_token.pos_start  # Track data type position
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

            #error handler
            initializer = None
            if self.current_token and self.current_token.type == 'ASSIGN_OP':
                self.advance()
                initializer = self.expr()

                # Type Checking Logic
                if initializer.type == "Literal" or initializer.type == "CHAR_LITERAL":
                    if data_type == 'int':
                        if initializer.type == "CHAR_LITERAL" or not isinstance(initializer.value, (int, float)):
                            raise TypeError(
                                initializer.pos_start,
                                initializer.pos_end,
                                f"Cannot assign {initializer.value} of type '{initializer.value.__class__.__name__}' to '{data_type}'"
                            )
                    elif data_type == 'char':
                        if initializer.type != "CHAR_LITERAL" and not isinstance(initializer.value, str):
                            raise TypeError(
                                initializer.pos_start,
                                initializer.pos_end,
                                f"Cannot assign {initializer.value} of type '{initializer.value.__class__.__name__}' to '{data_type}'"
                            )
                
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

        #error hadnler
        if expect_semicolon:
            self.expect('SEMICOLON', "Expected ';' after declaration")
        return ASTNode(
            type_="VariableDeclaration",
            value=data_type,
            children=declarators,
            pos_start=data_type_pos,
            pos_end=self.current_token.pos_end if self.current_token else data_type_pos
        )


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
    # Check for 'println' or 'print' keyword
        if not (self.current_token and self.current_token.type == 'KEYWORD' and self.current_token.value in ('println', 'print')):
            raise UnexpectedTokenError(
                self.current_token.pos_start if self.current_token else None,
                self.current_token.pos_end if self.current_token else None,
                "Expected 'println' or 'print' keyword"
            )
        keyword = self.current_token.value
        self.advance()  # Consume the keyword

        self.expect('L_PARENTHESIS', "Expected '(' after output keyword")

        parts = []  # This will hold the literal and replacement nodes

        # Expect a string literal first
        if self.current_token.type != 'STRING_LITERAL':
            raise UnexpectedTokenError(
                self.current_token.pos_start,
                self.current_token.pos_end,
                "Expected string literal in output statement"
            )
        # Create a literal node from the string literal token.
        literal_value = self.current_token.value
        parts.append(LiteralNode(literal_value))
        self.advance()  # Consume the STRING_LITERAL

        # Now check for any replacement field tokens that might follow.
        # Our lexer produces L_REPFIELD, then an IDENTIFIER, then R_REPFIELD.
        while self.current_token and self.current_token.type == 'L_REPFIELD':
            self.advance()  # Consume the '{'
            if self.current_token.type != 'IDENTIFIER':
                raise UnexpectedTokenError(
                    self.current_token.pos_start,
                    self.current_token.pos_end,
                    "Expected identifier after '{' in interpolation"
                )
            identifier_value = self.current_token.value
            self.advance()  # Consume the identifier

            self.expect('R_REPFIELD', "Expected '}' after replacement field")

            # Create a replacement field node
            parts.append(ReplacementFieldNode(identifier_value))

            # Optionally, if your language allows literal text after a replacement field,
            # you might check if the next token is a STRING_LITERAL and add it as another literal node.
            # For example:
            if self.current_token and self.current_token.type == 'STRING_LITERAL':
                parts.append(LiteralNode(self.current_token.value))
                self.advance()

        # Now we expect the closing parenthesis.
        self.expect('R_PARENTHESIS', "Expected ')' after string literal/interpolation")
        self.expect('SEMICOLON', "Expected ';' after output statement")

        return OutputStatementNode(parts)
    
    def process_string_with_replacements(self, raw_string):
        import re
        pattern = r'\{([a-zA-Z_][a-zA-Z0-9_]*)\}'
        parts = []
        last_idx = 0

        for match in re.finditer(pattern, raw_string):
            start, end = match.span()
            literal_part = raw_string[last_idx:start]
            if literal_part:
                parts.append(LiteralNode(literal_part))
            identifier = match.group(1)
            parts.append(ReplacementFieldNode(identifier))
            last_idx = end

        # Add remaining literal part
        if last_idx < len(raw_string):
            parts.append(LiteralNode(raw_string[last_idx:]))

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

        # Check for 'else' clause
        if self.current_token and self.current_token.type == 'KEYWORD' and self.current_token.value == 'else':
            self.advance()
            if self.current_token and self.current_token.value == 'if':
                false_block = self.parse_conditional_statement()
            else:
                false_block = self.parse_statement_block()

        # Build children list without None
        children = [ASTNode(type_="IfClause", children=[condition, true_block])]
        if false_block is not None:
            children.append(false_block)

        return ASTNode(type_="ConditionalStatement", children=children)
    
    
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
        # Parse the left-hand side (must be an identifier or member access)
        identifier = self.parse_member_access()

        # Check if this is a function call (e.g., areaOf.Rectangle(...))
        if self.current_token and self.current_token.type == 'L_PARENTHESIS':
            return self.parse_function_call(identifier)

        # Handle assignment (e.g., x = 5)
        if self.current_token and self.current_token.type == 'ASSIGN_OP':
            self.advance()  # Consume '='
            value = self.expr()
            self.expect('SEMICOLON', "Expected ';' after assignment")
            return ASTNode(type_="Assignment", value=identifier.value, children=[value])

        # If not an assignment or function call, treat as an identifier expression
        self.expect('SEMICOLON', "Expected ';' after expression")
        return identifier

    def parse_member_access(self):
        unit_specifiers = ('cm', 'ft', 'in', 'kg', 'km', 'l', 'lbs', 'm', 'mg', 'mm', 'sq')
        geometric_words = ('areaOf', 'volumeOf', 'perimeterOf')

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
        
        # dito ung line na inaayos ko
        if token.value in unit_specifiers:
            current_node = ASTNode(type_="UnitSpecifier", value=token.value)
        elif token.value in geometric_words:
            current_node = ASTNode(type_="Geometric", value=token.value)
        elif token.value == 'input':
            current_node = ASTNode(type_="Function", value=token.value)
        else:
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
        """
        Parses expressions, including function calls and assignments.
        - Example: ARectangle = areaOf.rectangle(L, W);
        - Example: x = myFunction(5, y + 2);
        """
        relational_ops = [
            'LESS_THAN', 'GREATER_THAN', 'LESS_THAN_OR_EQUAL_TO',
            'GREATER_THAN_OR_EQUAL_TO', 'EQUAL_TO', 'NOT_EQUAL_TO'
        ]

        # ✅ Parse left-hand side (could be a function call or identifier)
        left = self.term()

        # ✅ Check if it's a function call (Fix: Now `expr()` can handle function calls!)
        if self.current_token and self.current_token.type == 'L_PARENTHESIS':
            left = self.parse_function_call(left)  # Now correctly recognizes function calls!

        # ✅ Handle binary operators (e.g., x + y, a == b)
        while self.current_token and (
            self.current_token.type in ['ARITHMETIC_OPERATOR'] + relational_ops or
            (self.current_token.type == 'LOGICAL_OPERATOR' and self.current_token.value in ['&&', '||'])
        ):
            op = self.current_token
            self.advance()
            right = self.term()

            # ✅ Ensure right-hand side is parsed correctly
            if self.current_token and self.current_token.type == 'L_PARENTHESIS':
                right = self.parse_function_call(right)

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
        self.expect('ACCESSOR_SYMBOL', f"Expected '.' after '{calculation_type}'")
        
        # Parse shape (e.g., Rectangle)
        if self.current_token.type not in ('IDENTIFIER', 'RESERVED_WORD'):
            raise UnexpectedTokenError(
                self.current_token.pos_start,
                self.current_token.pos_end,
                f"Expected shape after '{calculation_type}.'"
            )
        shape = self.current_token.value
        self.advance()

        # Parse parameters (e.g., L, W)
        self.expect('L_PARENTHESIS', "Expected '('")
        params = []
        while self.current_token.type != 'R_PARENTHESIS':
            params.append(self.expr())
            if self.current_token.type == 'SEPARATING_SYMBOL':
                self.advance()
        self.expect('R_PARENTHESIS', "Expected ')'")
        
        return ASTNode(type_="GeometricCalculation", value=f"{calculation_type}.{shape}", children=params)
    
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

        #error handler
        if token.type in ('INTEGER', 'FLOAT', 'STRING_LITERAL', 'CHAR_LITERAL'):
            # Capture position before advancing
            pos_start = token.pos_start
            pos_end = token.pos_end
            self.advance()
            return ASTNode(
                type_="Literal",
                value=token.value,
                pos_start=pos_start,
                pos_end=pos_end
            )

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

    def next_token(self):
        """Advances to the next token."""
        self.current_token = self.tokenizer.get_next_token()


#from prettytable import PrettyTable

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