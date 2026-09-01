import sys
from types import ModuleType
from unittest.mock import Mock

from app.documents.celery_dispatcher import CeleryDocumentProcessingDispatcher


def test_celery_dispatcher_sends_only_document_id(monkeypatch):
    task = Mock()
    fake_module = ModuleType("app.tasks.documents")
    fake_module.process_document = task
    monkeypatch.setitem(sys.modules, "app.tasks.documents", fake_module)

    CeleryDocumentProcessingDispatcher().enqueue("document-id")

    task.delay.assert_called_once_with("document-id")
