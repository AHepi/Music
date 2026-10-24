import ast, sys, os, glob, builtins
sys.dont_write_bytecode = True
ROOT='/home/user/Music/plugins/explainer-film'
files = glob.glob(ROOT+'/kit/place-kit/**/*.py', recursive=True)+[ROOT+'/kit/calculators/'+n for n in ('place_audit_check.py','picture_measures.py','preflight.py','plan_budget.py','paint_request.py')]+[ROOT+'/kit/paper-film/blender/'+n for n in ('textures.py','model_kit.py','model_lint.py','make_check_file.py')]+glob.glob(ROOT+'/kit/calculators/tests/test_place*.py')+glob.glob(ROOT+'/kit/calculators/tests/test_picture*.py')+glob.glob(ROOT+'/kit/calculators/tests/test_build*.py')+glob.glob(ROOT+'/kit/calculators/tests/test_model_kit_surfaces.py')
bi = set(dir(builtins)) | {'__file__','__name__','args','bpy'}
for f in sorted(files):
    src = open(f, encoding='utf-8').read()
    try:
        tree = ast.parse(src)
    except SyntaxError as e:
        print('SYNTAX', f, e); continue
    imported = {}
    for n in ast.walk(tree):
        if isinstance(n, ast.Import):
            for a in n.names: imported[(a.asname or a.name).split('.')[0]] = n.lineno
        elif isinstance(n, ast.ImportFrom):
            for a in n.names: imported[a.asname or a.name] = n.lineno
    used = {n.id for n in ast.walk(tree) if isinstance(n, ast.Name)} | {n.value.id for n in ast.walk(tree) if isinstance(n, ast.Attribute) and isinstance(n.value, ast.Name)}
    # names in __all__ or noqa lines
    lines = src.splitlines()
    unused = [(k, ln) for k, ln in imported.items() if k not in used and 'noqa' not in lines[ln-1] and k != '*' and not f.endswith('__init__.py')]
    # undefined names (rough): module-level defined + function args + assigned anywhere
    defined = set(bi)
    for n in ast.walk(tree):
        if isinstance(n, (ast.FunctionDef, ast.ClassDef, ast.AsyncFunctionDef)): defined.add(n.name)
        if isinstance(n, ast.arg): defined.add(n.arg)
        if isinstance(n, ast.Name) and isinstance(n.ctx, (ast.Store, ast.Del)): defined.add(n.id)
        if isinstance(n, ast.ExceptHandler) and n.name: defined.add(n.name)
        if isinstance(n, (ast.Import, ast.ImportFrom)):
            for a in n.names: defined.add((a.asname or a.name).split('.')[0])
        if isinstance(n, ast.comprehension):
            for t in ast.walk(n.target):
                if isinstance(t, ast.Name): defined.add(t.id)
        if isinstance(n, ast.Global):
            defined.update(n.names)
    undefined = sorted({n.id for n in ast.walk(tree) if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Load) and n.id not in defined})
    rel = os.path.relpath(f, ROOT)
    if unused or undefined:
        print(rel, '| unused imports:', unused[:6], '| undefined:', undefined[:6])
print('files checked', len(files))
