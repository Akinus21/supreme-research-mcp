from utils.logger import local as log
from utils.transform.case import sentence as sentence_case
from utils.transform.case import title as title_case

async def apa(data: dict) -> str:
    """
    Format a reference in APA 7th edition style.

    Automatically converts the title to sentence case if needed,
    fills in missing fields with defaults, and returns a properly formatted citation string.

    Args:
        data (dict): Reference details, e.g.:
            - author (str)
            - year (int or str)
            - title (str)
            - source (str)  # journal, website, etc.
            - publisher (str)
            - url (str)

    Returns:
        str: Formatted APA 7 citation.
    """
    author = data.get("author", "Unknown Author")
    year = str(data.get("year", "n.d."))
    raw_title = data.get("title", "Untitled")
    
    try:
        # Convert to sentence case only if needed
        if raw_title and raw_title != sentence_case(raw_title):
            title = sentence_case(raw_title)
        else:
            title = raw_title
    except Exception as e:
        log("error", "academic.references.apa", f"Error formatting title: {e}")
        title = raw_title

    source = data.get("source", "")
    publisher = data.get("publisher", "")
    url = data.get("url", "")

    for field in ["author", "year", "title"]:
        if not data.get(field):
            log("warning", f"Missing '{field}' for APA reference.", "academic.references.apa")

    apa_ref = f"{author} ({year}). {title}."
    if source:
        apa_ref += f" {source}."
    if publisher:
        apa_ref += f" {publisher}."
    if url:
        apa_ref += f" {url}"

    log("info", f"Generated APA reference: {apa_ref}", "academic.references.apa")
    return apa_ref


def mla(data: dict) -> str:
    """
    Format a reference in MLA 9th edition style.

    Automatically converts the title to title case if needed,
    fills in missing fields with defaults, and returns a properly formatted citation string.

    Args:
        data (dict): Reference details, e.g.:
            - author (str)
            - title (str)
            - container (str)  # journal, book, website
            - publisher (str)
            - year (int or str)
            - url (str)

    Returns:
        str: Formatted MLA 9 citation.
    """
    author = data.get("author", "Unknown Author")
    raw_title = data.get("title", "Untitled")
    # Convert to title case only if needed
    if raw_title and raw_title != title_case(raw_title):
        title = title_case(raw_title)
    else:
        title = raw_title

    container = data.get("container", "")
    publisher = data.get("publisher", "")
    year = str(data.get("year", "n.d."))
    url = data.get("url", "")

    for field in ["author", "title", "year"]:
        if not data.get(field):
            log("warning", f"Missing '{field}' for MLA reference.", "academic.references.mla")

    mla_ref = f"{author}. \"{title}.\""
    if container:
        mla_ref += f" {container},"
    if publisher:
        mla_ref += f" {publisher},"
    mla_ref += f" {year}."
    if url:
        mla_ref += f" {url}"

    log("info", f"Generated MLA reference: {mla_ref}", "academic.references.mla")
    return mla_ref
