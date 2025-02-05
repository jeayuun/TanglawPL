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

        # Parse tokens and generate AST
        ast = None
        if not errors:
            parser_instance = parser.Parser(tokens)  # Assuming your parser class is named `Parser`
            ast = parser_instance.parse()  # Generate AST

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

            output_file.write("----------- Errors Table ------------\n")
            if errors:
                error_table = PrettyTable()
                error_table.field_names = ["Error Type", "Details", "Location"]
                for error in errors:
                    error_table.add_row([
                        error.error_name,
                        error.details,
                        f"Line {error.pos_start.ln + 1}, Column {error.pos_start.col + 1}"
                    ])
                output_file.write(error_table.get_string())
            else:
                output_file.write("No errors found.\n")

            # Add AST Output with proper encoding
            output_file.write("----------- AST Output ------------\n")
            if ast:
                output_file.write(ast.__repr__() + "\n")  # This will print the AST
                output_file.write("Correct syntax, Output is Valid.\n")
            else:
                output_file.write("AST generation failed due to syntax errors.\n")

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
