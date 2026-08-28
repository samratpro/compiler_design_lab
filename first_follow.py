import sys

def parse_grammar(filepath):
    grammar = {}
    terminals = set()
    non_terminals = set()
    start_symbol = None
    
    try:
        with open(filepath, 'r') as f:
            for line in f:
                # Remove comments or empty lines
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                
                # Format: A -> B c | d
                if '->' not in line:
                    continue
                    
                left, right = line.split('->')
                left = left.strip()
                non_terminals.add(left)
                
                if start_symbol is None:
                    start_symbol = left
                    
                productions = right.split('|')
                for prod in productions:
                    symbols = prod.strip().split()
                    if left not in grammar:
                        grammar[left] = []
                    grammar[left].append(symbols)
                            
    except FileNotFoundError:
        print(f"Error: File '{filepath}' not found.")
        sys.exit(1)
        
    for prods in grammar.values():
        for prod in prods:
            for sym in prod:
                if sym != 'epsilon' and sym not in non_terminals:
                    terminals.add(sym)
                        
    return grammar, terminals, non_terminals, start_symbol

def compute_first(grammar, non_terminals, terminals):
    first = {nt: set() for nt in non_terminals}
    
    def get_first(symbol):
        if symbol in terminals or symbol == 'epsilon':
            return {symbol}
        return first.get(symbol, set())

    changed = True
    while changed:
        changed = False
        for nt in non_terminals:
            for prod in grammar[nt]:
                epsilon_in_all = True
                for sym in prod:
                    sym_first = get_first(sym)
                    new_elements = sym_first - {'epsilon'}
                    
                    if not new_elements.issubset(first[nt]):
                        first[nt].update(new_elements)
                        changed = True
                        
                    if 'epsilon' not in sym_first:
                        epsilon_in_all = False
                        break
                        
                if epsilon_in_all:
                    if 'epsilon' not in first[nt]:
                        first[nt].add('epsilon')
                        changed = True
                        
    return first

def compute_follow(grammar, non_terminals, start_symbol, first, terminals):
    follow = {nt: set() for nt in non_terminals}
    follow[start_symbol].add('$')
    
    def get_first(symbol):
        if symbol in terminals or symbol == 'epsilon':
            return {symbol}
        return first.get(symbol, set())

    changed = True
    while changed:
        changed = False
        for nt in non_terminals:
            for prod in grammar[nt]:
                for i in range(len(prod)):
                    sym = prod[i]
                    if sym in non_terminals:
                        next_first = set()
                        epsilon_in_all = True
                        
                        for j in range(i + 1, len(prod)):
                            next_sym = prod[j]
                            sym_first = get_first(next_sym)
                            next_first.update(sym_first - {'epsilon'})
                            if 'epsilon' not in sym_first:
                                epsilon_in_all = False
                                break
                        
                        # Add FIRST of string following sym to FOLLOW(sym)
                        if not next_first.issubset(follow[sym]):
                            follow[sym].update(next_first)
                            changed = True
                            
                        # If epsilon is in FIRST of all following symbols, or sym is at the end
                        if epsilon_in_all:
                            if not follow[nt].issubset(follow[sym]):
                                follow[sym].update(follow[nt])
                                changed = True
                                
    return follow

if __name__ == "__main__":
    filepath = "grammar.txt"
    grammar, terminals, non_terminals, start_symbol = parse_grammar(filepath)
    
    print("--- Parsed Grammar ---")
    for nt, prods in grammar.items():
        for prod in prods:
            print(f"{nt} -> {' '.join(prod)}")
            
    print("\n--- FIRST Sets ---")
    first = compute_first(grammar, non_terminals, terminals)
    for nt in sorted(non_terminals):
        print(f"FIRST({nt}) = {{ {', '.join(sorted(first[nt]))} }}")
        
    print("\n--- FOLLOW Sets ---")
    follow = compute_follow(grammar, non_terminals, start_symbol, first, terminals)
    for nt in sorted(non_terminals):
        print(f"FOLLOW({nt}) = {{ {', '.join(sorted(follow[nt]))} }}")
