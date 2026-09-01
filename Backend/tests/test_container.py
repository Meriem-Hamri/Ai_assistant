import subprocess
import sys

import pytest

from app import container


CACHED_GETTERS = (
    container.get_embedding_service,
    container.get_vector_store,
    container.get_document_repository,
    container.get_document_processing_dispatcher,
    container.get_conversation_repository,
    container.get_conversation_service,
    container.get_message_repository,
    container.get_message_service,
    container.get_prompt_builder,
    container.get_llm,
    container.get_metadata_extractor,
    container.get_rag_pipeline,
)


@pytest.fixture(autouse=True)
def clear_container_caches():
    for getter in CACHED_GETTERS:
        getter.cache_clear()
    yield
    for getter in CACHED_GETTERS:
        getter.cache_clear()


@pytest.mark.parametrize(
    ("getter_name", "dependency_name"),
    [
        ("get_embedding_service", "EmbeddingService"),
        ("get_vector_store", "ChromaStore"),
        ("get_document_repository", "DocumentRepository"),
        (
            "get_document_processing_dispatcher",
            "CeleryDocumentProcessingDispatcher",
        ),
        ("get_conversation_repository", "ConversationRepository"),
        ("get_message_repository", "MessageRepository"),
        ("get_prompt_builder", "PromptBuilder"),
        ("get_llm", "QwenClient"),
        ("get_metadata_extractor", "MetadataExtractor"),
    ],
)
def test_shared_getters_cache_one_instance(
    monkeypatch,
    getter_name,
    dependency_name,
):
    instances = []

    def factory(*args, **kwargs):
        instance = object()
        instances.append(instance)
        return instance

    monkeypatch.setattr(container, dependency_name, factory)
    getter = getattr(container, getter_name)

    assert getter() is getter()
    assert len(instances) == 1


def test_rag_pipeline_is_cached_and_reuses_shared_dependencies(monkeypatch):
    captured = {}
    dependencies = {
        "embedding_service": object(),
        "vector_store": object(),
        "prompt_builder": object(),
        "llm": object(),
    }

    class FakeRAGPipeline:
        def __init__(self, **kwargs):
            captured.update(kwargs)

    monkeypatch.setattr(container, "RAGPipeline", FakeRAGPipeline)
    monkeypatch.setattr(
        container,
        "get_embedding_service",
        lambda: dependencies["embedding_service"],
    )
    monkeypatch.setattr(
        container,
        "get_vector_store",
        lambda: dependencies["vector_store"],
    )
    monkeypatch.setattr(
        container,
        "get_prompt_builder",
        lambda: dependencies["prompt_builder"],
    )
    monkeypatch.setattr(container, "get_llm", lambda: dependencies["llm"])

    pipeline = container.get_rag_pipeline()

    assert pipeline is container.get_rag_pipeline()
    assert {name: captured[name] for name in dependencies} == dependencies


def test_message_service_is_cached_and_reuses_repository(monkeypatch):
    repository = object()
    captured = {}

    class FakeMessageService:
        def __init__(self, **kwargs):
            captured.update(kwargs)

    monkeypatch.setattr(container, "MessageService", FakeMessageService)
    monkeypatch.setattr(container, "get_message_repository", lambda: repository)

    service = container.get_message_service()

    assert service is container.get_message_service()
    assert captured == {"repository": repository}


def test_conversation_service_is_cached_and_reuses_repository(monkeypatch):
    repository = object()
    captured = {}

    class FakeConversationService:
        def __init__(self, **kwargs):
            captured.update(kwargs)

    monkeypatch.setattr(
        container,
        "ConversationService",
        FakeConversationService,
    )
    monkeypatch.setattr(
        container,
        "get_conversation_repository",
        lambda: repository,
    )

    service = container.get_conversation_service()

    assert service is container.get_conversation_service()
    assert captured == {"repository": repository}


def test_document_processor_factory_is_not_cached_and_reuses_dependencies(
    monkeypatch,
):
    embedding_service = object()
    vector_store = object()
    metadata_extractor = object()
    monkeypatch.setattr(
        container,
        "get_embedding_service",
        lambda: embedding_service,
    )
    monkeypatch.setattr(container, "get_vector_store", lambda: vector_store)
    monkeypatch.setattr(
        container,
        "get_metadata_extractor",
        lambda: metadata_extractor,
    )

    processor_a = container.create_document_processor()
    processor_b = container.create_document_processor()

    assert processor_a is not processor_b
    assert processor_a._indexer is not processor_b._indexer
    assert processor_a._indexer._embedding_service is embedding_service
    assert processor_b._indexer._embedding_service is embedding_service
    assert processor_a._indexer._vector_store is vector_store
    assert processor_b._indexer._vector_store is vector_store
    assert processor_a._metadata_extractor is metadata_extractor
    assert processor_b._metadata_extractor is metadata_extractor


def test_importing_api_main_does_not_construct_chroma():
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "from app import container; "
                "container.ChromaStore = lambda *args, **kwargs: "
                "(_ for _ in ()).throw(AssertionError(" 
                "'ChromaStore construit à l import')); "
                "from app.api.main import app; "
                "assert app.title == 'Assistant AI'"
            ),
        ],
        capture_output=True,
        text=True,
        timeout=30,
    )

    assert result.returncode == 0, result.stderr
