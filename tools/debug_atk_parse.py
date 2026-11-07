#!/usr/bin/env python3
import sys
sys.stdout.reconfigure(encoding='utf-8')
import glob, re, os

texts = {}
for p in glob.glob('poketcg2-en/src/text/**/*.asm', recursive=True) + glob.glob('poketcg/src/text/**/*.asm', recursive=True):
    with open(p, 'r', encoding='latin-1') as f:
        content = f.read()
    blocks = re.findall(r'([A-Za-z0-9_]+):([\s\S]*?)(?=\ndone|\n[A-Za-z0-9_]+:|\Z)', content)
    for label, body in blocks:
        lines = []
        for m in re.finditer(r'(?:text|line)\s+"([^"]*)"', body):
            lines.append(m.group(1))
        if lines and label not in texts:
            texts[label] = " ".join(lines)

with open('poketcg2-en/src/data/cards1.asm', 'r', encoding='latin-1') as f:
    content = f.read()

cards = re.split(r'\n(?=[A-Za-z0-9_]+Card:)', content)
for c in cards[:5]:
    lines = c.splitlines()
    if not lines: continue
    print("--- CARD ---", lines[0])
    for l in lines:
        if 'attack' in l.lower() or 'tx ' in l or 'damage' in l:
            print("  ", l)
