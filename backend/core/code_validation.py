import io
import re
import token
import tokenize


_C_STYLE_COMMENTS = re.compile(r"/\*[\s\S]*?\*/|//[^\r\n]*")


def normalize_code_for_comparison(code: str) -> str:
    """Normaliza diferencias visuales sin ocultar cambios reales de código."""
    normalized_lines = (
        (code or "")
        .replace("\r\n", "\n")
        .replace("\r", "\n")
        .split("\n")
    )
    return "\n".join(line.rstrip() for line in normalized_lines).strip()


def _code_signature(code: str, lang: str) -> object:
    """Representa instrucciones y estructura, ignorando comentarios y formato visual."""
    if (lang or "python").lower() == "python":
        ignored_tokens = {
            token.ENDMARKER,
            token.NEWLINE,
            token.NL,
            token.COMMENT,
            getattr(token, "ENCODING", -1),
        }
        try:
            tokens = tokenize.generate_tokens(io.StringIO(code or "").readline)
            return tuple(
                (item.type, item.string)
                for item in tokens
                if item.type not in ignored_tokens
            )
        except (IndentationError, tokenize.TokenError):
            pass

    without_comments = _C_STYLE_COMMENTS.sub("", code or "")
    if (lang or "python").lower() == "python":
        without_comments = re.sub(r"#.*$", "", without_comments, flags=re.MULTILINE)
    return normalize_code_for_comparison(without_comments)


def differs_from_initial_code(
    code: str,
    initial_code: str,
    lang: str = "python",
) -> bool:
    """Indica si cambió alguna instrucción respecto al código inicial."""
    return _code_signature(code, lang) != _code_signature(initial_code, lang)


def has_meaningful_code(code: str, lang: str = "python") -> bool:
    """Indica si hay algo distinto de espacios y comentarios en el editor."""
    if not code or not code.strip():
        return False

    if (lang or "python").lower() == "python":
        ignored_tokens = {
            token.ENDMARKER,
            token.NEWLINE,
            token.NL,
            token.INDENT,
            token.DEDENT,
            token.COMMENT,
            getattr(token, "ENCODING", -1),
        }
        try:
            tokens = tokenize.generate_tokens(io.StringIO(code).readline)
            return any(item.type not in ignored_tokens for item in tokens)
        except (IndentationError, tokenize.TokenError):
            # El código incompleto o con mala indentación sigue siendo útil para una pista.
            return True

    return bool(_C_STYLE_COMMENTS.sub("", code).strip())
