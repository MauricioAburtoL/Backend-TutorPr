# backend/app/ast_cfg.py
import ast
from typing import List, Dict, Any, Tuple, Optional

# ---------- Tipos comunes ----------
class CFGNode(dict):
    def __init__(self, _id: str, kind: str, label: str, lineno: int, end_lineno: int):
        super().__init__(id=_id, type=kind, label=label, lineno=lineno, end_lineno=end_lineno)

class CFG:
    def __init__(self):
        self.nodes: List[CFGNode] = []
        self.edges: List[Tuple[str, str]] = []
        self._i = 0
    def nid(self) -> str:
        self._i += 1
        return f"N{self._i}"
    def add(self, kind: str, label: str, ln: int, en: int) -> str:
        _id = self.nid()
        self.nodes.append(CFGNode(_id, kind, label, ln, en))
        return _id

# ---------- Render a Mermaid (independiente del lenguaje) ----------
def _safe_label(text: str) -> str:
    s = str(text).replace("\n", " ")
    s = s.replace('"', '\\"').replace("<", "&lt;").replace(">", "&gt;")
    s = s.replace("{", "(").replace("}", ")")
    return s

def cfg_to_mermaid(nodes: List[CFGNode], edges: List[Tuple[str, str]]) -> str:
    lines = ["flowchart TD"]
    for n in nodes:
        lab = _safe_label(n["label"])
        if n["type"] == "start":
            shape = f'{n["id"]}([start])'
        elif n["type"] == "if":
            shape = f'{n["id"]}{{"{lab}"}}'
        elif n["type"] == "loop":
            shape = f'{n["id"]}(["{lab}"])'
        else:
            shape = f'{n["id"]}["{lab}"]'  # <- corregido
        lines.append(shape)
    for a, b in edges:
        lines.append(f"{a} --> {b}")
    return "\n".join(lines)

# ---------- Adaptadores por lenguaje ----------
def _cfg_python(code: str) -> Dict[str, Any]:
    """Construye un CFG legible a partir del AST de Python."""
    try:
        tree = ast.parse(code)
    except SyntaxError:
        nodes = [CFGNode("E", "error", "Syntax Error", 1, 1)]
        return {"language": "python", "nodes": nodes, "edges": []}

    g = CFG()
    loop_stack: List[Tuple[str, str]] = []  # (loop_head, loop_exit)
    exc_sink_id: Optional[str] = None

    def exc_sink() -> str:
        nonlocal exc_sink_id
        if exc_sink_id is None:
            exc_sink_id = g.add("stmt", "<exception>", 0, 0)
        return exc_sink_id

    def connect(sources: List[str], target: str) -> None:
        for source in sources:
            edge = (source, target)
            if edge not in g.edges:
                g.edges.append(edge)

    def unique(node_ids: List[str]) -> List[str]:
        return list(dict.fromkeys(node_ids))

    def statement_label(statement: ast.stmt) -> str:
        if hasattr(ast, "unparse"):
            try:
                return ast.unparse(statement)
            except Exception:
                pass
        return statement.__class__.__name__

    def add_statement(statement: ast.stmt, kind: str = "stmt", label: str | None = None) -> str:
        line = getattr(statement, "lineno", 1)
        end_line = getattr(statement, "end_lineno", line)
        return g.add(kind, label or statement_label(statement), line, end_line)

    def build_block(statements: List[ast.stmt], incoming: List[str]) -> List[str]:
        exits = incoming
        for statement in statements:
            exits = build_statement(statement, exits)
        return unique(exits)

    def build_statement(statement: ast.stmt, incoming: List[str]) -> List[str]:
        if isinstance(statement, ast.If):
            condition = ast.unparse(statement.test) if hasattr(ast, "unparse") else "cond"
            decision = add_statement(statement, "if", f"if {condition}")
            connect(incoming, decision)
            then_exits = build_block(statement.body, [decision])
            else_exits = (
                build_block(statement.orelse, [decision])
                if statement.orelse
                else [decision]
            )
            return unique(then_exits + else_exits)

        if isinstance(statement, (ast.For, ast.While, ast.AsyncFor)):
            if isinstance(statement, (ast.For, ast.AsyncFor)) and hasattr(ast, "unparse"):
                prefix = "async for" if isinstance(statement, ast.AsyncFor) else "for"
                label = f"{prefix} {ast.unparse(statement.target)} in {ast.unparse(statement.iter)}"
            elif hasattr(ast, "unparse"):
                label = f"while {ast.unparse(statement.test)}"
            else:
                label = statement.__class__.__name__.lower()

            head = add_statement(statement, "loop", label)
            loop_exit = g.add("stmt", "loop_end", statement.lineno, statement.lineno)
            connect(incoming, head)
            connect([head], loop_exit)

            loop_stack.append((head, loop_exit))
            body_exits = build_block(statement.body, [head])
            loop_stack.pop()
            connect(body_exits, head)

            if statement.orelse:
                return build_block(statement.orelse, [loop_exit])
            return [loop_exit]

        if isinstance(statement, ast.Break):
            node = add_statement(statement, label="break")
            connect(incoming, node)
            if loop_stack:
                connect([node], loop_stack[-1][1])
            return []

        if isinstance(statement, ast.Continue):
            node = add_statement(statement, label="continue")
            connect(incoming, node)
            if loop_stack:
                connect([node], loop_stack[-1][0])
            return []

        if isinstance(statement, ast.Return):
            label = "return"
            if statement.value is not None and hasattr(ast, "unparse"):
                label = f"return {ast.unparse(statement.value)}"
            node = add_statement(statement, label=label)
            connect(incoming, node)
            return []

        if isinstance(statement, ast.Raise):
            label = statement_label(statement)
            node = add_statement(statement, label=label)
            connect(incoming, node)
            connect([node], exc_sink())
            return []

        if isinstance(statement, ast.Try):
            try_node = add_statement(statement, label="try")
            connect(incoming, try_node)
            body_exits = build_block(statement.body, [try_node])
            normal_exits = (
                build_block(statement.orelse, body_exits)
                if statement.orelse
                else body_exits
            )

            handler_exits: List[str] = []
            for handler in statement.handlers:
                exception_type = (
                    ast.unparse(handler.type)
                    if handler.type is not None and hasattr(ast, "unparse")
                    else ""
                )
                label = f"except {exception_type}".rstrip()
                handler_node = g.add(
                    "stmt",
                    label,
                    handler.lineno,
                    getattr(handler, "end_lineno", handler.lineno),
                )
                connect([try_node], handler_node)
                handler_exits.extend(build_block(handler.body, [handler_node]))

            exits = unique(normal_exits + handler_exits)
            if statement.finalbody:
                return build_block(statement.finalbody, exits or [try_node])
            return exits

        if isinstance(statement, (ast.With, ast.AsyncWith)):
            prefix = "async with" if isinstance(statement, ast.AsyncWith) else "with"
            context = (
                ast.unparse(statement.items[0].context_expr)
                if statement.items and hasattr(ast, "unparse")
                else ""
            )
            with_node = add_statement(statement, label=f"{prefix} {context}".rstrip())
            connect(incoming, with_node)
            body_exits = build_block(statement.body, [with_node])
            exit_node = g.add("stmt", "with_exit", statement.lineno, statement.lineno)
            connect(body_exits or [with_node], exit_node)
            return [exit_node]

        if hasattr(ast, "Match") and isinstance(statement, ast.Match):
            subject = ast.unparse(statement.subject) if hasattr(ast, "unparse") else ""
            match_node = add_statement(statement, label=f"match {subject}".rstrip())
            connect(incoming, match_node)
            case_exits: List[str] = []

            for case in statement.cases:
                pattern = ast.unparse(case.pattern) if hasattr(ast, "unparse") else "case"
                guard = (
                    f" if {ast.unparse(case.guard)}"
                    if case.guard is not None and hasattr(ast, "unparse")
                    else ""
                )
                case_line = getattr(case.pattern, "lineno", statement.lineno)
                case_end = getattr(case.pattern, "end_lineno", case_line)
                case_node = g.add("stmt", f"case {pattern}{guard}", case_line, case_end)
                connect([match_node], case_node)
                case_exits.extend(build_block(case.body, [case_node]))

            join = g.add("stmt", "match_join", statement.lineno, statement.lineno)
            connect(case_exits or [match_node], join)
            return [join]

        if isinstance(statement, (ast.FunctionDef, ast.AsyncFunctionDef)):
            arguments = ast.unparse(statement.args) if hasattr(ast, "unparse") else ""
            prefix = "async def" if isinstance(statement, ast.AsyncFunctionDef) else "def"
            function_node = add_statement(
                statement,
                label=f"{prefix} {statement.name}({arguments})",
            )
            connect(incoming, function_node)
            build_block(statement.body, [function_node])
            return [function_node]

        if isinstance(statement, ast.ClassDef):
            class_node = add_statement(statement, label=f"class {statement.name}")
            connect(incoming, class_node)
            build_block(statement.body, [class_node])
            return [class_node]

        if isinstance(statement, ast.Expr) and isinstance(statement.value, ast.IfExp):
            condition = (
                ast.unparse(statement.value.test)
                if hasattr(ast, "unparse")
                else "cond"
            )
            decision = add_statement(statement, "if", f"if {condition}")
            connect(incoming, decision)
            then_node = g.add(
                "stmt",
                ast.unparse(statement.value.body) if hasattr(ast, "unparse") else "then",
                statement.lineno,
                statement.lineno,
            )
            else_node = g.add(
                "stmt",
                ast.unparse(statement.value.orelse) if hasattr(ast, "unparse") else "else",
                statement.lineno,
                statement.lineno,
            )
            join = g.add("stmt", "ifexp_join", statement.lineno, statement.lineno)
            connect([decision], then_node)
            connect([decision], else_node)
            connect([then_node, else_node], join)
            return [join]

        node = add_statement(statement)
        connect(incoming, node)
        return [node]

    entry = g.add("start", "start", 1, 1)
    build_block(tree.body, [entry])

    return {"language": "python", "nodes": g.nodes, "edges": g.edges}



def _cfg_java_stub(code: str) -> Dict[str, Any]:
    # Placeholder: reemplaza por microservicio JavaParser o tree-sitter
    g = CFG()
    s = g.add("start", "start", 1, 1)
    x = g.add("stmt", "Java stub", 1, 1)
    g.edges.append((s, x))
    return {"language": "java", "nodes": g.nodes, "edges": g.edges}

def _cfg_cpp_stub(code: str) -> Dict[str, Any]:
    # Placeholder: reemplaza por libclang / tree-sitter
    g = CFG()
    s = g.add("start", "start", 1, 1)
    x = g.add("stmt", "C++ stub", 1, 1)
    g.edges.append((s, x))
    return {"language": "cpp", "nodes": g.nodes, "edges": g.edges}

_ADAPTERS = {
    "python": _cfg_python,
    "java": _cfg_java_stub,
    "cpp": _cfg_cpp_stub,
}

def build_cfg_any(lang: str, code: str) -> Dict[str, Any]:
    if lang not in _ADAPTERS:
        raise ValueError(f"language not supported: {lang}")

    data = _ADAPTERS[lang](code)  # debe devolver al menos {"nodes": [...], "edges": [...]}
    mermaid = cfg_to_mermaid(data.get("nodes", []), data.get("edges", []))

    return {
        "language": lang,
        "mermaid": mermaid,
        "nodes": data.get("nodes", []),
        "edges": data.get("edges", []),  # ← IMPORTANTE
    }
