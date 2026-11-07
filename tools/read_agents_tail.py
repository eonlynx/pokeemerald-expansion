#!/usr/bin/env python3
with open('AGENTS.md', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for l in lines[-45:]:
    print(l, end='')
