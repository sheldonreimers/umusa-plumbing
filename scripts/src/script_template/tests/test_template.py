"""
Unit tests for the {{ ModuleName }} module.

This module validates integration logic using mocked components.
"""

import logging
import pytest

from ..config import Config
from ..handlers.api_handlers import APIHandlers
from ..handlers.data_handlers import DataHandlers
from ..processor.processorTemplate import ProcessorTemplate

logging.basicConfig(level=logging.INFO)


@pytest.fixture
def deps():
    config = Config()
    api_handlers = APIHandlers()
    data_handlers = DataHandlers(config, api_handlers)
    process_template = ProcessorTemplate(config, api_handlers, data_handlers)
    return process_template, api_handlers


def test_processor_template_smoke(deps, monkeypatch, caplog):
    process_template, api_handlers = deps
    monkeypatch.setattr(api_handlers.ServiceTemplate, 'template_method', lambda *a, **k: None)

    caplog.set_level(logging.INFO)
    process_template.process(items=[])

    errors = [r for r in caplog.records if r.levelno >= logging.ERROR]
    assert not errors, "ERROR logs were emitted during processing: " + "; ".join(
        f"{r.levelname}: {r.getMessage()}" for r in errors
    )
