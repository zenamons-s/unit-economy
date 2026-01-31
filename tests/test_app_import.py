import importlib


def test_app_import_smoke():
    importlib.import_module("app")
