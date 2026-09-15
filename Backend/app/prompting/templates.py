"""
Templates utilisés pour la construction des prompts RAG.
"""


HISTORY_HEADER = "HISTORIQUE RÉCENT"


CONTEXT_HEADER = "CONTEXTE DOCUMENTAIRE"


QUESTION_HEADER = "QUESTION"


ANSWER_HEADER = "RÉPONSE"


SOURCE_TEMPLATE = """[SOURCE_{source_number}]
Nom du fichier : {document_name}
Page : {page_number}
Contenu du passage :

{content}
"""


PROMPT_TEMPLATE = """{system_instruction}

{history_header}

{history}

{context_header}

{context}

{question_header}

{question}

{numeric_fidelity_instruction}

{answer_header}
"""
