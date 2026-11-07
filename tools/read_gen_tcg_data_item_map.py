#!/usr/bin/env python3
with open('tools/generate_tcg_data.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i in range(165, 185):
    print(f"{i+1}: {lines[i]}", end="")
print("---")
for i in range(350, 395):
    if i < len(lines):
        print(f"{i+1}: {lines[i]}", end="")
