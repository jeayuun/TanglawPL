import sys
from tokenizer import Lexer
from syntax_parser import Parser

#######################################
#                RUN                  #
#######################################

def run(fn, text):
    # Tokenize input
    lexer = Lexer(fn, text)
    tokens, error = lexer.make_tokens()
    if error:
        return None, error.as_string()

    # Parse input
    parser = Parser(tokens)
    ast = parser.parse()

    if ast.error:
        return None, ast.error

    return ast.node, None

if __name__ == "__main__":
    print("Welcome to the Interactive Parser!")
    print("Type your code below and press Enter to evaluate. Type 'exit' to quit.")

    while True:
        try:
            text = input(">>> ")  # Prompt for user input
            if text.strip().lower() == "exit":
                print("Goodbye!")
                break

            result, error = run("<stdin>", text)  # Use <stdin> as filename for context

            if error:
                print(error)
            else:
                print("AST:", result)

        except KeyboardInterrupt:
            print("\nGoodbye!")
            break