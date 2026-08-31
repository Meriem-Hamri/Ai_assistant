from app.vectorstore.search_result import SearchResult

from app.prompting.templates import SOURCE_TEMPLATE


def format_search_result(
    result: SearchResult,
    source_number: int,
    include_metadata: bool = True,
) -> str:
    """
    Transforme un résultat de recherche en texte lisible
    pour le Prompt Builder.

    Args:
        result: Résultat retourné par le Vector Store.
        source_number: Numéro de la source dans le prompt.
        include_metadata: Indique si les métadonnées doivent
            être incluses.

    Returns:
        Représentation textuelle du résultat.
    """

    if include_metadata:
        return SOURCE_TEMPLATE.format(
            source_number=source_number,
            document_name=result.document_name,
            page_number=result.page_number,
            content=result.text,
        )

    return (
        f"[SOURCE_{source_number}]\n"
        f"{result.text}\n"
    )


def build_context(
    results: list[SearchResult],
    max_results: int,
    max_context_length: int,
    include_metadata: bool = True,
) -> str:
    """
    Construit le contexte à partir des résultats de recherche.

    Les résultats sont conservés dans l'ordre fourni
    par le Vector Store.

    Args:
        results: Résultats de la recherche vectorielle.
        max_results: Nombre maximal de résultats à utiliser.
        max_context_length: Taille maximale du contexte.
        include_metadata: Inclure ou non les métadonnées.

    Returns:
        Contexte textuel destiné au LLM.
    """

    if not results:
        return "Aucun passage pertinent n'a été trouvé."

    formatted_sources = []

    for index, result in enumerate(
        results[:max_results],
        start=1,
    ):
        formatted_sources.append(
            format_search_result(
                result=result,
                source_number=index,
                include_metadata=include_metadata,
            )
        )

    context = "\n".join(formatted_sources)

    if len(context) > max_context_length:
        context = context[:max_context_length]

    return context
