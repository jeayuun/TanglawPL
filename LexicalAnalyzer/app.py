import tokenizer
import os

# Function to process the file
def process_file(filename):
    # Step 1: Check if the file has the '.lit' extension
    if not filename.endswith('.lit'):
        print(f"Error: '{filename}' is not a valid .lit file.")
        return
    
    try:
        # Step 2: Open the file and read the content
        with open(filename, 'r') as file:
            text = file.read()
        
        # Step 3: Run the tokenizer on the file content
        result, error = tokenizer.run(filename, text)

        if error:
            print(error.as_string())  # Print error if there's any
        else:
            # Print the tokens or output to the symbol table file
            print(result)

    except FileNotFoundError:
        print(f"Error: The file '{filename}' does not exist.")
    except Exception as e:
        print(f"Error: {e}")

# Main logic
if __name__ == '__main__':
    # Step 4: Ask the user for the file name
    filename = input("Enter the .lit file name: ")

    # Process the file
    process_file(filename)
