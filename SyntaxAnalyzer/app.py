import tokenizer
import parser  # Import your parser module
from pathlib import Path
from prettytable import PrettyTable

def process_file(filename):
    if not filename.endswith('.lit'):
        print(f"Error: '{filename}' is not a valid .lit file.")
        return

    try:
        downloads_folder = Path.home() / "Downloads"
        input_filepath = downloads_folder / filename

        if not input_filepath.exists():
            print(f"\nError: The file '{input_filepath}' does not exist in the Downloads folder.")
            return

        with open(input_filepath, 'r') as file:
            text = file.read()

        tokens, errors = tokenizer.run(filename, text)

                # Parse tokens and generate AST or capture errors
        ast_or_error = None
        if not errors:
            parser_instance = parser.Parser(tokens)
            ast_or_error = parser_instance.parse()  # This now returns either AST or an error message

        output_filename = downloads_folder / filename.replace('.lit', '_output.txt')

        with open(output_filename, 'w', encoding='utf-8') as output_file:
            output_file.write("--------------- Input ---------------\n")
            output_file.write(text + "\n\n")

            output_file.write("----------- Tokens Table ------------\n")
            token_table = PrettyTable()
            token_table.field_names = ["Lexeme", "Token Specification"]

            for token in tokens:
                if isinstance(token, list): 
                    for sub_token in token:
                        token_table.add_row([sub_token.value, sub_token.type])
                else:
                    token_table.add_row([token.value, token.type])

            output_file.write(token_table.get_string() + "\n\n")

            output_file.write("----------- Errors Table (Tokenizer) ------------\n")
            if errors:
                error_table = PrettyTable()
                error_table.field_names = ["Error Type", "Details", "Location"]
                for error in errors:
                    error_table.add_row([
                        error.error_name,
                        error.details,
                        f"Line {error.pos_start.ln + 1}, Column {error.pos_start.col + 1}"
                    ])
                output_file.write(error_table.get_string() + "\n\n")
            else:
                output_file.write("No lexical errors found.\n\n")

            output_file.write("----------- Syntax Error ------------\n")
            if isinstance(ast_or_error, str):  # If a syntax error message was returned
                output_file.write(ast_or_error + "\n")
            else:
                output_file.write("No syntax errors found.\n\n")

            # Add AST Output if valid
            output_file.write("----------- AST Output ------------\n")
            if isinstance(ast_or_error, str):  # If there was an error, no AST is written
                output_file.write("AST generation failed due to syntax errors.\n")
            else:
                output_file.write(ast_or_error.__repr__() + "\n")
                output_file.write("Correct syntax, Output is Valid.\n")

        print(f"\nOutput saved to {output_filename}")


    except UnicodeDecodeError as e:
        print(f"Encoding error: {e}")
        print("Try using a different encoding such as 'latin-1' or ensure the file is UTF-8 encoded.")
    except FileNotFoundError:
        print(f"Error: The file '{filename}' does not exist.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == '__main__':
    filename = input("Enter the .lit file name from the Downloads folder: ")
    process_file(filename)
