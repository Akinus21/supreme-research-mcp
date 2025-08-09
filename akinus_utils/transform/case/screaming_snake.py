from akinus_utils.case.upper_snake import upper_snake
from akinus_utils.logger import log

def screaming_snake(text: str) -> str:
    """
    Alias for UPPER_SNAKE_CASE (screaming snake case).

    Args:
        text (str): Input string.

    Returns:
        str: Screaming snake case (all uppercase with underscores).
    """
    result = upper_snake(text)
    log("info", "case.screaming_snake", f"'{text}' -> '{result}'")
    return result
