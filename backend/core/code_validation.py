import io
import re
import token
import tokenize


_C_STYLE_COMMENTS = re.compile(r"/\*[\s\S]*?\*/|//[^\r\n]*")


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
