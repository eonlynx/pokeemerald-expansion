#!/usr/bin/env python3
import re

with open('include/constants/tcg_cards.h', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for l in lines[380:435]:
    print(l, end='')
