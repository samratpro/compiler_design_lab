import sys

def parse_grammar(filepath):
    grammar = {}
    terminals = set()
    non_terminals = set()
    start_symbol = None
    
    try:
        with open(filepath, 'r') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
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
                        
                        if not next_first.issubset(follow[sym]):
                            follow[sym].update(next_first)
                            changed = True
                            
                        if epsilon_in_all:
                            if not follow[nt].issubset(follow[sym]):
                                follow[sym].update(follow[nt])
                                changed = True
                                
    return follow

def build_ll1_table(grammar, non_terminals, terminals, first, follow):
    table = {}
    
    def get_first(symbol):
        if symbol in terminals or symbol == 'epsilon':
            return {symbol}
        return first.get(symbol, set())

    for nt in non_terminals:
        for prod in grammar[nt]:
            prod_first = set()
            epsilon_in_all = True
            
            for sym in prod:
                sym_first = get_first(sym)
                prod_first.update(sym_first - {'epsilon'})
                if 'epsilon' not in sym_first:
                    epsilon_in_all = False
                    break
                    
            if epsilon_in_all:
                prod_first.add('epsilon')
                
            if nt not in table:
                table[nt] = {}
                
            for terminal in prod_first - {'epsilon'}:
                if terminal in table[nt]:
                    print(f"Warning: LL(1) Conflict at M[{nt}, {terminal}]")
                table[nt][terminal] = prod
                
            if 'epsilon' in prod_first:
                for terminal in follow[nt]:
                    if terminal in table[nt]:
                        print(f"Warning: LL(1) Conflict at M[{nt}, {terminal}]")
                    table[nt][terminal] = prod
                    
    return table

def print_table(table, non_terminals, terminals):
    terminals_list = sorted(list(terminals)) + ['$']
    print("\n--- LL(1) Parsing Table ---")
    
    # Header
    col_width = 15
    header = f"{'':<{col_width}}" + "".join([f"{t:<{col_width}}" for t in terminals_list])
    print(header)
    print("-" * len(header))
    
    for nt in sorted(non_terminals):
        row = f"{nt:<{col_width}}"
        for t in terminals_list:
            if t in table[nt]:
                prod_str = " ".join(table[nt][t])
                row += f"{prod_str:<{col_width}}"
            else:
                row += f"{'':<{col_width}}"
        print(row)

if __name__ == "__main__":
    filepath = "grammar.txt"
    grammar, terminals, non_terminals, start_symbol = parse_grammar(filepath)
    
    first = compute_first(grammar, non_terminals, terminals)
    follow = compute_follow(grammar, non_terminals, start_symbol, first, terminals)
    table = build_ll1_table(grammar, non_terminals, terminals, first, follow)
    
    print_table(table, non_terminals, terminals)
