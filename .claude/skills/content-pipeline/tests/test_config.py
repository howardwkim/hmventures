import json
from content_pipeline import config


def test_brand_context_missing_file_returns_empty(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "CONFIG_PATH", tmp_path / "nope.json")
    assert config.brand_context() == ""


def test_brand_context_reads_file(tmp_path, monkeypatch):
    p = tmp_path / "config.json"
    p.write_text(json.dumps({"brand_context": "MiHO: plainspoken, no hype"}))
    monkeypatch.setattr(config, "CONFIG_PATH", p)
    assert config.brand_context() == "MiHO: plainspoken, no hype"


def test_load_malformed_file_returns_empty(tmp_path, monkeypatch):
    p = tmp_path / "config.json"
    p.write_text("{not valid json")
    monkeypatch.setattr(config, "CONFIG_PATH", p)
    assert config.load() == {}
    assert config.brand_context() == ""
