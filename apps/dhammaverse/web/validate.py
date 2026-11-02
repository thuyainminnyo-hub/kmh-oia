import json
import re
from pathlib import Path

root = Path(__file__).resolve().parent
required = ["index.html", "offline.html", "styles.css", "app.js", "manifest.webmanifest", "sw.js"]
missing = [name for name in required if not (root / name).is_file()]
assert not missing, f"Missing files: {missing}"

html = (root / "index.html").read_text(encoding="utf-8")
js = (root / "app.js").read_text(encoding="utf-8")
manifest = json.loads((root / "manifest.webmanifest").read_text(encoding="utf-8"))
sw = (root / "sw.js").read_text(encoding="utf-8")

assert manifest["start_url"] == "./index.html"
assert manifest["display"] == "standalone"
for marker in ['id="language-toggle"', 'id="quiz-feedback"', 'id="reflection"', 'id="save-reflection"']:
    assert marker in html, f"Missing HTML element: {marker}"

html_keys = set(re.findall(r'data-i18n="([^"]+)"', html))
my_block = re.search(r'my:\s*\{(.*?)\n  \},\n  en:', js, re.S)
en_block = re.search(r'en:\s*\{(.*?)\n  \}\n\};', js, re.S)
assert my_block and en_block, "Bilingual dictionaries not found"
for label, block in [("my", my_block.group(1)), ("en", en_block.group(1))]:
    keys = set(re.findall(r'([A-Za-z][A-Za-z0-9]*):', block))
    missing_keys = html_keys - keys
    assert not missing_keys, f"{label} translation missing keys: {sorted(missing_keys)}"

for url in [
    "https://suttacentral.net/an3.65/pli/ms",
    "https://suttacentral.net/an3.65/en/sujato",
    "https://suttacentral.net/AN3.65/en/bodhi",
]:
    assert url in html, f"Missing source link: {url}"

for asset in ["./index.html", "./offline.html", "./styles.css", "./app.js", "./manifest.webmanifest"]:
    assert asset in sw, f"Service worker cache missing: {asset}"
assert 'rel="noopener noreferrer"' in html
assert 'request.mode==="navigate"' in sw, "Navigation fallback handler missing"
assert 'caches.match("./offline.html")' in sw, "Offline fallback handler missing"
assert "localStorage" in js
assert "fetch(" not in js, "Unexpected app network request added"
print("DhammaVerse structural and bilingual-content checks: PASS")
