def count_tokens(filepath):
    try:
        with open(filepath, 'r') as file:
            code = file.read()
    except FileNotFoundError:
        print(f"Error: File '{filepath}' not found.")
        return
        
    keywords = {'if', 'else', 'while', 'for', 'return', 'int', 'float', 'void', 'char'}
    operators = {'+', '-', '*', '/', '=', '%', '&', '|', '<', '>', '!'}
    punctuation = {';', ',', '{', '}', '(', ')', '[', ']'}
    
    token_counts = {
        'KEYWORD': 0,
        'IDENTIFIER': 0,
        'NUMBER': 0,
        'OPERATOR': 0,
        'PUNCTUATION': 0,
        'STRING': 0,
        'COMMENT': 0
    }
    
    i = 0
    length = len(code)
    
    while i < length:
        char = code[i]
        
        # Skip whitespaces
        if char.isspace():
            i += 1
            continue
            
        # Comments (Single line // and Multi-line /* */)
        if char == '/' and i + 1 < length:
            if code[i+1] == '/':
                token_counts['COMMENT'] += 1
                i += 2
                while i < length and code[i] != '\n':
                    i += 1
                continue
            elif code[i+1] == '*':
                token_counts['COMMENT'] += 1
                i += 2
                while i + 1 < length and not (code[i] == '*' and code[i+1] == '/'):
                    i += 1
                i += 2 # Skip '*/'
                continue
                
        # Strings
        if char == '"':
            token_counts['STRING'] += 1
            i += 1
            while i < length and code[i] != '"':
                i += 1
            i += 1 # Skip closing quote
            continue
            
        # Identifiers and Keywords
        if char.isalpha() or char == '_':
            word = ""
            while i < length and (code[i].isalnum() or code[i] == '_'):
                word += code[i]
                i += 1
            
            if word in keywords:
                token_counts['KEYWORD'] += 1
            else:
                token_counts['IDENTIFIER'] += 1
            continue
            
        # Numbers (integers and floats)
        if char.isdigit():
            while i < length and (code[i].isdigit() or code[i] == '.'):
                i += 1
            token_counts['NUMBER'] += 1
            continue
            
        # Operators (grouping multiple symbols like ==, ++, etc. as one operator token)
        if char in operators:
            while i < length and code[i] in operators:
                i += 1
            token_counts['OPERATOR'] += 1
            continue
            
        # Punctuation
        if char in punctuation:
            token_counts['PUNCTUATION'] += 1
            i += 1
            continue
            
        # Move forward if it's an unrecognized character
        i += 1
        
    total_tokens = sum(token_counts.values())
    
    print(f"--- Token Count for {filepath} ---")
    for name, count in token_counts.items():
        if count > 0:
            print(f"{name}: {count}")
    print(f"Total Tokens: {total_tokens}")

if __name__ == "__main__":
    filepath = "input_code.txt"
    count_tokens(filepath)
