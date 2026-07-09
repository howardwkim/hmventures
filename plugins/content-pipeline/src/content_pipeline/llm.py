import json, re, subprocess

DEFAULT_MODEL = "claude-sonnet-5"

def complete(prompt, *, model=DEFAULT_MODEL, timeout=180):
    r = subprocess.run(["claude", "-p", prompt, "--model", model],
                       capture_output=True, text=True, timeout=timeout)
    if r.returncode != 0:
        raise RuntimeError(f"claude -p failed: {r.stderr.strip()}")
    return r.stdout.strip()

def _extract_json(text):
    m = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.S) or \
        re.search(r"(\{.*\})", text, re.S)
    if not m:
        raise ValueError("no JSON object in reply")
    return json.loads(m.group(1))

def complete_json(prompt, *, schema_hint, model=DEFAULT_MODEL):
    full = f"{prompt}\n\nReturn ONLY a JSON object matching: {schema_hint}"
    text = complete(full, model=model)
    try:
        return _extract_json(text)
    except ValueError:
        return _extract_json(complete(full + "\n\nReturn valid JSON only.", model=model))
