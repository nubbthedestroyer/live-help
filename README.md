# live-help

A Claude Code skill: a live meeting copilot. `/live-help [question]` reads the Notion AI meeting transcript that's recording right now, finds the current topic, and answers in about 10 seconds from a local BM25 (SQLite FTS5) index of your own docs.

Company-agnostic: everything specific to you lives in `~/.config/live-help/`, outside this repo.

## Install
```bash
git clone https://github.com/nubbthedestroyer/live-help ~/.claude/skills/live-help
mkdir -p ~/.config/live-help && cp ~/.claude/skills/live-help/examples/sources.conf.example ~/.config/live-help/sources.conf
# edit sources.conf, then:
~/.claude/skills/live-help/bin/refresh.sh
```
Requires Python 3 (with SQLite FTS5) and the Notion MCP connector (meeting notes).

## Files
- `SKILL.md`: the skill instructions (at most 2 tool rounds, replies of 80 words or less).
- `bin/build_index.py`: indexes the markdown sources listed in `sources.conf`.
- `bin/search.py`: `search.py "keywords" -n 4 -c 600`, about 40 ms per query.
- `bin/refresh.sh`: pulls the repos listed in `repos.conf`, then rebuilds the index.
- `examples/`: config templates.
