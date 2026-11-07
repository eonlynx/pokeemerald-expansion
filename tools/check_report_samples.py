#!/usr/bin/env python3
print("=== SAMPLE: vanilla_vs_tcg_items.txt ===")
with open('tools/vanilla_vs_tcg_items.txt', 'r', encoding='utf-8') as f:
    for i in range(25):
        print(f.readline(), end='')

print("\n=== SAMPLE: tcg_moves_mechanics_check.txt ===")
with open('tools/tcg_moves_mechanics_check.txt', 'r', encoding='utf-8') as f:
    for i in range(35):
        print(f.readline(), end='')
