# STEP 1: PARSE THE GRAMMAR FILE
def parse_grammar(filepath):
    productions = []      # List of all rules, e.g. [['E', ['T', "E'"]], ...]
    terminals = set()     
    non_terminals = []   
    start_symbol = None   
    
    with open(filepath, 'r') as file:
        for line in file:
            line = line.strip()
            if not line or '->' not in line:
                continue
                
            left_side, right_side = line.split('->')
            left_side = left_side.strip()

            # Record non-terminals in the order they appear
            if left_side not in non_terminals:
                non_terminals.append(left_side)
            
            # The very first LHS symbol is the start symbol
            if start_symbol is None:
                start_symbol = left_side
                
            # Split alternatives separated by '|' (e.g., "+ T E' | epsilon")
            for alt in right_side.split('|'):
                alt = alt.strip()
                if alt:
                    # Store as [LHS, [list of RHS tokens]]
                    productions.append([left_side, alt.split()])
                        
    # Find all terminal symbols (anything that is not a non-terminal and not epsilon)
    for left_side, right_side in productions:
        for symbol in right_side:
            if symbol != 'epsilon' and symbol not in non_terminals:
                terminals.add(symbol)

    # Print summary of parsed elements
    print("Productions :", productions)
    print("Terminals :", terminals)
    print("Non-terminals :", non_terminals)
    print("Start symbol :", start_symbol)
                        
    return productions, terminals, non_terminals, start_symbol

"""
STEP 2: COMPUTE FIRST SETS
Rules for FIRST:
1. If X is a terminal or epsilon -> FIRST(X) = {X}
2. If X is a non-terminal (X -> Y1 Y2 ...):
   - Add FIRST(Y1) (excluding epsilon) to FIRST(X)
   - If Y1 can derive epsilon, continue to Y2, etc.
    - If all derive epsilon, add epsilon to FIRST(X)
"""

def compute_first(productions, non_terminals, terminals):
    # Initialize an empty set for each non-terminal
    first = {}
    for non_terminal in non_terminals:
        first[non_terminal] = set()

    # Iterate bottom-up (from last production to first production for dependency resolution)
    for left_side, right_side in reversed(productions):
        for symbol in right_side:
            # Case A: If symbol is a terminal or epsilon -> add directly and stop
            if symbol in terminals or symbol == 'epsilon':
                first[left_side].add(symbol)
                break

            # Case B: If symbol is a Non-Terminal -> add its FIRST (except epsilon)
            elif symbol in non_terminals:
                first[left_side].update(first[symbol] - {'epsilon'})

                # If this non-terminal cannot derive epsilon, do not check further symbols
                if 'epsilon' not in first[symbol]:
                    break
        else:
            # If all symbols in right_side can derive epsilon, add epsilon to LHS
            first[left_side].add('epsilon')

    return first

"""
STEP 3: COMPUTE FOLLOW SETS
Rules for FOLLOW:
1. Place '$' (End of Input) into FOLLOW(start_symbol).
2. If there is a production A -> alpha B beta:
   - Everything in FIRST(beta) (except epsilon) goes into FOLLOW(B).
   - If beta can derive epsilon (or beta is empty), everything in FOLLOW(A) goes into FOLLOW(B).
"""
def compute_follow(productions, non_terminals, start_symbol, first, terminals):
    # Initialize an empty set for each non-terminal
    follow = {}
    for non_terminal in non_terminals:
        follow[non_terminal] = set()

    # Rule 1: Start symbol always gets '$'
    follow[start_symbol].add('$')

    # Search where each Non-Terminal appears on the Right-Hand Side
    for non_terminal in non_terminals:
        for lhs, rhs in productions:
            for i, symbol in enumerate(rhs):
                # Found the non-terminal on the RHS
                if symbol == non_terminal:
                    following_symbols = rhs[i + 1:]  # Symbols after this non-terminal

                    # Case A: There are symbols after this non-terminal (A -> ... B beta)
                    if following_symbols:
                        next_symbol = following_symbols[0]

                        # If next symbol is a terminal -> add directly to FOLLOW
                        if next_symbol in terminals:
                            follow[non_terminal].add(next_symbol)

                        # If next symbol is a non-terminal -> add FIRST(next_symbol) without epsilon
                        elif next_symbol in non_terminals:
                            follow[non_terminal].update(first[next_symbol] - {'epsilon'})
                            # If next symbol derives epsilon, also inherit FOLLOW(LHS)
                            if 'epsilon' in first[next_symbol]:
                                follow[non_terminal].update(follow[lhs])

                    # Case B: The non-terminal is at the very end (A -> ... B)
                    else:
                        follow[non_terminal].update(follow[lhs])

    return follow

"""
STEP 4: COMPUTE LL(1) PARSING TABLE (Storing Production Numbers)
Rules for LL(1) Table construction:
For each production index (1, 2, 3...):
1. If alpha is 'epsilon': Place production number under each terminal in FOLLOW(A).
2. If alpha begins with terminal 'a': Place production number in column 'a'.
3. If alpha begins with non-terminal 'B': Place production number in columns of FIRST(B).
4. Check for conflict: If any cell gets > 1 production number, grammar is NOT LL(1).
"""
def compute_ll1_table(productions, non_terminals, terminals, first, follow):
    # Table columns: terminals (alphabetically sorted) + '$' as the last column
    table_terminals = sorted(list(terminals - {'epsilon'})) + ['$']
    
    # 1. Initialize empty table with blank strings for all (Row, Col) cells
    table = {}
    for non_terminal in non_terminals:
        table[non_terminal] = {}
        for terminal in table_terminals:
            table[non_terminal][terminal] = ""

    is_ll1 = True  # Flag to track if the grammar is LL(1)

    # 2. Place each production NUMBER into the parsing table (1-based index)
    for prod_num, (left_side, right_side) in enumerate(productions, 1):
        prod_text = str(prod_num)

        # Rule 1: If production is epsilon (e.g. E' -> epsilon), place in FOLLOW(left_side)
        if right_side == ['epsilon']:
            for terminal in follow[left_side]:
                if table[left_side][terminal] != "" and table[left_side][terminal] != prod_text:
                    is_ll1 = False  # Conflict detected!
                table[left_side][terminal] = prod_text
        else:
            # Rule 2 & 3: Place under FIRST of the first RHS symbol
            first_symbol = right_side[0]
            
            # If first symbol is a terminal (e.g. + in "+ T E'")
            if first_symbol in terminals:
                if table[left_side][first_symbol] != "" and table[left_side][first_symbol] != prod_text:
                    is_ll1 = False  # Conflict detected!
                table[left_side][first_symbol] = prod_text
                
            # If first symbol is a non-terminal (e.g. T in "T E'")
            elif first_symbol in non_terminals:
                for terminal in first[first_symbol] - {'epsilon'}:
                    if table[left_side][terminal] != "" and table[left_side][terminal] != prod_text:
                        is_ll1 = False  # Conflict detected!
                    table[left_side][terminal] = prod_text

    return table, table_terminals, is_ll1


# STEP 5: DISPLAY LL(1) PARSING TABLE
# Compact formatted 2D table display showing production numbers

def print_ll1_table(table, non_terminals, table_terminals):
    col_width = 8
    header = f"{'Non-Terminal':<14} | " + " | ".join(f"{t:<{col_width}}" for t in table_terminals)
    separator = "-" * len(header)

    print("\n--- LL(1) Parsing Table (Production Numbers) ---")
    print(separator)
    print(header)
    print(separator)

    # Print each non-terminal row
    for non_terminal in non_terminals:
        row = f"{non_terminal:<14} | " + " | ".join(f"{table[non_terminal][t]:<{col_width}}" for t in table_terminals)
        print(row)

    print(separator)



# Main Execution
filepath = "grammer.txt"

# 1. Parse grammar file
productions, terminals, non_terminals, start_symbol = parse_grammar(filepath)

# Print numbered productions
print("\n--- Parsed Grammar Productions ---")
for i, (left_side, right_side) in enumerate(productions, 1):
    print(f"({i}) {left_side} -> {' '.join(right_side)}")
        
# 2. Calculate and display FIRST sets
print("\n--- FIRST Sets ---")
first = compute_first(productions, non_terminals, terminals)
for non_terminal in sorted(non_terminals):
    print(f"FIRST({non_terminal}) = {{ {', '.join(sorted(first[non_terminal]))} }}")
    
# 3. Calculate and display FOLLOW sets
print("\n--- FOLLOW Sets ---")
follow = compute_follow(productions, non_terminals, start_symbol, first, terminals)
for non_terminal in sorted(non_terminals):
    print(f"FOLLOW({non_terminal}) = {{ {', '.join(sorted(follow[non_terminal]))} }}")

# 4. Compute and display LL(1) Parsing Table (Numbered)
table, table_terminals, is_ll1 = compute_ll1_table(productions, non_terminals, terminals, first, follow)
print_ll1_table(table, non_terminals, table_terminals)

# 5. Final Result Check
print("\n" + "=" * 50)
if is_ll1:
    print("RESULT: The grammar is LL(1) (Valid - No Conflicts)")
else:
    print("RESULT: The grammar is NOT LL(1) (Contains Conflicts)")
print("=" * 50)
