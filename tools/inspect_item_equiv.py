#!/usr/bin/env python3
import re

with open('tools/generate_tcg_data.py', 'r', encoding='utf-8') as f:
    text = f.read()

m = re.search(r'item_equiv\s*=\s*\{([\s\S]*?)\}', text)
if m:
    print(m.group(0))
