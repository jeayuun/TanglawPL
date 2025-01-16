import tokenizer
import os
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
            print(f"Error: The file '{input_filepath}' does not exist in the Downloads folder.")
            return

        with open(input_filepath, 'r') as file:
            text = file.read()

        tokens, errors = tokenizer.run(filename, text)

        # Output file location
        output_filename = downloads_folder / filename.replace('.lit', '_output.txt')

        # Write results to the output file
        with open(output_filename, 'w') as output_file:
            # Input Section
            output_file.write("--------------- Input ---------------\n")
            output_file.write(text + "\n\n")

            # Tokens Table
            output_file.write("----------- Tokens Table ------------\n")
            token_table = PrettyTable()
            token_table.field_names = ["Token Specification", "Tokens"]

            for token in tokens:
                token_table.add_row([token.type, token.value])

            output_file.write(token_table.get_string() + "\n\n")

            # Errors Table
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

        print(f"\nOutput saved to {output_filename}")

    except FileNotFoundError:
        print(f"Error: The file '{filename}' does not exist.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == '__main__':
    filename = input("Enter the .lit file name from the Downloads folder: ")
    process_file(filename)
