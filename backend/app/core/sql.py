def escape_like(term: str) -> str:
    """Escape LIKE/ILIKE wildcards so user input matches literally.

    Use with an explicit escape char::

        col.ilike(f"%{escape_like(q)}%", escape="\\\\")
    """
    return term.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
