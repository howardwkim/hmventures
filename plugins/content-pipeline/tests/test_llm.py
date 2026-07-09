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

def test_complete_json_retries_once_on_bad_first_reply(monkeypatch):
    calls = []
    def fake_complete(prompt, *, model=llm.DEFAULT_MODEL):
        calls.append(prompt)
        if len(calls) == 1:
            return "sorry, here's some prose with no json object at all"
        return 'noise ```json\n{"ok": true, "attempt": 2}\n``` tail'
    monkeypatch.setattr(llm, "complete", fake_complete)
    result = llm.complete_json("x", schema_hint="{}")
    assert result == {"ok": True, "attempt": 2}
    assert len(calls) == 2
    assert "Return valid JSON only." in calls[1]
    assert "Return valid JSON only." not in calls[0]
