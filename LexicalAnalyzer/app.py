import tokenizer
import os
from pathlib import Path

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

        result, error = tokenizer.run(filename, text)

        if error:
            print(f"Error: {error}")
        else:
            output_filename = downloads_folder / filename.replace('.lit', '_output.txt')

            with open(output_filename, 'w') as output_file:
                output_file.write("--------------- Input ---------------\n")
                output_file.write(text + "\n\n")

                output_file.write("----------- Tokens Table ------------\n")
                from prettytable import PrettyTable
                token_table = PrettyTable()
                token_table.field_names = ["Token Specification", "Tokens"]

                symbol_table = {}
                for token in result:
                    if token.type not in symbol_table:
                        symbol_table[token.type] = []
                    symbol_table[token.type].append(token.value)
                    token_table.add_row([token.type, token.value])

                output_file.write(token_table.get_string() + "\n\n")

                output_file.write("----------- Symbol Table ------------\n")
                symbol_table_table = PrettyTable()
                symbol_table_table.field_names = ["Token Specification", "Tokens"]

                for token_type, values in symbol_table.items():
                    symbol_table_table.add_row([token_type, ", ".join(map(str, values))])

                output_file.write(symbol_table_table.get_string())

            print(f"Output saved to {output_filename}")

    except FileNotFoundError:
        print(f"Error: The file '{filename}' does not exist.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == '__main__':
    filename = input("Enter the .lit file name from the Downloads folder: ")
    process_file(filename)
