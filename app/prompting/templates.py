"""
Templates utilisés pour la construction des prompts RAG.
"""


CONTEXT_HEADER = "CONTEXTE"


QUESTION_HEADER = "QUESTION"


ANSWER_HEADER = "RÉPONSE"


SOURCE_TEMPLATE = """[Source {source_number}]
Document : {document_name}
Page : {page_number}

{content}
"""


PROMPT_TEMPLATE = """{system_instruction}

{context_header}

{context}

{question_header}

{question}

{answer_header}
"""