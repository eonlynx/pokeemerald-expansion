#!/usr/bin/env python3
with open('tools/moves_items_supporters_status.txt', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for l in lines[-55:]:
    print(l, end='')
