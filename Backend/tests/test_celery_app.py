import importlib
import sys

import pytest


def test_celery_app_uses_redis_broker_without_result_backend(monkeypatch):
    redis_url = "redis://example-redis:6379/7"
    monkeypatch.setenv("REDIS_URL", redis_url)
    sys.modules.pop("app.celery_app", None)

    module = importlib.import_module("app.celery_app")

    assert module.celery_app.conf.broker_url == redis_url
    assert module.celery_app.conf.task_ignore_result is True
    assert module.celery_app.conf.result_backend is None


def test_celery_app_requires_redis_url(monkeypatch):
    monkeypatch.delenv("REDIS_URL", raising=False)
    sys.modules.pop("app.celery_app", None)

    with pytest.raises(RuntimeError, match="REDIS_URL is required"):
        importlib.import_module("app.celery_app")
