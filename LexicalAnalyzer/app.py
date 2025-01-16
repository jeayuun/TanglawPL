import tokenizer
import os
from pathlib import Path

def process_file(filename):
    """
    Processes a .lit file, generates tokens, and creates an output file.

    Args:
        filename (str): The name of the .lit file to process.
    """

    # Check if the file extension is .lit
    if not filename.endswith('.lit'):
        print(f"Error: '{filename}' is not a valid .lit file.")
        return

    try:
        # Get the Downloads folder path using pathlib
        downloads_folder = Path.home() / "Downloads"
        input_filepath = downloads_folder / filename

        if not input_filepath.exists():
            print(f"Error: The file '{input_filepath}' does not exist in the Downloads folder.")
            return

        with open(input_filepath, 'r') as file:
            text = file.read()

        # Tokenize the text using the tokenizer
        result, error = tokenizer.run(filename, text)

        # If there are errors in tokenization, print the error
        if error:
            print(f"Error: {error}")
        else:
            # Set the output file path by replacing the .lit extension with _output.txt
            output_filename = downloads_folder / filename.replace('.lit', '_output.txt')

            # Open the output file for writing  
            with open(output_filename, 'w') as output_file:
                output_file.write("--------------- Input ---------------\n")
                output_file.write(text + "\n\n") # Write the input text

                output_file.write("----------- Tokens Table ------------\n")
                from prettytable import PrettyTable # Import PrettyTable for formatting tables
                token_table = PrettyTable()
                token_table.field_names = ["Token Specification", "Tokens"]

                symbol_table = {} # Dictionary to store tokens by type
                for token in result:
                    if token.type not in symbol_table:
                        symbol_table[token.type] = [] # Add token type if not already in the symbol table
                    symbol_table[token.type].append(token.value) # Append token values for each type
                    token_table.add_row([token.type, token.value]) # Add token details to the table

                output_file.write(token_table.get_string() + "\n\n") # Write the token table to the output file

                output_file.write("----------- Symbol Table ------------\n")
                symbol_table_table = PrettyTable() # Create a table for the symbol table
                symbol_table_table.field_names = ["Token Specification", "Tokens"]

                for token_type, values in symbol_table.items():
                    symbol_table_table.add_row([token_type, ", ".join(map(str, values))]) # Add rows for each token type

                output_file.write(symbol_table_table.get_string()) # Write the symbol table to the output file

            print(f"Output saved to {output_filename}")

    except FileNotFoundError: # Handles the error if the file doesn't exist
        print(f"Error: The file '{filename}' does not exist.")
    except Exception as e:  #Handles other exceptions
        print(f"Error: {e}") 

 # main of the scriptttt
if __name__ == '__main__': 
    filename = input("Enter the .lit file name from the Downloads folder: ") # Prompt the user for the file name
    process_file(filename) # Call the process_file function to process the .lit file
