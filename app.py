import streamlit as st
from tabulate import tabulate
import pandas as pd

# Function to get grammar input from user
def get_grammar():
    st.sidebar.subheader("Enter Grammar Rules")
    grammar = {}
    
    num_rules = st.sidebar.number_input("Number of rules", min_value=1, value=3, step=1)
    
    for i in range(num_rules):
        rule = st.sidebar.text_input(f"Rule {i+1} (e.g., E -> E + T | T)", key=f"rule_{i}").strip()
        if rule and '->' in rule:
            lhs, rhs = rule.split('->')
            lhs = lhs.strip()
            rhs_productions = [prod.strip().split() for prod in rhs.split('|')]
            grammar[lhs] = grammar.get(lhs, []) + rhs_productions
        elif rule:
            st.sidebar.warning(f"Invalid format in rule {i+1}. Use '->' to separate LHS and RHS.")

    return grammar if grammar else None  # Return None if empty

# Augment Grammar
def augment_grammar(grammar):
    if not grammar:
        st.error("No valid grammar rules provided. Please enter at least one rule.")
        st.stop()

    start_symbol = next(iter(grammar))  # First non-terminal as the start symbol
    augmented_grammar = {"S'": [[start_symbol]]}  
    augmented_grammar.update(grammar)  
    return augmented_grammar

# Closure Function
def closure(items, grammar):
    closure_set = set(items)
    added = True
    while added:
        added = False
        new_items = set()
        for lhs, rhs, dot_pos in closure_set:
            if dot_pos < len(rhs):
                symbol = rhs[dot_pos]
                if symbol in grammar:  
                    for production in grammar[symbol]:
                        new_item = (symbol, tuple(production), 0)
                        if new_item not in closure_set:
                            new_items.add(new_item)
                            added = True
        closure_set.update(new_items)
    return closure_set

# GOTO Function
def goto(items, symbol, grammar):
    next_items = set()
    for lhs, rhs, dot_pos in items:
        if dot_pos < len(rhs) and rhs[dot_pos] == symbol:
            next_items.add((lhs, tuple(rhs), dot_pos + 1))
    return closure(next_items, grammar) if next_items else set()

# Generate LR(0) Items
def generate_lr0_items(augmented_grammar):
    start_symbol = next(iter(augmented_grammar))  
    initial_item = (start_symbol, tuple(augmented_grammar[start_symbol][0]), 0)
    initial_state = closure({initial_item}, augmented_grammar)

    states = [initial_state]
    state_indices = {frozenset(initial_state): 0}  
    transitions = {}
    queue = [initial_state]  

    while queue:
        state = queue.pop(0)
        state_index = state_indices[frozenset(state)]  
        symbols = {rhs[pos] for lhs, rhs, pos in state if pos < len(rhs)}

        for symbol in symbols:
            new_state = goto(state, symbol, augmented_grammar)

            if frozenset(new_state) not in state_indices:
                states.append(new_state)
                new_index = len(states) - 1
                state_indices[frozenset(new_state)] = new_index
                queue.append(new_state)
            else:
                new_index = state_indices[frozenset(new_state)]

            transitions[(state_index, symbol)] = new_index

    return states, transitions

# Compute FIRST sets
def compute_first(symbol, grammar, first):
    if symbol in first:
        return first[symbol]

    first[symbol] = set()

    for production in grammar.get(symbol, []):
        if production == [""]:
            first[symbol].add("ε")
        else:
            for sub_symbol in production:
                if not sub_symbol.isupper():  
                    first[symbol].add(sub_symbol)
                    break
                else:
                    sub_first = compute_first(sub_symbol, grammar, first)
                    first[symbol].update(sub_first - {"ε"})
                    if "ε" not in sub_first:
                        break
            else:
                first[symbol].add("ε")

    return first[symbol]

# Compute FOLLOW sets
def compute_follow(symbol, grammar, first, follow, start_symbol):
    if symbol in follow:
        return follow[symbol]

    follow[symbol] = set()

    if symbol == start_symbol:
        follow[symbol].add("$")  

    for lhs, rhs_list in grammar.items():
        for rhs in rhs_list:
            for i, sub_symbol in enumerate(rhs):
                if sub_symbol == symbol:
                    if i + 1 < len(rhs):  
                        next_symbol = rhs[i + 1]
                        if not next_symbol.isupper():
                            follow[symbol].add(next_symbol)
                        else:
                            next_first = first[next_symbol] - {"ε"}
                            follow[symbol].update(next_first)
                            if "ε" in first[next_symbol]:
                                follow[symbol].update(compute_follow(lhs, grammar, first, follow, start_symbol))
                    else:  
                        if lhs != symbol:
                            follow[symbol].update(compute_follow(lhs, grammar, first, follow, start_symbol))

    return follow[symbol]

# Generate SLR(1) Parsing Table
def generate_slr1_parsing_table(states, transitions, grammar, first, follow):
    parsing_table = {state: {} for state in range(len(states))}
    goto_table = {state: {} for state in range(len(states))}

    for (state, symbol), next_state in transitions.items():
        if symbol.isupper():
            goto_table[state][symbol] = next_state
        else:
            parsing_table[state][symbol] = f"S{next_state}"

    for state, items in enumerate(states):
        for lhs, rhs, dot_pos in items:
            if dot_pos == len(rhs):
                if lhs == "S'":
                    parsing_table[state]['$'] = 'ACC'
                else:
                    for terminal in follow[lhs]:
                        parsing_table[state][terminal] = f"R({lhs} → {' '.join(rhs)})"

    return parsing_table, goto_table

# Streamlit UI
st.title("SLR(1) Parser with Streamlit")

grammar = get_grammar()
if not grammar:
    st.error("No valid grammar entered. Please enter at least one rule.")
    st.stop()

augmented_grammar = augment_grammar(grammar)

states, transitions = generate_lr0_items(augmented_grammar)

first = {}
follow = {}

start_symbol = next(iter(grammar))  
for nt in grammar:
    compute_first(nt, grammar, first)

for nt in grammar:
    compute_follow(nt, grammar, first, follow, start_symbol)

slr1_parsing_table, goto_table = generate_slr1_parsing_table(states, transitions, grammar, first, follow)

st.subheader("SLR(1) Parsing Table")
terminals = set()
for lhs, rhs_list in grammar.items():
    for rhs in rhs_list:
        for symbol in rhs:
            if not symbol.isupper() and symbol not in {"ε"}:  # Terminals are lowercase or symbols
                terminals.add(symbol)

# Ensure $ is included for parsing table (end-of-input marker)
terminals.add("$")

terminals = sorted(terminals)  # Sort for consistent order

non_terminals = sorted(grammar.keys())  # All LHS symbols are non-terminals

# Correct headers list
headers = ["State"] + terminals + ["|"] + non_terminals

table = [
    [state] + 
    [slr1_parsing_table[state].get(t, "") for t in terminals] + ["|"] + 
    [goto_table[state].get(nt, "") for nt in non_terminals]
    for state in slr1_parsing_table.keys()
]

# Ensure all rows have the same number of columns as headers
for row in table:
    if len(row) != len(headers):
        st.error(f"Row length mismatch detected! Expected {len(headers)}, got {len(row)}: {row}")

df = pd.DataFrame(table, columns=headers)
st.table(df)  # Display properly formatted table
