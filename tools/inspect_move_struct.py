#!/usr/bin/env python3
import re

with open('src/data/moves_info.h', 'r', encoding='utf-8') as f:
    text = f.read()

m = re.search(r'\[MOVE_POUND\]\s*=\s*\{([\s\S]*?)\},', text)
if m:
    print(m.group(0))
