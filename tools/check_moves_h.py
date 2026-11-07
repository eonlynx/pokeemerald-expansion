#!/usr/bin/env python3
with open('include/constants/moves.h', 'r', encoding='utf-8') as f:
    for i in range(35):
        print(f.readline(), end='')
