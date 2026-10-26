#!/usr/bin/env python3
"""Build the /live-help search index (SQLite FTS5, BM25) from your local docs.

Re-run any time your sources change:  python3 ~/.claude/skills/live-help/bin/build_index.py
"""
import os, re, sqlite3, sys, time

HOME = os.path.expanduser("~")
DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "index.db")

# (root, label, extensions)
CONF_DIR = os.environ.get("LIVE_HELP_CONFIG", os.path.expanduser("~/.config/live-help"))


def load_sources():
    """sources.conf: one source per line: <path> | <label> [| ext1,ext2]. Lines starting with # are ignored.
    A path ending in /* adds every git repo directly under that folder, labelled repo:<name>."""
    out = []
    conf = os.path.join(CONF_DIR, "sources.conf")
    if not os.path.exists(conf):
        print(f"no {conf}; copy sources.conf.example there"); return out
    for line in open(conf):
        line = line.strip()
        if not line or line.startswith("#"): continue
        parts = [x.strip() for x in line.split("|")]
        path = os.path.expanduser(os.path.expandvars(parts[0]))
        label = parts[1] if len(parts) > 1 else os.path.basename(path.rstrip("/*"))
        exts = tuple(parts[2].split(",")) if len(parts) > 2 else (".md", ".mdx")
        if path.endswith("/*"):
            root = path[:-2]
            for r in sorted(os.listdir(root)) if os.path.isdir(root) else []:
                if os.path.isdir(os.path.join(root, r, ".git")):
                    out.append((os.path.join(root, r), f"repo:{r}", exts))
        else:
            out.append((path, label, exts))
    return out


SOURCES = load_sources()
SKIP_DIRS = {".git", ".tools", "node_modules", ".next", "dist", "build", "vendor", ".claude"}
MAX_CHUNK = 1500
MAX_FILE = 400_000

HEAD = re.compile(r"^(#{1,4})\s+(.+)$")


def chunks(text):
    """Split markdown by headings; keep the heading path; cap chunk size."""
    path, buf, out = [], [], []

    def flush():
        body = "\n".join(buf).strip()
        if len(body) > 40:
            for i in range(0, len(body), MAX_CHUNK):
                out.append((" > ".join(path), body[i:i + MAX_CHUNK]))
        buf.clear()

    for line in text.splitlines():
        m = HEAD.match(line)
        if m:
            flush()
            lvl = len(m.group(1))
            path[:] = path[:lvl - 1] + [m.group(2).strip()]
        else:
            buf.append(line)
    flush()
    return out


def title_of(text, fp):
    m = re.search(r'^title:\s*"?(.+?)"?\s*$', text[:600], re.M) or re.search(r"^#\s+(.+)$", text, re.M)
    return m.group(1).strip() if m else os.path.splitext(os.path.basename(fp))[0]


def main():
    t0 = time.time()
    if os.path.exists(DB):
        os.remove(DB)
    db = sqlite3.connect(DB)
    db.execute("CREATE VIRTUAL TABLE docs USING fts5(title, heading, body, path UNINDEXED, src UNINDEXED, tokenize='porter unicode61')")
    n_files = n_chunks = 0
    for root, label, exts in SOURCES:
        if not os.path.isdir(root):
            continue
        for d, dirs, files in os.walk(root):
            dirs[:] = [x for x in dirs if x not in SKIP_DIRS]
            for f in files:
                if not f.endswith(exts):
                    continue
                fp = os.path.join(d, f)
                try:
                    if os.path.getsize(fp) > MAX_FILE:
                        continue
                    text = open(fp, encoding="utf-8", errors="ignore").read()
                except OSError:
                    continue
                title = title_of(text, fp)
                rows = [(title, h, b, fp, label) for h, b in chunks(text)]
                db.executemany("INSERT INTO docs VALUES (?,?,?,?,?)", rows)
                n_files += 1
                n_chunks += len(rows)
    db.execute("INSERT INTO docs(docs) VALUES('optimize')")
    db.commit()
    print(f"indexed {n_files} files, {n_chunks} chunks in {time.time()-t0:.1f}s -> {os.path.abspath(DB)}")


if __name__ == "__main__":
    sys.exit(main())
