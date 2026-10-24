import ast, sys, re
p = sys.argv[1]
src = open(p, encoding="utf-8").read()
tree = ast.parse(src)
print("== imports (all, incl. nested) ==")
for n in ast.walk(tree):
    if isinstance(n, ast.Import):
        print(n.lineno, "import", [a.name for a in n.names])
    elif isinstance(n, ast.ImportFrom):
        print(n.lineno, "from", n.module, [a.name for a in n.names])
print("== top-level statements that are not def/import/assign/docstring/class ==")
for n in tree.body:
    if isinstance(n, (ast.FunctionDef, ast.ClassDef, ast.Import, ast.ImportFrom)):
        continue
    if isinstance(n, ast.Assign):
        print(n.lineno, "assign", ast.unparse(n)[:90]); continue
    if isinstance(n, ast.Expr) and isinstance(n.value, ast.Constant):
        print(n.lineno, "docstring/const"); continue
    print(n.lineno, type(n).__name__, ast.unparse(n)[:120])
print("== decorators ==")
for n in ast.walk(tree):
    if isinstance(n, ast.FunctionDef) and n.decorator_list:
        print(n.lineno, n.name, [ast.unparse(d) for d in n.decorator_list])
print("== calls: bpy.ops.* ==")
ops = {}
for n in ast.walk(tree):
    if isinstance(n, ast.Call):
        s = ast.unparse(n.func)
        if s.startswith("bpy.ops."):
            ops.setdefault(s, []).append(n.lineno)
for k, v in sorted(ops.items()):
    print(k, v)
print("== calls: bpy.data.*.remove/clear/etc, builtins of interest ==")
for n in ast.walk(tree):
    if isinstance(n, ast.Call):
        s = ast.unparse(n.func)
        if re.search(r"\.(remove|unlink|clear|batch_remove|orphans_purge|rmtree|rename|replace|write|save|save_as_mainfile|load|new)$", s) or s in ("open","exec","eval","compile","__import__","getattr","setattr","input","print","hash"):
            print(n.lineno, ast.unparse(n)[:110])
print("== string literals mentioning net/system words ==")
pat = re.compile(r"http|ftp|ssh|curl|wget|socket|subprocess|system|popen|environ|getenv|token|key|password|~|/home|/tmp|\.runpod|npx|pip|install", re.I)
for n in ast.walk(tree):
    if isinstance(n, ast.Constant) and isinstance(n.value, str) and pat.search(n.value):
        print(n.lineno, repr(n.value[:120]))
