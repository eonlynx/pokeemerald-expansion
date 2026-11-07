#!/usr/bin/env python3
with open('tools/generate_tcg_data.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()
for i in range(180, 205):
    print(f"{i+1}: {lines[i]}", end="")
