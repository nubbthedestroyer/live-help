#!/usr/bin/env bash
# Refresh /live-help sources and rebuild the index.
# Fast-forwards every clean git repo under the folders listed in ~/.config/live-help/repos.conf
# (one folder per line), then rebuilds index.db.
set -u
CONF="${LIVE_HELP_CONFIG:-$HOME/.config/live-help}"
if [ -f "$CONF/repos.conf" ]; then
  while IFS= read -r root; do
    root=$(eval echo "$root"); [ -z "$root" ] || [ "${root#\#}" != "$root" ] && continue
    for r in "$root"/*/; do
      [ -d "$r/.git" ] || continue
      ( cd "$r"
        if [ -n "$(git status --porcelain)" ]; then echo "skip $r (local changes)"; exit 0; fi
        git pull -q --ff-only 2>/dev/null || echo "pull failed: $r" )
    done
  done < "$CONF/repos.conf"
fi
python3 "$(dirname "$0")/build_index.py"
date -u +"%Y-%m-%dT%H:%MZ" > "$(dirname "$0")/../.last_refresh"
