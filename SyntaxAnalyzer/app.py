from tokenizer import Lexer
from parser import Parser
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

        # Tokenization
        lexer = Lexer(filename, text)
        tokens, lexer_errors = lexer.make_tokens()

        if lexer_errors:
            print("Lexer encountered errors. Skipping parsing...")

            output_filename = downloads_folder / filename.replace('.lit', '_output.txt')

            with open(output_filename, 'w') as output_file:
                output_file.write("--------------- Input ---------------\n")
                output_file.write(text + "\n\n")

                output_file.write("\n----------- Errors Table ------------\n")
                
                error_table = PrettyTable()
                error_table.field_names = ["Error Type", "Details", "Location"]
                error_table.align["Error Type"] = "l"
                error_table.align["Details"] = "l"
                error_table.align["Location"] = "l"

                for error in lexer_errors:
                    error_table.add_row([
                        error.error_name,
                        error.details,
                        f"Line {error.pos_start.ln + 1}, Column {error.pos_start.col + 1}"
                    ])

                output_file.write(error_table.get_string() + "\n\n")

            print(f"\nOutput saved to {output_filename}")
            return




        # Parsing
        parser_instance = Parser(tokens)
        ast = parser_instance.parse()
        parser_errors = parser_instance.syntax_errors

        # Output File
        output_filename = downloads_folder / filename.replace('.lit', '_output.txt')

        with open(output_filename, 'w') as output_file:
            output_file.write("--------------- Input ---------------\n")
            output_file.write(text + "\n\n")

            # Abstract Syntax Tree
            output_file.write("----------- Abstract Syntax Tree ------------\n")
            if ast:
                output_file.write(str(ast) + "\n\n")
            else:
                output_file.write("Failed to generate AST due to syntax errors.\n\n")

            # Errors Table
            output_file.write("\n----------- Errors Table ------------\n")
            error_table = PrettyTable()
            error_table.field_names = ["Error Type", "Details", "Location"]
            error_table.align["Error Type"] = "l"
            error_table.align["Details"] = "l"
            error_table.align["Location"] = "l"

            if lexer_errors or parser_errors:
                output_file.write("\n----------- Errors Table ------------\n")

                error_table = PrettyTable()
                error_table.field_names = ["Error Type", "Details", "Location"]

                for error in lexer_errors:
                    error_table.add_row([
                        error.error_name,
                        error.details,
                        f"Line {error.pos_start.ln + 1}, Column {error.pos_start.col + 1}"
                    ])

                for error in parser_errors:
                    error_table.add_row([
                        error["Error Type"],
                        error["Details"],
                        error["Location"]
                    ])

                output_file.write(error_table.get_string() + "\n\n")


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
