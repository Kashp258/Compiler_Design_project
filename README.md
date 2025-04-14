#  SLR(1) Parser with Streamlit

This is a **Streamlit-based interactive web app** for building and visualizing an **SLR(1) parsing table** from a given context-free grammar. It allows users to input grammar rules, and then generates the **FIRST**, **FOLLOW**, **LR(0) items**, and finally the **SLR(1) parsing table**.

> Designed for compiler design students and enthusiasts to **understand parsing concepts** with ease through a visual and interactive UI.

---

##  Features

- Input grammar rules in a user-friendly sidebar
- Automatic augmentation of the grammar
- Computes:
  - FIRST sets
  - FOLLOW sets
  - LR(0) item sets
  - GOTO transitions
- Displays the **SLR(1) parsing table** in a clean tabular format
- Highlights reduction and shift actions
- Error checking and helpful messages for invalid grammar rules

---

## 🛠️ Technologies Used

- **Python**
- **Streamlit** – for interactive UI
- **Pandas** – for tabular data display
- **Tabulate** – for structured formatting (optional usage)

---

##  How to Use

### 1. Clone the repository:

```bash
git clone https://github.com/your-username/slr1-parser-streamlit.git
cd slr1-parser-streamlit
```

### 2. Install dependencies:

```bash
pip install streamlit pandas tabulate
```

### 3. Run the Streamlit app:

```bash
streamlit run app.py
```

> Replace `app.py` with the filename if it’s different.

---

## 📘 Example Grammar Format

In the sidebar, enter grammar rules like:

```
E -> E + T | T  
T -> T * F | F  
F -> ( E ) | id
```

Each rule should use `->` and separate alternatives with `|`. Do not forget to add whitespace between symbols.

---

##  Behind the Scenes

This parser:

1. **Augments the grammar** by adding a new start symbol.
2. **Generates LR(0) item sets** using the Closure and GOTO functions.
3. **Computes FIRST and FOLLOW sets** using recursive methods.
4. **Constructs the SLR(1) parsing table**, marking Shift, Reduce, GOTO, and Accept actions.

---

## 🧪 Example Output

Here’s a snippet of what you’ll see in the output parsing table:

| State | id | + | * | ( | ) | $ | \| | E | T | F |
|-------|----|---|---|---|---|---|---|---|---|---|
| 0     | S5 |   |   | S4 |   |   |   | 1 | 2 | 3 |
| ...   |    |   |   |    |   |   |   |   |   |   |

---

## 💡 Tips

- Non-terminals should be uppercase (e.g., `E`, `T`, `F`)
- Terminals are lowercase or symbols (`+`, `*`, `id`, `(`, `)`)
- Use `ε` for epsilon (empty string) if needed
