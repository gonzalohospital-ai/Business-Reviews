#!/usr/bin/env python3
"""Rebuild index.html (full, internal), per-fleet files (fleet/<id>-<token>.html),
and the PROD file from data.json + template.html + chart.umd.js.
Deterministic: safe to run any time. Tokens are stable (raw_fo/fleet_tokens.json)
so shared per-fleet links never change.
Usage:  python3 raw_fo/rebuild_publish.py
Run from the "Business reviews" project root.
"""
import json, os, secrets, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)

data = json.load(open("data.json"))
tpl = open("template.html").read()
chartjs = open("chart.umd.js").read()

tokpath = "raw_fo/fleet_tokens.json"
tokens = json.load(open(tokpath)) if os.path.exists(tokpath) else {}
for f in data["fleets"]:
    k = str(f["id"])
    if k not in tokens:
        tokens[k] = secrets.token_hex(8)
json.dump(tokens, open(tokpath, "w"))

MARK = '<script>/*__CHARTJS__*/</script>'
def build(dj, cfg):
    h = tpl.replace(MARK, MARK + '\n<script>' + cfg + '</script>')
    return h.replace('/*__CHARTJS__*/', chartjs).replace('/*__DATA__*/', dj)

dj_full = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
full_cfg = 'window.FLEET_TOKENS=' + json.dumps({int(k): v for k, v in tokens.items()}) + ';'
open("index.html", "w").write(build(dj_full, full_cfg))
open("Bolt_BusinessReview_Flota_Madrid_PROD.html", "w").write(build(dj_full, ''))

os.makedirs("fleet", exist_ok=True)
for fn in os.listdir("fleet"):
    if fn.endswith(".html"):
        os.remove("fleet/" + fn)
n = 0
manifest = []
for f in data["fleets"]:
    if not f.get("cars") and not f.get("drivers"):
        continue
    sub = {k: v for k, v in data.items() if k != "fleets"}
    sub["fleets"] = [f]
    fn = f"fleet/{f['id']}-{tokens[str(f['id'])]}.html"
    open(fn, "w").write(build(json.dumps(sub, ensure_ascii=False, separators=(",", ":")),
                              f'window.LOCK_FLEET={f["id"]};'))
    manifest.append({"fo": f["id"], "name": f["name"], "file": fn, "token": tokens[str(f["id"])]})
    n += 1
json.dump(manifest, open("fleet/_manifest.json", "w"), ensure_ascii=False, indent=1)
print(f"OK: index.html + PROD + {n} per-fleet files. weeks={data.get('weeks')}")
