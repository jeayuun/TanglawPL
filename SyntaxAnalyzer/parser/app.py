import parser  # Importing the syntax analyzer

while True:
    try:
        # Prompting user for input
        text = input("parser > ")
        if text.strip() == "":
            continue  # Skip empty inputs
        
        # Parsing the input using the syntax analyzer
        result, error = parser.run("<stdin>", text)

        # Handling output
        if error:
            print(error)  # Print detailed error message
        else:
            print(result)  # Print the syntax tree
    except KeyboardInterrupt:
        # Graceful exit on Ctrl+C
        print("\nExiting parser.")
        break
    except EOFError:
        # Graceful exit on Ctrl+D (Unix/Mac)
        print("\nExiting parser.")
        break
