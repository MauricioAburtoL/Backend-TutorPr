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
    """Construye CFG desde código Python usando ast (cobertura ampliada)."""
    try:
        tree = ast.parse(code)
    except SyntaxError:
        nodes = [CFGNode("E", "error", "Syntax Error", 1, 1)]
        return {"language": "python", "nodes": nodes, "edges": []}

    g = CFG()
    loop_stack: List[Tuple[str, str]] = []  # (loop_head, loop_exit)

    # Sumidero de excepciones: se crea solo si se usa.
    exc_sink_id: Optional[str] = None
    def exc_sink() -> str:
        nonlocal exc_sink_id
        if exc_sink_id is None:
            exc_sink_id = g.add("stmt", "<exception>", 0, 0)
        return exc_sink_id

    def add_stmt_node(s: ast.stmt) -> str:
        if isinstance(s, ast.Expr) and isinstance(getattr(s, "value", None), ast.Call) and hasattr(ast, "unparse"):
            lab = ast.unparse(s.value)  # p.ej. print(i)
        else:
            lab = s.__class__.__name__
        return g.add("stmt", lab, s.lineno, getattr(s, "end_lineno", s.lineno))

    def join_node(label: str, ln: int) -> str:
        return g.add("stmt", label, ln, ln)

    def visit(stmts: List[ast.stmt]) -> List[str]:
        prev = None
        heads: List[str] = []
        last = None

        for s in stmts:

            # ---------- IF / ELIF / ELSE ----------
            if isinstance(s, ast.If):
                cond = ast.unparse(s.test) if hasattr(ast, "unparse") else "cond"
                cur = g.add("if", f"if {cond}", s.lineno, getattr(s, "end_lineno", s.lineno))
                if prev:
                    g.edges.append((prev, cur))
                if not heads:
                    heads = [cur]

                then_heads = visit(s.body)

                if len(s.orelse) == 1 and isinstance(s.orelse[0], ast.If):
                    else_heads = visit([s.orelse[0]])  # elif cadena
                else:
                    else_heads = visit(s.orelse) if s.orelse else []

                for h in (then_heads or [cur]):
                    g.edges.append((cur, h))
                for h in (else_heads or [cur]):
                    g.edges.append((cur, h))

                prev = cur
                last = cur

            # ---------- FOR / WHILE (entrada, retorno y salida) ----------
            elif isinstance(s, (ast.For, ast.While)):
                head = g.add("loop", type(s).__name__.lower(),
                             s.lineno, getattr(s, "end_lineno", s.lineno))
                exitn = g.add("stmt", "loop_end", s.lineno, s.lineno)
                if prev:
                    g.edges.append((prev, head))
                if not heads:
                    heads = [head]

                loop_stack.append((head, exitn))
                body_heads = visit(s.body)

                for h in (body_heads or []):          # entrada
                    g.edges.append((head, h))
                for h in (body_heads or [head]):      # retorno
                    g.edges.append((h, head))
                g.edges.append((head, exitn))         # salida

                loop_stack.pop()
                prev = exitn
                last = exitn

            # ---------- BREAK ----------
            elif isinstance(s, ast.Break):
                cur = g.add("stmt", "break", s.lineno, getattr(s, "end_lineno", s.lineno))
                if prev:
                    g.edges.append((prev, cur))
                if loop_stack:
                    _, loop_exit = loop_stack[-1]
                    g.edges.append((cur, loop_exit))
                prev = None
                last = cur
                if not heads:
                    heads = [cur]

            # ---------- CONTINUE ----------
            elif isinstance(s, ast.Continue):
                cur = g.add("stmt", "continue", s.lineno, getattr(s, "end_lineno", s.lineno))
                if prev:
                    g.edges.append((prev, cur))
                if loop_stack:
                    loop_head, _ = loop_stack[-1]
                    g.edges.append((cur, loop_head))
                prev = None
                last = cur
                if not heads:
                    heads = [cur]

            # ---------- RETURN ----------
            elif isinstance(s, ast.Return):
                cur = g.add("stmt", "return", s.lineno, getattr(s, "end_lineno", s.lineno))
                if prev:
                    g.edges.append((prev, cur))
                prev = None
                last = cur
                if not heads:
                    heads = [cur]

            # ---------- RAISE ----------
            elif isinstance(s, ast.Raise):
                lab = "raise " + (ast.unparse(s.exc) if hasattr(ast, "unparse") and s.exc else "")
                cur = g.add("stmt", lab, s.lineno, getattr(s, "end_lineno", s.lineno))
                if prev:
                    g.edges.append((prev, cur))
                g.edges.append((cur, exc_sink()))
                prev = None
                last = cur
                if not heads:
                    heads = [cur]

            # ---------- TRY / EXCEPT / ELSE / FINALLY ----------
            elif isinstance(s, ast.Try):
                tnode = g.add("stmt", "try", s.lineno, getattr(s, "end_lineno", s.lineno))
                if prev:
                    g.edges.append((prev, tnode))
                if not heads:
                    heads = [tnode]

                body_heads = visit(s.body)
                except_heads_all: List[str] = []
                for h in s.handlers:
                    et = ast.unparse(h.type) if hasattr(ast, "unparse") and h.type else "except"
                    en = g.add("stmt", f"except {et}", h.lineno, getattr(h, "end_lineno", h.lineno))
                    g.edges.append((tnode, en))
                    eh = visit(h.body)
                    for x in (eh or [en]):
                        except_heads_all.append(x)

                else_heads = visit(s.orelse) if s.orelse else []

                for h in (body_heads or [tnode]):
                    g.edges.append((tnode, h))

                if s.finalbody:
                    fin_heads = visit(s.finalbody)
                    tails = (body_heads or [tnode]) + (except_heads_all or []) + (else_heads or [])
                    for th in tails:
                        for fh in (fin_heads or []):
                            g.edges.append((th, fh))
                    j = join_node("try_join", s.lineno)
                    for fh in (fin_heads or []):
                        g.edges.append((fh, j))
                    prev = j
                    last = j
                else:
                    j = join_node("try_join", s.lineno)
                    for th in (body_heads or [tnode]):
                        g.edges.append((th, j))
                    for eh in (except_heads_all or []):
                        g.edges.append((eh, j))
                    for elh in (else_heads or []):
                        g.edges.append((elh, j))
                    prev = j
                    last = j

            # ---------- WITH ----------
            elif isinstance(s, ast.With):
                lab = "with " + (ast.unparse(s.items[0].context_expr) if hasattr(ast, "unparse") and s.items else "")
                wnode = g.add("stmt", lab, s.lineno, getattr(s, "end_lineno", s.lineno))
                if prev:
                    g.edges.append((prev, wnode))
                if not heads:
                    heads = [wnode]
                wb = visit(s.body)
                for h in (wb or []):
                    g.edges.append((wnode, h))
                j = join_node("with_exit", s.lineno)
                for h in (wb or [wnode]):
                    g.edges.append((h, j))
                prev = j
                last = j

            # ---------- MATCH / CASE (Py 3.10+) ----------
            elif hasattr(ast, "Match") and isinstance(s, ast.Match):
                mnode = g.add("stmt", "match", s.lineno, getattr(s, "end_lineno", s.lineno))
                if prev:
                    g.edges.append((prev, mnode))
                if not heads:
                    heads = [mnode]
                case_tails: List[str] = []
                for c in s.cases:
                    clen = g.add("stmt", "case", c.lineno, getattr(c, "end_lineno", c.lineno))
                    g.edges.append((mnode, clen))
                    bh = visit(c.body)
                    for h in (bh or [clen]):
                        case_tails.append(h)
                j = join_node("match_join", s.lineno)
                for t in (case_tails or [mnode]):
                    g.edges.append((t, j))
                prev = j
                last = j

            # ---------- Funciones (def / async def) ----------
            elif isinstance(s, (ast.FunctionDef, getattr(ast, "AsyncFunctionDef", ()))):  # type: ignore[arg-type]
                name = getattr(s, "name", "func")
                fnode = g.add("stmt", f"def {name}()", s.lineno, getattr(s, "end_lineno", s.lineno))
                if prev:
                    g.edges.append((prev, fnode))
                if not heads:
                    heads = [fnode]
                prev = fnode
                last = fnode

            # ---------- Expresión condicional (if-expr) ----------
            elif isinstance(s, ast.Expr) and isinstance(getattr(s, "value", None), ast.IfExp):
                cond = s.value
                cur = g.add("if", f"if {ast.unparse(cond.test) if hasattr(ast,'unparse') else 'cond'}",
                            s.lineno, getattr(s, "end_lineno", s.lineno))
                if prev:
                    g.edges.append((prev, cur))
                if not heads:
                    heads = [cur]
                tb = g.add("stmt", ast.unparse(cond.body) if hasattr(ast, "unparse") else "then", s.lineno, s.lineno)
                eb = g.add("stmt", ast.unparse(cond.orelse) if hasattr(ast, "unparse") else "else", s.lineno, s.lineno)
                g.edges.append((cur, tb))
                g.edges.append((cur, eb))
                j = join_node("ifexp_join", s.lineno)
                g.edges.append((tb, j))
                g.edges.append((eb, j))
                prev = j
                last = j

            # ---------- ASYNC / AWAIT / YIELD ----------
            elif isinstance(s, ast.Expr) and isinstance(getattr(s, "value", None), ast.Await):
                lab = "await " + (ast.unparse(s.value.value) if hasattr(ast, "unparse") else "")
                cur = g.add("stmt", lab, s.lineno, getattr(s, "end_lineno", s.lineno))
                if prev:
                    g.edges.append((prev, cur))
                if not heads:
                    heads = [cur]
                prev = cur
                last = cur

            elif isinstance(s, ast.Expr) and isinstance(getattr(s, "value", None), (ast.Yield, getattr(ast, "YieldFrom", ()))):
                lab = s.value.__class__.__name__.lower()
                cur = g.add("stmt", lab, s.lineno, getattr(s, "end_lineno", s.lineno))
                if prev:
                    g.edges.append((prev, cur))
                if not heads:
                    heads = [cur]
                prev = cur
                last = cur

            # ---------- Default: statement genérico ----------
            else:
                cur = add_stmt_node(s)
                if prev:
                    g.edges.append((prev, cur))
                if not heads:
                    heads = [cur]
                prev = cur
                last = cur

        return heads or ([last] if last else [])

    entry = g.add("start", "start", 1, 1)
    heads = visit(tree.body)
    for h in (heads or [entry]):
        g.edges.append((entry, h))

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
    data = _ADAPTERS[lang](code)
    mermaid = cfg_to_mermaid(data["nodes"], data["edges"])
    return {"language": lang, "mermaid": mermaid, "nodes": data["nodes"]}
