import tokenizer
import os

def process_file(filename):
    if not filename.endswith('.lit'):
        print(f"Error: '{filename}' is not a valid .lit file.")
        return
    
    try:
        with open(filename, 'r') as file:
            text = file.read()
        
        result, error = tokenizer.run(filename, text)

        if error:
            print(f"Error: {error}")  
        else:
            print("Tokens:")
            for token in result:
                print(token)

    except FileNotFoundError:
        print(f"Error: The file '{filename}' does not exist.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == '__main__':
    filename = input("Enter the .lit file name: ")

    process_file(filename)
