"""Creates a mini SQL database project with skeleton code and tests."""
import os

WORKDIR = os.path.join(os.path.dirname(__file__), "test_project")

def setup_test_project():
    os.makedirs(WORKDIR, exist_ok=True)

    # ---- Sample CSV data ----
    with open(os.path.join(WORKDIR, "employees.csv"), "w") as f:
        f.write("""id,name,dept,salary,manager_id
1,Alice,Engineering,120000,5
2,Bob,Engineering,95000,5
3,Carol,Sales,85000,6
4,Dave,Sales,90000,6
5,Eve,Engineering,150000,
6,Frank,Sales,140000,
7,Grace,Marketing,110000,
8,Heidi,Marketing,95000,7
9,Ivan,Engineering,98000,5
10,Judy,Marketing,88000,7
""")

    with open(os.path.join(WORKDIR, "departments.csv"), "w") as f:
        f.write("""dept_name,budget,location
Engineering,500000,Building A
Sales,300000,Building B
Marketing,250000,Building C
""")

    with open(os.path.join(WORKDIR, "projects.csv"), "w") as f:
        f.write("""project_id,project_name,dept,lead_id
P1,Search Engine,Engineering,1
P2,Ad Platform,Sales,3
P3,Brand Campaign,Marketing,7
P4,ML Pipeline,Engineering,5
P5,CRM System,Sales,4
""")

    # ---- database.py (provided — just CSV loading) ----
    with open(os.path.join(WORKDIR, "database.py"), "w") as f:
        f.write("""# CSV-backed database — loads CSV files as tables
import csv, os

DATA_DIR = os.path.dirname(__file__)

def load_table(name):
    path = os.path.join(DATA_DIR, f"{name}.csv")
    if not os.path.exists(path):
        raise FileNotFoundError(f"Table not found: {name}")
    with open(path, newline="") as f:
        reader = csv.DictReader(f)
        rows = []
        for row in reader:
            typed = {}
            for k, v in row.items():
                typed[k] = _cast(v)
            rows.append(typed)
        return rows

def _cast(value):
    if value == "" or value is None:
        return None
    for conv in (int, float):
        try: return conv(value)
        except ValueError: pass
    return value
""")

    # ---- db.py (ONE BIG SKELETON — tokenizer + parser + executor) ----
    with open(os.path.join(WORKDIR, "db.py"), "w") as f:
        f.write("""# Mini SQL Database — tokenizer, parser, and executor in one file
import re
from database import load_table

# =========================================================================
# TOKENIZER — converts SQL string into a list of (type, value) tokens
# =========================================================================

KEYWORDS = {
    "SELECT", "FROM", "WHERE", "AND", "OR", "NOT",
    "ORDER", "BY", "ASC", "DESC",
    "GROUP", "HAVING",
    "JOIN", "LEFT", "RIGHT", "INNER", "ON",
    "AS", "IN", "BETWEEN", "LIKE", "IS", "NULL",
    "COUNT", "SUM", "AVG", "MIN", "MAX",
    "LIMIT", "DISTINCT",
}

TOKEN_PATTERNS = [
    ("WHITESPACE", r"\\s+"),
    ("NUMBER",     r"\\d+(?:\\.\\d+)?"),
    ("STRING",     r"'[^']*'"),
    ("COMP_OP",    r"<=|>=|!=|<>|<|>|="),
    ("SYMBOL",     r"[(),.*]"),
    ("WORD",       r"[A-Za-z_][A-Za-z0-9_]*"),
]

def tokenize(sql):
    tokens = []
    pos = 0
    while pos < len(sql):
        match = None
        for token_type, pattern in TOKEN_PATTERNS:
            regex = re.compile(pattern)
            match = regex.match(sql, pos)
            if match:
                value = match.group(0)
                if token_type == "WHITESPACE":
                    pass
                elif token_type == "WORD" and value.upper() in KEYWORDS:
                    tokens.append(("KEYWORD", value.upper()))
                elif token_type == "WORD":
                    tokens.append(("IDENTIFIER", value))
                else:
                    tokens.append((token_type, value))
                pos = match.end()
                break
        if not match:
            raise SyntaxError(f"Unexpected character at position {pos}: {sql[pos:]}")
    return tokens

class TokenStream:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0

    def peek(self):
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        return None

    def advance(self):
        token = self.tokens[self.pos]
        self.pos += 1
        return token

    def expect(self, token_type, value=None):
        token = self.advance()
        if token[0] != token_type or (value and token[1] != value):
            raise SyntaxError(f"Expected ({token_type}, {value}), got {token}")
        return token

    def match(self, token_type, value=None):
        token = self.peek()
        if token and token[0] == token_type and (value is None or token[1] == value):
            return self.advance()
        return None

    def at_end(self):
        return self.pos >= len(self.tokens)

# =========================================================================
# PARSER — converts token stream into an AST dict
# =========================================================================

def parse(sql):
    tokens = tokenize(sql)
    stream = TokenStream(tokens)
    return parse_select(stream)

def parse_select(stream):
    # Parse: SELECT [DISTINCT] columns FROM table [JOIN...] [WHERE...] [GROUP BY...] [HAVING...] [ORDER BY...] [LIMIT n]
    # Returns dict with keys: type, distinct, columns, from, where, joins, group_by, having, order_by, limit
    pass  # TODO

def parse_select_columns(stream):
    # Parse comma-separated column list. Returns list of column dicts.
    pass  # TODO

def parse_select_column(stream):
    # Parse one select item. Returns one of:
    #   star: {"type": "star"}
    #   column: {"type": "column", "name": "col"}  (optionally with "alias")
    #   aggregate: {"type": "aggregate", "func": "COUNT", "arg": "*"}  (optionally with "alias")
    # Aggregates: COUNT, SUM, AVG, MIN, MAX followed by (arg).
    # Alias: followed by AS alias_name.
    # Column names may be dotted (table.column).
    pass  # TODO

def parse_join(stream):
    # Parse: [LEFT|RIGHT|INNER] JOIN table ON left_col = right_col
    # ON columns can be dotted: employees.id = projects.lead_id
    # Returns {"type": "INNER"/"LEFT", "table": str, "on": (left_col, right_col)}
    pass  # TODO

def parse_condition(stream):
    # Parse WHERE/HAVING condition with correct precedence: AND binds tighter than OR.
    # a OR b AND c  =>  OR(a, AND(b, c))
    # Returns nested condition nodes with type "logic" and op "AND"/"OR".
    pass  # TODO

def parse_comparison(stream):
    # Parse a single condition:
    #   NOT expr -> {"type": "not", "expr": ...}
    #   col IS [NOT] NULL -> {"type": "compare", "op": "IS NULL"/"IS NOT NULL", "left": ..., "right": None}
    #   col BETWEEN low AND high -> {"type": "between", "expr": ..., "low": ..., "high": ...}
    #   col IN (v1, v2) -> {"type": "in", "expr": ..., "values": [...]}
    #   col LIKE pattern -> {"type": "like", "expr": ..., "pattern": ...}
    #   col op value -> {"type": "compare", "op": "=", "left": ..., "right": ...}
    pass  # TODO

# ---- Parser helpers (provided) ----

def _parse_dotted_name(stream):
    name = stream.advance()[1]
    if stream.match("SYMBOL", "."):
        name += "." + stream.advance()[1]
    return name

def parse_value(stream):
    token = stream.peek()
    if token[0] == "NUMBER":
        stream.advance()
        return {"type": "literal", "value": float(token[1]) if "." in token[1] else int(token[1])}
    if token[0] == "STRING":
        stream.advance()
        return {"type": "literal", "value": token[1][1:-1]}
    if token[0] in ("IDENTIFIER", "KEYWORD"):
        name = _parse_dotted_name(stream)
        return {"type": "column_ref", "name": name}
    raise SyntaxError(f"Unexpected token: {token}")

def parse_column_list(stream):
    cols = [stream.advance()[1]]
    while stream.match("SYMBOL", ","):
        cols.append(stream.advance()[1])
    return cols

def parse_order_by(stream):
    orders = []
    col = stream.advance()[1]
    direction = "ASC"
    if stream.match("KEYWORD", "DESC"):
        direction = "DESC"
    elif stream.match("KEYWORD", "ASC"):
        direction = "ASC"
    orders.append((col, direction))
    while stream.match("SYMBOL", ","):
        col = stream.advance()[1]
        direction = "ASC"
        if stream.match("KEYWORD", "DESC"):
            direction = "DESC"
        elif stream.match("KEYWORD", "ASC"):
            direction = "ASC"
        orders.append((col, direction))
    return orders

# =========================================================================
# EXECUTOR — takes an AST and executes against CSV tables
# =========================================================================

def execute(ast):
    # Execute a parsed SQL AST. Returns list of row dicts.
    # Order: FROM -> JOIN -> WHERE -> GROUP BY/HAVING -> SELECT -> DISTINCT -> ORDER BY -> LIMIT
    pass  # TODO

def execute_join(left_rows, join):
    # INNER: only matching rows. LEFT: all left rows, NULLs for unmatched right.
    # Column names in join["on"] may be dotted (table.col) — use the part after the dot.
    pass  # TODO

def execute_select(rows, columns):
    # Project rows to selected columns.
    # star -> return all. column -> pick by name (use alias if present).
    # aggregate without GROUP BY -> compute over all rows, return single row.
    pass  # TODO

def execute_group_by(rows, group_cols, select_cols, having):
    # Group rows by group_cols, compute aggregates, apply HAVING filter.
    pass  # TODO

def execute_order_by(rows, order_by):
    # Sort rows. order_by is list of (col, "ASC"/"DESC"). None values sort last.
    pass  # TODO

def evaluate_condition(row, cond):
    # Evaluate a condition AST node against a row. Returns bool.
    # Types: compare (=, !=, <, >, <=, >=, IS NULL, IS NOT NULL),
    #        logic (AND, OR), not, between, in, like (% = any, _ = single char)
    pass  # TODO

# ---- Executor helpers (provided) ----

def _resolve(row, node):
    if node["type"] == "literal":
        return node["value"]
    if node["type"] == "column_ref":
        return row.get(node["name"])
    return None

def _compare(row, cond):
    left = _resolve(row, cond["left"])
    op = cond["op"]
    if op == "IS NULL": return left is None
    if op == "IS NOT NULL": return left is not None
    right = _resolve(row, cond["right"])
    ops = {"=": lambda a, b: a == b, "!=": lambda a, b: a != b, "<>": lambda a, b: a != b,
           "<": lambda a, b: a < b, ">": lambda a, b: a > b, "<=": lambda a, b: a <= b, ">=": lambda a, b: a >= b}
    return ops[op](left, right)

def _sort_key(value):
    if value is None: return (1, "")
    return (0, value)

def _aggregate(rows, func, arg):
    if func == "COUNT":
        if arg == "*": return len(rows)
        return sum(1 for r in rows if r.get(arg) is not None)
    values = [r[arg] for r in rows if r.get(arg) is not None]
    if not values: return None
    if func == "SUM": return sum(values)
    if func == "AVG": return sum(values) / len(values)
    if func == "MIN": return min(values)
    if func == "MAX": return max(values)
    raise ValueError(f"Unknown aggregate: {func}")

# =========================================================================
# QUERY — entry point
# =========================================================================

def query(sql):
    ast = parse(sql)
    return execute(ast)
""")

    # ---- test_tokenizer.py ----
    with open(os.path.join(WORKDIR, "test_tokenizer.py"), "w") as f:
        f.write("""from db import tokenize, TokenStream

def test_tokenize_select_star():
    tokens = tokenize("SELECT * FROM employees")
    assert tokens == [
        ("KEYWORD", "SELECT"), ("SYMBOL", "*"),
        ("KEYWORD", "FROM"), ("IDENTIFIER", "employees"),
    ]

def test_tokenize_number():
    tokens = tokenize("WHERE salary > 100000")
    assert ("NUMBER", "100000") in tokens
    assert ("COMP_OP", ">") in tokens

def test_tokenize_float():
    tokens = tokenize("WHERE rate > 3.14")
    assert ("NUMBER", "3.14") in tokens

def test_tokenize_string():
    tokens = tokenize("WHERE name = 'Alice'")
    assert ("STRING", "'Alice'") in tokens

def test_tokenize_comparison_ops():
    for op in ["=", "!=", "<", ">", "<=", ">="]:
        tokens = tokenize(f"WHERE x {op} 1")
        assert ("COMP_OP", op) in tokens

def test_tokenize_keywords_uppercase():
    tokens = tokenize("select FROM where")
    types = [t[0] for t in tokens]
    assert all(t == "KEYWORD" for t in types)

def test_tokenize_identifier():
    tokens = tokenize("SELECT employee_name FROM t")
    assert ("IDENTIFIER", "employee_name") in tokens

def test_tokenize_symbols():
    tokens = tokenize("COUNT(*)")
    assert ("KEYWORD", "COUNT") in tokens
    assert ("SYMBOL", "(") in tokens
    assert ("SYMBOL", "*") in tokens
    assert ("SYMBOL", ")") in tokens

def test_tokenize_skip_whitespace():
    tokens = tokenize("SELECT  *   FROM   t")
    assert len(tokens) == 4

def test_tokenize_dotted_name():
    tokens = tokenize("employees.id")
    assert tokens == [("IDENTIFIER", "employees"), ("SYMBOL", "."), ("IDENTIFIER", "id")]

def test_tokenize_complex():
    tokens = tokenize("SELECT name, salary FROM employees WHERE dept = 'Engineering' AND salary > 100000")
    keywords = [t[1] for t in tokens if t[0] == "KEYWORD"]
    assert "SELECT" in keywords
    assert "FROM" in keywords
    assert "WHERE" in keywords
    assert "AND" in keywords

# TokenStream tests

def test_stream_peek():
    s = TokenStream([("KEYWORD", "SELECT"), ("SYMBOL", "*")])
    assert s.peek() == ("KEYWORD", "SELECT")
    assert s.peek() == ("KEYWORD", "SELECT")  # doesn't advance

def test_stream_advance():
    s = TokenStream([("KEYWORD", "SELECT"), ("SYMBOL", "*")])
    assert s.advance() == ("KEYWORD", "SELECT")
    assert s.advance() == ("SYMBOL", "*")

def test_stream_expect_success():
    s = TokenStream([("KEYWORD", "SELECT")])
    result = s.expect("KEYWORD", "SELECT")
    assert result == ("KEYWORD", "SELECT")

def test_stream_expect_fail():
    s = TokenStream([("KEYWORD", "FROM")])
    try:
        s.expect("KEYWORD", "SELECT")
        assert False, "Should have raised"
    except SyntaxError:
        pass

def test_stream_match_hit():
    s = TokenStream([("KEYWORD", "DESC"), ("IDENTIFIER", "x")])
    result = s.match("KEYWORD", "DESC")
    assert result == ("KEYWORD", "DESC")
    assert s.peek() == ("IDENTIFIER", "x")

def test_stream_match_miss():
    s = TokenStream([("KEYWORD", "ASC")])
    result = s.match("KEYWORD", "DESC")
    assert result is None
    assert s.peek() == ("KEYWORD", "ASC")  # didn't advance

def test_stream_at_end():
    s = TokenStream([("KEYWORD", "X")])
    assert not s.at_end()
    s.advance()
    assert s.at_end()

def test_stream_peek_at_end():
    s = TokenStream([])
    assert s.peek() is None
""")

    # ---- test_parser.py ----
    with open(os.path.join(WORKDIR, "test_parser.py"), "w") as f:
        f.write("""from db import parse

def test_parse_select_star():
    ast = parse("SELECT * FROM employees")
    assert ast["type"] == "SELECT"
    assert ast["from"] == "employees"
    assert ast["columns"][0]["type"] == "star"

def test_parse_select_columns():
    ast = parse("SELECT name, salary FROM employees")
    assert len(ast["columns"]) == 2
    assert ast["columns"][0] == {"type": "column", "name": "name"}
    assert ast["columns"][1] == {"type": "column", "name": "salary"}

def test_parse_select_alias():
    ast = parse("SELECT name AS n FROM employees")
    assert ast["columns"][0]["alias"] == "n"

def test_parse_select_aggregate():
    ast = parse("SELECT COUNT(*) AS cnt FROM employees")
    col = ast["columns"][0]
    assert col["type"] == "aggregate"
    assert col["func"] == "COUNT"
    assert col["arg"] == "*"
    assert col["alias"] == "cnt"

def test_parse_where_simple():
    ast = parse("SELECT * FROM t WHERE x = 1")
    w = ast["where"]
    assert w["type"] == "compare"
    assert w["op"] == "="
    assert w["left"] == {"type": "column_ref", "name": "x"}
    assert w["right"] == {"type": "literal", "value": 1}

def test_parse_where_string():
    ast = parse("SELECT * FROM t WHERE name = 'Alice'")
    assert ast["where"]["right"] == {"type": "literal", "value": "Alice"}

def test_parse_where_and():
    ast = parse("SELECT * FROM t WHERE a = 1 AND b = 2")
    w = ast["where"]
    assert w["type"] == "logic"
    assert w["op"] == "AND"

def test_parse_where_or():
    ast = parse("SELECT * FROM t WHERE a = 1 OR b = 2")
    w = ast["where"]
    assert w["type"] == "logic"
    assert w["op"] == "OR"

def test_parse_and_or_precedence():
    # AND binds tighter: a OR b AND c => OR(a, AND(b, c))
    ast = parse("SELECT * FROM t WHERE a = 1 OR b = 2 AND c = 3")
    w = ast["where"]
    assert w["type"] == "logic"
    assert w["op"] == "OR"
    assert w["right"]["op"] == "AND"

def test_parse_between():
    ast = parse("SELECT * FROM t WHERE x BETWEEN 1 AND 10")
    w = ast["where"]
    assert w["type"] == "between"

def test_parse_in():
    ast = parse("SELECT * FROM t WHERE x IN (1, 2, 3)")
    w = ast["where"]
    assert w["type"] == "in"
    assert len(w["values"]) == 3

def test_parse_like():
    ast = parse("SELECT * FROM t WHERE name LIKE 'A%'")
    assert ast["where"]["type"] == "like"

def test_parse_is_null():
    ast = parse("SELECT * FROM t WHERE x IS NULL")
    assert ast["where"]["op"] == "IS NULL"

def test_parse_is_not_null():
    ast = parse("SELECT * FROM t WHERE x IS NOT NULL")
    assert ast["where"]["op"] == "IS NOT NULL"

def test_parse_not():
    ast = parse("SELECT * FROM t WHERE NOT x = 1")
    assert ast["where"]["type"] == "not"

def test_parse_join():
    ast = parse("SELECT * FROM a JOIN b ON a.id = b.aid")
    j = ast["joins"][0]
    assert j["type"] == "INNER"
    assert j["table"] == "b"
    assert j["on"] == ("a.id", "b.aid")

def test_parse_left_join():
    ast = parse("SELECT * FROM a LEFT JOIN b ON a.id = b.aid")
    assert ast["joins"][0]["type"] == "LEFT"

def test_parse_group_by():
    ast = parse("SELECT dept, COUNT(*) FROM employees GROUP BY dept")
    assert ast["group_by"] == ["dept"]

def test_parse_having():
    ast = parse("SELECT dept, COUNT(*) AS c FROM t GROUP BY dept HAVING c > 3")
    assert ast["having"] is not None
    assert ast["having"]["type"] == "compare"

def test_parse_order_by_asc():
    ast = parse("SELECT * FROM t ORDER BY x ASC")
    assert ast["order_by"] == [("x", "ASC")]

def test_parse_order_by_desc():
    ast = parse("SELECT * FROM t ORDER BY x DESC")
    assert ast["order_by"] == [("x", "DESC")]

def test_parse_order_by_default():
    ast = parse("SELECT * FROM t ORDER BY x")
    assert ast["order_by"] == [("x", "ASC")]

def test_parse_limit():
    ast = parse("SELECT * FROM t LIMIT 5")
    assert ast["limit"] == 5

def test_parse_distinct():
    ast = parse("SELECT DISTINCT dept FROM employees")
    assert ast["distinct"] is True
""")

    # ---- test_executor.py ----
    with open(os.path.join(WORKDIR, "test_executor.py"), "w") as f:
        f.write("""from db import evaluate_condition, execute_order_by, execute_select, execute_join, execute_group_by
from database import load_table

# evaluate_condition tests

def test_eval_equals():
    row = {"name": "Alice", "salary": 100}
    cond = {"type": "compare", "op": "=", "left": {"type": "column_ref", "name": "name"}, "right": {"type": "literal", "value": "Alice"}}
    assert evaluate_condition(row, cond) is True

def test_eval_greater():
    row = {"salary": 150}
    cond = {"type": "compare", "op": ">", "left": {"type": "column_ref", "name": "salary"}, "right": {"type": "literal", "value": 100}}
    assert evaluate_condition(row, cond) is True

def test_eval_less():
    row = {"salary": 50}
    cond = {"type": "compare", "op": "<", "left": {"type": "column_ref", "name": "salary"}, "right": {"type": "literal", "value": 100}}
    assert evaluate_condition(row, cond) is True

def test_eval_and():
    row = {"a": 1, "b": 2}
    cond = {"type": "logic", "op": "AND",
        "left": {"type": "compare", "op": "=", "left": {"type": "column_ref", "name": "a"}, "right": {"type": "literal", "value": 1}},
        "right": {"type": "compare", "op": "=", "left": {"type": "column_ref", "name": "b"}, "right": {"type": "literal", "value": 2}}}
    assert evaluate_condition(row, cond) is True

def test_eval_or():
    row = {"a": 1, "b": 99}
    cond = {"type": "logic", "op": "OR",
        "left": {"type": "compare", "op": "=", "left": {"type": "column_ref", "name": "a"}, "right": {"type": "literal", "value": 1}},
        "right": {"type": "compare", "op": "=", "left": {"type": "column_ref", "name": "b"}, "right": {"type": "literal", "value": 2}}}
    assert evaluate_condition(row, cond) is True

def test_eval_not():
    row = {"x": 5}
    cond = {"type": "not", "expr": {"type": "compare", "op": "=", "left": {"type": "column_ref", "name": "x"}, "right": {"type": "literal", "value": 5}}}
    assert evaluate_condition(row, cond) is False

def test_eval_between():
    row = {"x": 5}
    cond = {"type": "between", "expr": {"type": "column_ref", "name": "x"}, "low": {"type": "literal", "value": 1}, "high": {"type": "literal", "value": 10}}
    assert evaluate_condition(row, cond) is True

def test_eval_in():
    row = {"x": 3}
    cond = {"type": "in", "expr": {"type": "column_ref", "name": "x"}, "values": [{"type": "literal", "value": 1}, {"type": "literal", "value": 3}, {"type": "literal", "value": 5}]}
    assert evaluate_condition(row, cond) is True

def test_eval_like():
    row = {"name": "Alice"}
    cond = {"type": "like", "expr": {"type": "column_ref", "name": "name"}, "pattern": {"type": "literal", "value": "A%"}}
    assert evaluate_condition(row, cond) is True

def test_eval_is_null():
    row = {"x": None}
    cond = {"type": "compare", "op": "IS NULL", "left": {"type": "column_ref", "name": "x"}, "right": None}
    assert evaluate_condition(row, cond) is True

def test_eval_is_not_null():
    row = {"x": 5}
    cond = {"type": "compare", "op": "IS NOT NULL", "left": {"type": "column_ref", "name": "x"}, "right": None}
    assert evaluate_condition(row, cond) is True

# execute_order_by tests

def test_order_asc():
    rows = [{"x": 3}, {"x": 1}, {"x": 2}]
    result = execute_order_by(rows, [("x", "ASC")])
    assert [r["x"] for r in result] == [1, 2, 3]

def test_order_desc():
    rows = [{"x": 1}, {"x": 3}, {"x": 2}]
    result = execute_order_by(rows, [("x", "DESC")])
    assert [r["x"] for r in result] == [3, 2, 1]

def test_order_none_last():
    rows = [{"x": None}, {"x": 1}, {"x": 3}]
    result = execute_order_by(rows, [("x", "ASC")])
    assert result[0]["x"] == 1
    assert result[-1]["x"] is None

# execute_select tests

def test_select_star():
    rows = [{"a": 1, "b": 2}]
    cols = [{"type": "star"}]
    result = execute_select(rows, cols)
    assert result == [{"a": 1, "b": 2}]

def test_select_columns():
    rows = [{"a": 1, "b": 2, "c": 3}]
    cols = [{"type": "column", "name": "a"}, {"type": "column", "name": "c"}]
    result = execute_select(rows, cols)
    assert result == [{"a": 1, "c": 3}]

def test_select_alias():
    rows = [{"name": "Alice"}]
    cols = [{"type": "column", "name": "name", "alias": "n"}]
    result = execute_select(rows, cols)
    assert result == [{"n": "Alice"}]

def test_select_aggregate_count():
    rows = [{"x": 1}, {"x": 2}, {"x": 3}]
    cols = [{"type": "aggregate", "func": "COUNT", "arg": "*", "alias": "cnt"}]
    result = execute_select(rows, cols)
    assert len(result) == 1
    assert result[0]["cnt"] == 3

# execute_join tests

def test_join_inner():
    left = [{"id": 1, "name": "A"}, {"id": 2, "name": "B"}]
    right_table = "departments"  # we'll use real data
    join = {"type": "INNER", "table": "departments", "on": ("dept", "dept_name")}
    from database import load_table
    employees = load_table("employees")
    result = execute_join(employees[:2], join)
    assert all("budget" in r for r in result)

# execute_group_by tests

def test_group_by_count():
    rows = [{"dept": "A", "x": 1}, {"dept": "A", "x": 2}, {"dept": "B", "x": 3}]
    cols = [{"type": "column", "name": "dept"}, {"type": "aggregate", "func": "COUNT", "arg": "*", "alias": "cnt"}]
    result = execute_group_by(rows, ["dept"], cols, None)
    by_dept = {r["dept"]: r["cnt"] for r in result}
    assert by_dept == {"A": 2, "B": 1}

def test_group_by_sum():
    rows = [{"dept": "A", "val": 10}, {"dept": "A", "val": 20}, {"dept": "B", "val": 5}]
    cols = [{"type": "column", "name": "dept"}, {"type": "aggregate", "func": "SUM", "arg": "val", "alias": "total"}]
    result = execute_group_by(rows, ["dept"], cols, None)
    by_dept = {r["dept"]: r["total"] for r in result}
    assert by_dept == {"A": 30, "B": 5}
""")

    # ---- test_sql.py (end-to-end integration tests) ----
    with open(os.path.join(WORKDIR, "test_sql.py"), "w") as f:
        f.write("""from db import query

# =====================================================================
# Basic SELECT
# =====================================================================

def test_select_all():
    rows = query("SELECT * FROM employees")
    assert len(rows) == 10

def test_select_columns():
    rows = query("SELECT name, dept FROM employees")
    assert all(set(r.keys()) == {"name", "dept"} for r in rows)
    assert rows[0]["name"] == "Alice"

def test_select_single_column():
    rows = query("SELECT name FROM employees")
    assert all(set(r.keys()) == {"name"} for r in rows)

def test_select_with_alias():
    rows = query("SELECT name AS employee_name FROM employees")
    assert "employee_name" in rows[0]
    assert rows[0]["employee_name"] == "Alice"

def test_select_distinct():
    rows = query("SELECT DISTINCT dept FROM employees")
    depts = [r["dept"] for r in rows]
    assert sorted(depts) == ["Engineering", "Marketing", "Sales"]

# =====================================================================
# WHERE — comparisons
# =====================================================================

def test_where_equals():
    rows = query("SELECT name FROM employees WHERE dept = 'Engineering'")
    names = sorted([r["name"] for r in rows])
    assert names == ["Alice", "Bob", "Eve", "Ivan"]

def test_where_not_equals():
    rows = query("SELECT name FROM employees WHERE dept != 'Engineering'")
    assert len(rows) == 6

def test_where_greater():
    rows = query("SELECT name FROM employees WHERE salary > 100000")
    names = sorted([r["name"] for r in rows])
    assert names == ["Alice", "Eve", "Frank", "Grace"]

def test_where_less():
    rows = query("SELECT name FROM employees WHERE salary < 90000")
    names = sorted([r["name"] for r in rows])
    assert names == ["Carol", "Judy"]

def test_where_greater_equal():
    rows = query("SELECT name FROM employees WHERE salary >= 120000")
    names = sorted([r["name"] for r in rows])
    assert names == ["Alice", "Eve", "Frank"]

def test_where_less_equal():
    rows = query("SELECT name FROM employees WHERE salary <= 90000")
    names = sorted([r["name"] for r in rows])
    assert names == ["Carol", "Dave", "Judy"]

# =====================================================================
# WHERE — logic
# =====================================================================

def test_where_and():
    rows = query("SELECT name FROM employees WHERE dept = 'Engineering' AND salary > 100000")
    names = sorted([r["name"] for r in rows])
    assert names == ["Alice", "Eve"]

def test_where_or():
    rows = query("SELECT name FROM employees WHERE dept = 'Sales' OR dept = 'Marketing'")
    assert len(rows) == 6

def test_where_and_or_precedence():
    rows = query(
        "SELECT name FROM employees WHERE dept = 'Sales' OR dept = 'Engineering' AND salary > 100000"
    )
    names = sorted([r["name"] for r in rows])
    assert names == ["Alice", "Carol", "Dave", "Eve", "Frank"]

def test_where_not():
    rows = query("SELECT name FROM employees WHERE NOT dept = 'Engineering'")
    assert len(rows) == 6

# =====================================================================
# WHERE — special operators
# =====================================================================

def test_where_between():
    rows = query("SELECT name FROM employees WHERE salary BETWEEN 90000 AND 110000")
    names = sorted([r["name"] for r in rows])
    assert names == ["Bob", "Dave", "Grace", "Heidi", "Ivan"]

def test_where_in():
    rows = query("SELECT name FROM employees WHERE dept IN ('Engineering', 'Marketing')")
    assert len(rows) == 7

def test_where_like():
    rows = query("SELECT name FROM employees WHERE name LIKE 'A%'")
    assert [r["name"] for r in rows] == ["Alice"]

def test_where_is_null():
    rows = query("SELECT name FROM employees WHERE manager_id IS NULL")
    names = sorted([r["name"] for r in rows])
    assert names == ["Eve", "Frank", "Grace"]

def test_where_is_not_null():
    rows = query("SELECT name FROM employees WHERE manager_id IS NOT NULL")
    assert len(rows) == 7

# =====================================================================
# Aggregates
# =====================================================================

def test_count_star():
    rows = query("SELECT COUNT(*) AS cnt FROM employees")
    assert rows[0]["cnt"] == 10

def test_sum():
    rows = query("SELECT SUM(salary) AS total FROM employees")
    assert rows[0]["total"] == 1071000

def test_avg():
    rows = query("SELECT AVG(salary) AS avg_sal FROM employees")
    assert rows[0]["avg_sal"] == 107100.0

def test_min_max():
    rows = query("SELECT MIN(salary) AS low, MAX(salary) AS high FROM employees")
    assert rows[0]["low"] == 85000
    assert rows[0]["high"] == 150000

# =====================================================================
# GROUP BY
# =====================================================================

def test_group_by_count():
    rows = query("SELECT dept, COUNT(*) AS cnt FROM employees GROUP BY dept")
    result = {r["dept"]: r["cnt"] for r in rows}
    assert result == {"Engineering": 4, "Sales": 3, "Marketing": 3}

def test_group_by_sum():
    rows = query("SELECT dept, SUM(salary) AS total FROM employees GROUP BY dept")
    result = {r["dept"]: r["total"] for r in rows}
    assert result["Engineering"] == 463000

def test_group_by_having():
    rows = query("SELECT dept, COUNT(*) AS cnt FROM employees GROUP BY dept HAVING cnt > 3")
    assert len(rows) == 1
    assert rows[0]["dept"] == "Engineering"

# =====================================================================
# ORDER BY
# =====================================================================

def test_order_by_asc():
    rows = query("SELECT name, salary FROM employees ORDER BY salary ASC LIMIT 3")
    names = [r["name"] for r in rows]
    assert names == ["Carol", "Judy", "Dave"]

def test_order_by_desc():
    rows = query("SELECT name, salary FROM employees ORDER BY salary DESC LIMIT 3")
    names = [r["name"] for r in rows]
    assert names == ["Eve", "Frank", "Alice"]

def test_order_by_string_desc():
    rows = query("SELECT name FROM employees ORDER BY name DESC LIMIT 3")
    names = [r["name"] for r in rows]
    assert names == ["Judy", "Ivan", "Heidi"]

# =====================================================================
# JOIN
# =====================================================================

def test_inner_join():
    rows = query(
        "SELECT name, project_name FROM employees "
        "JOIN projects ON employees.id = projects.lead_id"
    )
    assert len(rows) == 5
    result = {r["name"]: r["project_name"] for r in rows}
    assert result["Alice"] == "Search Engine"
    assert result["Eve"] == "ML Pipeline"

def test_left_join():
    rows = query(
        "SELECT name, project_name FROM employees "
        "LEFT JOIN projects ON employees.id = projects.lead_id"
    )
    assert len(rows) == 10
    no_project = [r["name"] for r in rows if r["project_name"] is None]
    assert "Bob" in no_project

def test_join_with_where():
    rows = query(
        "SELECT name, project_name FROM employees "
        "JOIN projects ON employees.id = projects.lead_id "
        "WHERE dept = 'Engineering'"
    )
    names = sorted([r["name"] for r in rows])
    assert names == ["Alice", "Eve"]

def test_join_different_tables():
    rows = query(
        "SELECT name, budget FROM employees "
        "JOIN departments ON employees.dept = departments.dept_name"
    )
    assert len(rows) == 10
    alice = [r for r in rows if r["name"] == "Alice"][0]
    assert alice["budget"] == 500000

# =====================================================================
# LIMIT
# =====================================================================

def test_limit():
    rows = query("SELECT name FROM employees LIMIT 3")
    assert len(rows) == 3

# =====================================================================
# Combined
# =====================================================================

def test_group_order():
    rows = query(
        "SELECT dept, AVG(salary) AS avg_sal FROM employees "
        "GROUP BY dept ORDER BY avg_sal DESC"
    )
    assert rows[0]["dept"] == "Engineering"

def test_where_order_limit():
    rows = query(
        "SELECT name, salary FROM employees "
        "WHERE dept = 'Engineering' ORDER BY salary DESC LIMIT 2"
    )
    assert rows[0]["name"] == "Eve"
    assert rows[1]["name"] == "Alice"

def test_departments_table():
    rows = query("SELECT * FROM departments")
    assert len(rows) == 3

def test_projects_table():
    rows = query("SELECT * FROM projects")
    assert len(rows) == 5
""")

    # ---- AGENTS.md ----
    with open(os.path.join(WORKDIR, "AGENTS.md"), "w") as f:
        f.write("""# Mini SQL Database

## Architecture
- db.py: Single file containing tokenizer, parser, and executor
- database.py: CSV loader (already implemented)

## Rules
- AND has higher precedence than OR in WHERE clauses
- ORDER BY DESC must sort descending, ASC ascending
- JOIN ON must handle dotted column names like table.column
- All 4 test files must pass before done
- Run: python -m pytest test_tokenizer.py test_parser.py test_executor.py test_sql.py -v
""")

if __name__ == "__main__":
    setup_test_project()
    print(f"Test project created in {WORKDIR}")
