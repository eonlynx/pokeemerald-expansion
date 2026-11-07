#!/usr/bin/env python3
import sys
with open('poketcg2-en/src/data/cards1.asm', 'r', encoding='latin-1') as f:
    text = f.read()

idx = text.find('VenusaurLv67Card:')
print(text[idx:idx+800])
