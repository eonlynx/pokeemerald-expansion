#!/usr/bin/env python3
import re

with open('src/data/moves_info.h', 'r', encoding='utf-8') as f:
    t = f.read()

pattern = re.compile(r'\[MOVE_TELEPORT\]\s*=\s*\{.*?\n        \.effect = EFFECT_TCG_FORCE_SWITCH,', re.DOTALL)
replacement = """[MOVE_TELEPORT] =
    {
        .name = COMPOUND_STRING("Retreat"),
        .description = COMPOUND_STRING(
            "Switches user with a\\n"
            "benched Pokémon."),
        .effect = EFFECT_TCG_FORCE_SWITCH,"""

t = pattern.sub(replacement, t, count=1)
with open('src/data/moves_info.h', 'w', encoding='utf-8', newline='\n') as f:
    f.write(t)
print("Updated MOVE_TELEPORT!")
