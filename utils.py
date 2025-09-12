import ast


def check_code_safety(code):
    """
    Check if the code is safe to execute.
    """
    # 定义不允许的导入和关键词
    forbidden_imports = [
        "importlib",
        "os",
        "sys",
        "subprocess",
        "socket",
        "threading",
        "multiprocessing",
        "pickle",
        "marshal",
        "shelve",
        "sqlite3",
        "ctypes",
        "cffi",
    ]

    forbidden_keywords = ["exec", "eval", "open"]

    try:
        tree = ast.parse(code)
    except SyntaxError:
        raise ValueError("Python 语法无效。")

    for node in ast.walk(tree):
        if isinstance(node, ast.Import) or isinstance(node, ast.ImportFrom):
            for alias in node.names:
                if alias.name in forbidden_imports:
                    raise ValueError(f"检测到禁止的模块：{alias.name}")
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name) and node.func.id in forbidden_keywords:
                raise ValueError(f"检测到禁止的关键字：{node.func.id}")
