import streamlit as st
from tabulate import tabulate

# Streamlit App Title
st.title("SLR(1) Parser Table Generator")

# Sidebar for Grammar Input
st.sidebar.header("Enter Grammar Rules")
grammar_input = st.sidebar.text_area("Enter grammar rules (use '->' for production, '|' for multiple options)", 
                                     "E -> E + T | T\nT -> T * F | F\nF -> ( E ) | id")
st.sidebar.write("Example:\nS -> A B\nA -> a | ε\nB -> b")

# Function to Parse Grammar
def get_grammar(grammar_text):
    grammar = {}
    lines = grammar_text.strip().split("\n")

    for line in lines:
        if '->' not in line:
            st.sidebar.error(f"Invalid rule format: {line}. Use '->' to separate LHS and RHS.")
            return None

        lhs, rhs = line.split('->')
        lhs = lhs.strip()
        rhs_productions = [prod.strip().split() for prod in rhs.split('|')]

        if lhs in grammar:
            grammar[lhs].extend(rhs_productions)
        else:
            grammar[lhs] = rhs_productions

    return grammar

# Get grammar from input
grammar = get_grammar(grammar_input)
if not grammar:
    st.error("Please enter a valid grammar.")
    st.stop()

# Function to Augment Grammar
def augment_grammar(grammar):
    start_symbol = next(iter(grammar), None)
    if not start_symbol:
        st.error("Grammar is empty. Cannot augment.")
        st.stop()

    augmented_grammar = {"S'": [[start_symbol]]}  # New start symbol
    augmented_grammar.update(grammar)
    return augmented_grammar

augmented_grammar = augment_grammar(grammar)

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

states, transitions = generate_lr0_items(augmented_grammar)

# Compute FIRST Sets
first = {}
def compute_first(symbol):
    if symbol in first:
        return first[symbol]

    first[symbol] = set()
    for production in grammar.get(symbol, []):
        if production == [""]:
            first[symbol].add("ε")
        else:
            for sub_symbol in production:
                if sub_symbol not in grammar:
                    first[symbol].add(sub_symbol)
                    break
                else:
                    sub_first = compute_first(sub_symbol)
                    first[symbol].update(sub_first - {"ε"})
                    if "ε" not in sub_first:
                        break
            else:
                first[symbol].add("ε")

    return first[symbol]

for nt in grammar:
    compute_first(nt)

# Compute FOLLOW Sets
follow = {}
def compute_follow(symbol):
    if symbol in follow:
        return follow[symbol]

    follow[symbol] = set()
    if symbol == next(iter(grammar)):  # Start symbol
        follow[symbol].add("$")

    for lhs, rhs_list in grammar.items():
        for rhs in rhs_list:
            for i, sub_symbol in enumerate(rhs):
                if sub_symbol == symbol:
                    if i + 1 < len(rhs):
                        next_symbol = rhs[i + 1]
                        if next_symbol not in grammar:
                            follow[symbol].add(next_symbol)
                        else:
                            next_first = first[next_symbol] - {"ε"}
                            follow[symbol].update(next_first)
                            if "ε" in first[next_symbol]:
                                follow[symbol].update(compute_follow(lhs))
                    else:
                        if lhs != symbol:
                            follow[symbol].update(compute_follow(lhs))

    return follow[symbol]

for nt in grammar:
    compute_follow(nt)

# Generate SLR(1) Parsing Table
def generate_slr1_parsing_table(states, transitions, grammar, first, follow):
    parsing_table = {state: {} for state in range(len(states))}
    goto_table = {state: {} for state in range(len(states))}

    for (state, symbol), next_state in transitions.items():
        if symbol in grammar:
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

slr1_parsing_table, goto_table = generate_slr1_parsing_table(states, transitions, grammar, first, follow)

# Display Parsing Table
def display_slr1_parsing_table(parsing_table, goto_table):
    terminals = sorted({symbol for row in parsing_table.values() for symbol in row})
    non_terminals = sorted({symbol for row in goto_table.values() for symbol in row})

    headers = ["State"] + terminals + ["|"] + non_terminals
    table = []

    for state in parsing_table.keys():
        row = [state] + [parsing_table[state].get(t, "") for t in terminals] + ["|"] + [goto_table[state].get(nt, "") for nt in non_terminals]
        table.append(row)

    st.subheader("SLR(1) Parsing Table")
    st.text(tabulate(table, headers, tablefmt="grid"))

# Call Display Function
display_slr1_parsing_table(slr1_parsing_table, goto_table)
