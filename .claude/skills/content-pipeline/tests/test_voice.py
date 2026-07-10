from content_pipeline import voice
from content_pipeline.learning import canon


def test_voice_doc_uses_default_seed_when_no_brand_context(conn, monkeypatch):
    monkeypatch.setattr("content_pipeline.config.brand_context", lambda: "")
    doc = voice.voice_doc(conn)
    assert voice.DEFAULT_SEED in doc
    assert "em dash" in doc.lower()  # the no-em-dash rule is part of the floor


def test_voice_doc_prefers_operator_brand_context(conn, monkeypatch):
    monkeypatch.setattr("content_pipeline.config.brand_context", lambda: "MY HOUSE VOICE")
    doc = voice.voice_doc(conn)
    assert "MY HOUSE VOICE" in doc
    assert voice.DEFAULT_SEED not in doc


def test_voice_doc_appends_learned_layer(conn, monkeypatch):
    monkeypatch.setattr("content_pipeline.config.brand_context", lambda: "SEED")
    canon.add_permanent_rule(conn, "Keep paragraphs short.", "positive", [1])
    doc = voice.voice_doc(conn)
    assert "SEED" in doc
    assert "Keep paragraphs short." in doc
