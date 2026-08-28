import sys

def format_item(item):
    lhs, rhs, dot_pos = item
    rhs_str = list(rhs)
    if rhs_str and rhs_str[0] == 'epsilon':
        rhs_str = ['.']
    else:
        rhs_str.insert(dot_pos, '.')
    return f"{lhs} -> {' '.join(rhs_str)}"

def parse_grammar(filepath):
    grammar = {}
    productions = []
    terminals = set()
    non_terminals = set()
    start_symbol = None
    
    try:
        with open(filepath, 'r') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'): continue
                if '->' not in line: continue
                    
                left, right = line.split('->')
                left = left.strip()
                non_terminals.add(left)
                
                if start_symbol is None:
                    start_symbol = left
                    
                prods = right.split('|')
                for prod in prods:
                    symbols = prod.strip().split()
                    if left not in grammar:
                        grammar[left] = []
                    grammar[left].append(symbols)
                    productions.append((left, symbols))
                            
    except FileNotFoundError:
        print(f"Error: File '{filepath}' not found.")
        sys.exit(1)
        
    for prods in grammar.values():
        for prod in prods:
            for sym in prod:
                if sym != 'epsilon' and sym not in non_terminals:
                    terminals.add(sym)
                    
    # Augment Grammar
    aug_start = start_symbol + "'"
    if aug_start not in grammar:
        grammar[aug_start] = []
    grammar[aug_start].append([start_symbol])
    productions.insert(0, (aug_start, [start_symbol]))
    non_terminals.add(aug_start)
    
    return grammar, productions, terminals, non_terminals, aug_start

def compute_first(grammar, non_terminals, terminals):
    first = {nt: set() for nt in non_terminals}
    def get_first(symbol):
        if symbol in terminals or symbol == 'epsilon': return {symbol}
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
                if epsilon_in_all and 'epsilon' not in first[nt]:
                    first[nt].add('epsilon')
                    changed = True
    return first

def compute_follow(grammar, non_terminals, start_symbol, first, terminals):
    follow = {nt: set() for nt in non_terminals}
    follow[start_symbol].add('$')
    def get_first(symbol):
        if symbol in terminals or symbol == 'epsilon': return {symbol}
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
                        if epsilon_in_all and not follow[nt].issubset(follow[sym]):
                            follow[sym].update(follow[nt])
                            changed = True
    return follow

def closure(items, grammar):
    closure_set = set(items)
    changed = True
    while changed:
        changed = False
        for item in list(closure_set):
            lhs, rhs, dot_pos = item
            if dot_pos < len(rhs) and rhs[dot_pos] != 'epsilon':
                next_sym = rhs[dot_pos]
                if next_sym in grammar:
                    for prod in grammar[next_sym]:
                        new_item = (next_sym, tuple(prod), 0)
                        if new_item not in closure_set:
                            closure_set.add(new_item)
                            changed = True
    return closure_set

def goto(items, symbol, grammar):
    goto_set = set()
    for item in items:
        lhs, rhs, dot_pos = item
        if dot_pos < len(rhs) and rhs[dot_pos] == symbol:
            goto_set.add((lhs, rhs, dot_pos + 1))
    return closure(goto_set, grammar)

def build_lr0_automaton(grammar, start_symbol):
    start_item = (start_symbol, tuple(grammar[start_symbol][0]), 0)
    start_state = frozenset(closure({start_item}, grammar))
    
    states = [start_state]
    transitions = {} # (state_idx, symbol) -> state_idx
    
    unprocessed = [0]
    
    while unprocessed:
        state_idx = unprocessed.pop(0)
        state = states[state_idx]
        
        symbols = set()
        for item in state:
            lhs, rhs, dot_pos = item
            if dot_pos < len(rhs) and rhs[dot_pos] != 'epsilon':
                symbols.add(rhs[dot_pos])
                
        for sym in symbols:
            next_state = frozenset(goto(state, sym, grammar))
            if not next_state: continue
                
            if next_state not in states:
                states.append(next_state)
                unprocessed.append(len(states) - 1)
                
            next_state_idx = states.index(next_state)
            transitions[(state_idx, sym)] = next_state_idx
            
    return states, transitions

def build_slr_table(states, transitions, grammar, productions, terminals, non_terminals, follow, aug_start):
    action = {}
    goto_table = {}
    
    terminals_and_eof = list(terminals) + ['$']
    
    for i, state in enumerate(states):
        action[i] = {}
        goto_table[i] = {}
        for item in state:
            lhs, rhs, dot_pos = item
            if dot_pos == len(rhs) or rhs[0] == 'epsilon':
                if lhs == aug_start:
                    action[i]['$'] = 'Accept'
                else:
                    prod_idx = productions.index((lhs, list(rhs)))
                    for term in follow[lhs]:
                        if term in action[i]:
                            print(f"Warning: Conflict in state {i} on {term}")
                        action[i][term] = f"r{prod_idx}"
            else:
                next_sym = rhs[dot_pos]
                if next_sym in terminals:
                    if (i, next_sym) in transitions:
                        next_state = transitions[(i, next_sym)]
                        if next_sym in action[i]:
                            print(f"Warning: Conflict in state {i} on {next_sym}")
                        action[i][next_sym] = f"s{next_state}"
                        
        for nt in non_terminals:
            if nt != aug_start and (i, nt) in transitions:
                goto_table[i][nt] = transitions[(i, nt)]
                
    return action, goto_table, terminals_and_eof

def print_table(action, goto_table, states, terminals_and_eof, non_terminals, aug_start):
    print("\n--- SLR Parsing Table ---")
    
    nts = sorted([nt for nt in non_terminals if nt != aug_start])
    col_width = 10
    
    header = f"{'State':<{col_width}}"
    for t in terminals_and_eof:
        header += f"{t:<{col_width}}"
    header += "|"
    for nt in nts:
        header += f"{nt:<{col_width}}"
        
    print(header)
    print("-" * len(header))
    
    for i in range(len(states)):
        row = f"{i:<{col_width}}"
        for t in terminals_and_eof:
            row += f"{action[i].get(t, ''):<{col_width}}"
        row += "|"
        for nt in nts:
            row += f"{str(goto_table[i].get(nt, '')):<{col_width}}"
        print(row)

if __name__ == "__main__":
    filepath = "grammar.txt"
    grammar, productions, terminals, non_terminals, aug_start = parse_grammar(filepath)
    
    print("--- Augmented Grammar ---")
    for i, (lhs, rhs) in enumerate(productions):
        print(f"({i}) {lhs} -> {' '.join(rhs)}")
        
    first = compute_first(grammar, non_terminals, terminals)
    follow = compute_follow(grammar, non_terminals, aug_start, first, terminals)
    
    states, transitions = build_lr0_automaton(grammar, aug_start)
    
    print(f"\nConstructed LR(0) Automaton with {len(states)} states.")
    
    action, goto_table, terms = build_slr_table(
        states, transitions, grammar, productions, terminals, non_terminals, follow, aug_start
    )
    
    print_table(action, goto_table, states, terms, non_terminals, aug_start)
