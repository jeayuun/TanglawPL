from flask import Flask, request, render_template, jsonify
import sys
from pathlib import Path

# Add LexicalAnalyzer directory to sys.path
sys.path.append(r"C:\Users\itsrr\Downloads\PPL\TanglawPL\LexicalAnalyzer")
import tokenizer  # Import your tokenizer

app = Flask(__name__)

# Serve the main HTML page
@app.route('/')
def index():
    return render_template('index.html')  # Ensure index.html is in the 'templates' folder

# Endpoint to process input using tokenizer
@app.route('/tokenize', methods=['POST'])
def tokenize():
    try:
        # Get JSON data from the POST request
        data = request.json

        # Check if 'code' is present in the data
        if 'code' not in data:
            return jsonify({'error': 'No code provided'}), 400
        
        code = data['code']  # Extract the 'code' from the request

        # Use the tokenizer to process the code
        tokens, errors = tokenizer.run("user_input.lit", code)

        # Prepare tokens and errors for response
        token_list = [{'type': token.type, 'value': token.value} for token in tokens]
        error_list = [{'error_name': e.error_name, 'details': e.details} for e in errors]

        # Return JSON response with tokens and errors
        return jsonify({'tokens': token_list, 'errors': error_list})

    except Exception as e:
        # Return error message if something went wrong
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
  