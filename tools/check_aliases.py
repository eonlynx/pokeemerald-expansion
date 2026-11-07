#!/usr/bin/env python3
with open('include/constants/tcg_cards.h', 'r', encoding='utf-8') as f:
    text = f.read()

for cand in ['CARD_PROFESSOR_OAK', 'CARD_SUPER_POTION', 'CARD_FULL_HEAL', 'CARD_GUST_OF_WIND']:
    print(cand, cand in text)
