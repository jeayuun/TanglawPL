import tokenizer

while True:
    text = input('tokenizer > ')
    result, error = tokenizer.run('<stdin>', text)

    if error: print(error.as_string())
    else: print(result)