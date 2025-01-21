#######################################
# SYNTAX ANALYZER FOR TOKENIZER
#######################################

# IMPORTS
from tokenizer import Token, Lexer, IllegalCharError, InvalidNumberError, UnclosedStringError
from SyntaxAnalyzer.string_with_arrows import *

#######################################
# ERROR CLASS
#######################################

class InvalidSyntaxError(Exception):
    def __init__(self, pos_start, pos_end, details):
        self.pos_start = pos_start
        self.pos_end = pos_end
        self.details = details

    def as_string(self):
        result  = f"Invalid Syntax: {self.details}\n"
        result += f"File {self.pos_start.fn}, line {self.pos_start.ln + 1}, column {self.pos_start.col + 1}-{self.pos_end.col}"
        result += '\n' + string_with_arrows(self.pos_start.ftxt, self.pos_start, self.pos_end)
        return result

#######################################
# NODE CLASSES
#######################################

class Node:
    pass

class NumberNode(Node):
    def __init__(self, token):
        self.token = token

    def __repr__(self):
        return f"{self.token}"

class BinaryOpNode(Node):
    def __init__(self, left, operator_token, right):
        self.left = left
        self.operator_token = operator_token
        self.right = right

    def __repr__(self):
        return f"({self.left}, {self.operator_token}, {self.right})"

class UnaryOpNode(Node):
    def __init__(self, operator_token, node):
        self.operator_token = operator_token
        self.node = node

    def __repr__(self):
        return f"({self.operator_token}, {self.node})"

#######################################
# PARSE RESULT
#######################################

class ParseResult:
    def __init__(self):
        self.error = None
        self.node = None

    def register(self, result):
        if isinstance(result, ParseResult):
            if result.error:
                self.error = result.error
            return result.node
        return result

    def success(self, node):
        self.node = node
        return self

    def failure(self, error):
        self.error = error
        return self

#######################################
# PARSER CLASS
#######################################

class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.current_token_index = -1
        self.current_token = None
        self.advance()

    def advance(self):
        self.current_token_index += 1
        if self.current_token_index < len(self.tokens):
            self.current_token = self.tokens[self.current_token_index]
        return self.current_token

    def parse(self):
        result = self.expr()
        if not result.error and self.current_token.type != 'EOF':
            return result.failure(InvalidSyntaxError(
                self.current_token.pos_start,
                self.current_token.pos_end,
                "Expected an operator or end of input"
            ))
        return result

    ###################################
    # GRAMMAR RULES
    ###################################

    def factor(self):
        result = ParseResult()
        token = self.current_token

        if token.type in ('PLUS', 'MINUS'):
            result.register(self.advance())
            factor = result.register(self.factor())
            if result.error:
                return result
            return result.success(UnaryOpNode(token, factor))

        elif token.type in ('INTEGER', 'REAL_NUMBER'):
            result.register(self.advance())
            return result.success(NumberNode(token))

        elif token.type == 'LPAREN':
            result.register(self.advance())
            expr = result.register(self.expr())
            if result.error:
                return result
            if self.current_token.type == 'RPAREN':
                result.register(self.advance())
                return result.success(expr)
            else:
                return result.failure(InvalidSyntaxError(
                    self.current_token.pos_start,
                    self.current_token.pos_end,
                    "Expected closing parenthesis"
                ))

        return result.failure(InvalidSyntaxError(
            token.pos_start, token.pos_end,
            "Expected a number, an operator, or a parenthesis"
        ))

    def term(self):
        return self.bin_op(self.factor, ('MUL', 'DIV'))

    def expr(self):
        return self.bin_op(self.term, ('PLUS', 'MINUS'))

    ###################################

    def bin_op(self, func, ops):
        result = ParseResult()
        left = result.register(func())
        if result.error:
            return result

        while self.current_token.type in ops:
            operator_token = self.current_token
            result.register(self.advance())
            right = result.register(func())
            if result.error:
                return result
            left = BinaryOpNode(left, operator_token, right)

        return result.success(left)

#######################################
# RUN FUNCTION
#######################################

def run(fn, text):
    lexer = Lexer(fn, text)
    tokens, error = lexer.make_tokens()
    if error:
        return None, error.as_string()

    parser = Parser(tokens)
    syntax_tree = parser.parse()

    if syntax_tree.error:
        return None, syntax_tree.error.as_string()

    return syntax_tree.node, None
