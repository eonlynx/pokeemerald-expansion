#!/usr/bin/env python3
import re

moves_set = set()
with open('include/constants/moves.h', 'r', encoding='utf-8') as f:
    for line in f:
        m = re.search(r'\b(MOVE_[A-Z0-9_]+)\b', line)
        if m:
            moves_set.add(m.group(1))

print(f"Total moves extracted: {len(moves_set)}")
print(sorted(list(moves_set))[:20])
