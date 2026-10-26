---
name: live-help
description: Live meeting copilot. Reads the Notion AI meeting transcript that is recording right now, works out the current topic (or answers your question), and returns a short answer in ~10 seconds from a local BM25 index of your docs. Use when the user says /live-help, "what are they talking about", "help me answer this", or asks a question during a meeting.
argument-hint: "[optional question or topic]"
---

# /live-help: answer in 10 seconds

The user is in a meeting **right now**. **Target: answer within 10 seconds: at most 2 rounds of tool calls, then reply.** Brevity and speed beat completeness.

## Hard rules
- **Max 2 rounds of tool calls**; run independent calls in parallel.
- **Don't think long.** Pick the answer and write it.
- **No subagents, workflows, browser or web search** unless asked. Use the local index.
- **Reply ≤ 80 words.** No preamble, no transcript recap.
- **Not sure:** best answer plus "(unverified)". Never stall.
- **Read only:** write nothing to Notion or the user's notes.

## Setup (once, outside meetings)
- Config lives in `~/.config/live-help/` (override with `LIVE_HELP_CONFIG`). Copy files from `examples/`:
  - `sources.conf`: folders to index
  - `synonyms.conf`: extra search terms and mishearings (optional)
  - `repos.conf`: git folders to fast-forward (optional)
  - `context.md`: your private company map (optional)
- Build: `~/.claude/skills/live-help/bin/refresh.sh` (pulls repos and rebuilds) or `python3 ~/.claude/skills/live-help/bin/build_index.py`.

## Tools
- **Search** (~40 ms): `python3 ~/.claude/skills/live-help/bin/search.py "<3–6 keywords>" -n 4 -c 600`. For two topics, run two searches in the same round.
- **Context:** if `~/.config/live-help/context.md` exists, read it once per session (round 1) and answer from it first.
- **Meeting cache:** `~/.claude/skills/live-help/.current` holds `<YYYY-MM-DD> <block_id>`.

## Round 1 (parallel)
1. **Transcript:**
   - **Cache from today:** `notion-fetch {"id":"<block_id>","include_transcript":true}`.
   - **Otherwise:** `notion-query-meeting-notes` with `{"operator":"and","filters":[{"property":"created_time","filter":{"operator":"date_is","value":{"type":"relative","value":"today"}}}]}`. Take the newest result (often titled `Meeting ‣`), fetch it in round 2, and cache it with `echo "<date> <id>" > ~/.claude/skills/live-help/.current`.
2. **Question given:** also run `search.py` on its keywords.
3. `cat` the cache and context file if you haven't this session.

## Round 2 (only if needed)
- **No question:** take the last ~2,000 characters of the transcript as the current topic, then `search.py` on it.
- **Result saved to a file:** `tail -c 3000 <file>`.
- **`"truncated":true`:** fetch the last id in `unknown_block_ids`.
- **Empty transcript:** say "nothing captured yet" and answer from the index.

## Reading the transcript
- The newest speech is at the **end**. It lags 30–60 s and has no speaker labels; infer speakers from context.
- Correct obvious mishearings, using `synonyms.conf` and context.md.

## Reply format (strict)
```
**<Topic, ≤8 words>**: <direct answer, 1–2 sentences>
- <key fact>  (max 2)
**Say:** "<one sentence to say out loud>"
**Ask:** "<sharp follow-up>"   (optional)
<source path>
```
- Use plain words; spell out an uncommon acronym once.
- If someone said something wrong or risky, add `⚠️ <correction>`.
- **Repeat calls:** cover only what's new.

## Speed tips
- Run `/live-help` in a fresh, dedicated session per meeting.
- Keep `context.md` short: it's read every session.
