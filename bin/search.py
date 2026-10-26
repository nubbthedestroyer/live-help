#!/usr/bin/env python3
"""Fast BM25 search over the /live-help index.

Usage: search.py "free text query" [-n 5] [-c 700]
Prints the top chunks: [src] title > heading (path) followed by an excerpt.
"""
import os, re, sqlite3, sys

DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "index.db")

STOP = set("""a an and are as at be but by can do does for from how i if in into is it its of on or our
so that the their them then there these they this to us was we what when where which who why will with
you your about should would could just like get got have has had need want know tell me any all""".split())

# Optional synonyms / mishearings: ~/.config/live-help/synonyms.conf, lines "term: alt1, alt2"
SYN = {}
_syn = os.path.join(os.environ.get("LIVE_HELP_CONFIG", os.path.expanduser("~/.config/live-help")), "synonyms.conf")
if os.path.exists(_syn):
    for _l in open(_syn):
        if ":" in _l and not _l.lstrip().startswith("#"):
            k, v = _l.split(":", 1)
            SYN[k.strip().lower()] = [k.strip().lower()] + [x.strip().lower() for x in v.split(",") if x.strip()]


def fts_query(q):
    words = [w for w in re.findall(r"[a-z0-9][a-z0-9\-]*", q.lower()) if w not in STOP and len(w) > 1]
    terms = []
    for w in words:
        for t in SYN.get(w, [w]):
            t = t.replace("-", " ")
            terms.append(f'"{t}"' if " " in t else f'"{t}"*' if len(t) > 3 else f'"{t}"')
    return " OR ".join(dict.fromkeys(terms))


def main():
    args = sys.argv[1:]
    n, c = 5, 700
    if "-n" in args:
        i = args.index("-n"); n = int(args[i + 1]); del args[i:i + 2]
    if "-c" in args:
        i = args.index("-c"); c = int(args[i + 1]); del args[i:i + 2]
    q = fts_query(" ".join(args))
    if not q:
        print("empty query"); return
    if not os.path.exists(DB):
        print("index missing: run build_index.py"); return
    db = sqlite3.connect(DB)
    rows = db.execute(
        "SELECT src, title, heading, path, body FROM docs WHERE docs MATCH ? "
        "ORDER BY bm25(docs, 8.0, 4.0, 1.0) LIMIT ?", (q, n)).fetchall()
    if not rows:
        print("no hits for:", q); return
    home = os.path.expanduser("~")
    for src, title, heading, path, body in rows:
        if heading.startswith(title):
            heading = heading[len(title):].lstrip(" >")
        body = re.sub(r"\n{2,}", "\n", body).strip()
        print(f"## [{src}] {title}{' > ' + heading if heading else ''}\n({path.replace(home, '~')})\n{body[:c]}\n")


if __name__ == "__main__":
    main()
