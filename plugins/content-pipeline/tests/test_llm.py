from content_pipeline import llm

def test_complete_invokes_claude_p(monkeypatch):
    calls = {}
    def fake_run(cmd, **kw):
        calls["cmd"] = cmd
        class R: stdout = "hello"; returncode = 0; stderr = ""
        return R()
    monkeypatch.setattr(llm.subprocess, "run", fake_run)
    out = llm.complete("hi", model="claude-sonnet-5")
    assert out == "hello"
    assert "claude" in calls["cmd"][0] and "-p" in calls["cmd"]
    assert "--model" in calls["cmd"] and "claude-sonnet-5" in calls["cmd"]

def test_complete_json_extracts_object(monkeypatch):
    monkeypatch.setattr(llm, "complete", lambda *a, **k: 'noise ```json\n{"ok": true}\n``` tail')
    assert llm.complete_json("x", schema_hint="{}")["ok"] is True
