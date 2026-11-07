#!/usr/bin/env python3
with open('tools/moves_items_supporters_status.txt', 'r', encoding='utf-8') as f:
    for i in range(25):
        print(f.readline(), end='')
