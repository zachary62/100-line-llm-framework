"""Ground truth implementations for tokenizer.py, parser.py, executor.py.
Not used by the test project — just a reference for verifying correctness."""

# ===== executor.py =====

EXECUTOR_PY = '''# SQL Executor — takes an AST and executes against CSV tables
from database import load_table

def execute(ast):
    rows = load_table(ast["from"])
    for join in ast.get("joins", []):
        rows = execute_join(rows, join)
    if ast["where"]:
        rows = [r for r in rows if evaluate_condition(r, ast["where"])]
    if ast["group_by"]:
        rows = execute_group_by(rows, ast["group_by"], ast["columns"], ast.get("having"))
    if not ast["group_by"]:
        rows = execute_select(rows, ast["columns"])
    if ast.get("distinct"):
        seen = []
        unique_rows = []
        for r in rows:
            key = tuple(sorted(r.items()))
            if key not in seen:
                seen.append(key)
                unique_rows.append(r)
        rows = unique_rows
    if ast["order_by"]:
        rows = execute_order_by(rows, ast["order_by"])
    if ast["limit"]:
        rows = rows[:ast["limit"]]
    return rows

def execute_join(left_rows, join):
    right_rows = load_table(join["table"])
    left_col, right_col = join["on"]
    left_key = left_col.split(".")[-1]
    right_key = right_col.split(".")[-1]
    result = []
    if join["type"] == "INNER":
        for lr in left_rows:
            for rr in right_rows:
                if lr.get(left_key) == rr.get(right_key):
                    result.append({**lr, **rr})
    elif join["type"] == "LEFT":
        for lr in left_rows:
            matched = False
            for rr in right_rows:
                if lr.get(left_key) == rr.get(right_key):
                    result.append({**lr, **rr})
                    matched = True
            if not matched:
                result.append({**lr, **{k: None for k in right_rows[0]}})
    return result

def execute_select(rows, columns):
    if any(c["type"] == "star" for c in columns):
        return rows
    result = []
    for row in rows:
        new_row = {}
        for col in columns:
            if col["type"] == "column":
                name = col.get("alias", col["name"])
                new_row[name] = row.get(col["name"])
            elif col["type"] == "aggregate":
                name = col.get("alias", f"{col['func']}({col['arg']})")
                new_row[name] = _aggregate(rows, col["func"], col["arg"])
        result.append(new_row)
    if any(c["type"] == "aggregate" for c in columns):
        return [result[0]] if result else []
    return result

def execute_group_by(rows, group_cols, select_cols, having):
    groups = {}
    for row in rows:
        key = tuple(row.get(c) for c in group_cols)
        groups.setdefault(key, []).append(row)
    result = []
    for key, group_rows in groups.items():
        row = {}
        for i, gc in enumerate(group_cols):
            row[gc] = key[i]
        for col in select_cols:
            if col["type"] == "aggregate":
                name = col.get("alias", f"{col['func']}({col['arg']})")
                row[name] = _aggregate(group_rows, col["func"], col["arg"])
        if having and not evaluate_condition(row, having):
            continue
        result.append(row)
    return result

def execute_order_by(rows, order_by):
    for col, direction in reversed(order_by):
        reverse = direction == "DESC"
        rows = sorted(rows, key=lambda r: (_sort_key(r.get(col)),), reverse=reverse)
    return rows

def _sort_key(value):
    if value is None:
        return (1, "")
    return (0, value)

def _aggregate(rows, func, arg):
    if func == "COUNT":
        if arg == "*":
            return len(rows)
        return sum(1 for r in rows if r.get(arg) is not None)
    values = [r[arg] for r in rows if r.get(arg) is not None]
    if not values:
        return None
    if func == "SUM":
        return sum(values)
    if func == "AVG":
        return sum(values) / len(values)
    if func == "MIN":
        return min(values)
    if func == "MAX":
        return max(values)
    raise ValueError(f"Unknown aggregate: {func}")

def evaluate_condition(row, cond):
    if cond["type"] == "compare":
        return _compare(row, cond)
    if cond["type"] == "logic":
        left = evaluate_condition(row, cond["left"])
        right = evaluate_condition(row, cond["right"])
        if cond["op"] == "AND":
            return left and right
        if cond["op"] == "OR":
            return left or right
    if cond["type"] == "not":
        return not evaluate_condition(row, cond["expr"])
    if cond["type"] == "between":
        val = _resolve(row, cond["expr"])
        low = _resolve(row, cond["low"])
        high = _resolve(row, cond["high"])
        return low <= val <= high
    if cond["type"] == "in":
        val = _resolve(row, cond["expr"])
        return val in [_resolve(row, v) for v in cond["values"]]
    if cond["type"] == "like":
        val = _resolve(row, cond["expr"])
        pattern = _resolve(row, cond["pattern"])
        import re
        regex = "^" + pattern.replace("%", ".*").replace("_", ".") + "$"
        return bool(re.match(regex, str(val)))
    return bool(_resolve(row, cond))

def _compare(row, cond):
    left = _resolve(row, cond["left"])
    op = cond["op"]
    if op == "IS NULL":
        return left is None
    if op == "IS NOT NULL":
        return left is not None
    right = _resolve(row, cond["right"])
    if op == "=":
        return left == right
    if op in ("!=", "<>"):
        return left != right
    if op == "<":
        return left < right
    if op == ">":
        return left > right
    if op == "<=":
        return left <= right
    if op == ">=":
        return left >= right
    raise ValueError(f"Unknown operator: {op}")

def _resolve(row, node):
    if node["type"] == "literal":
        return node["value"]
    if node["type"] == "column_ref":
        return row.get(node["name"])
    return None
'''
