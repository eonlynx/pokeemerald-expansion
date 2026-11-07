#!/usr/bin/env python3
import re

REPLACEMENTS = {
    'MOVE_GROWL': [
        "Lowers the target's",
        "Attack stage.",
    ],
    'MOVE_MINIMIZE': [
        "Raises user's Evasion",
        "stage drastically.",
    ],
    'MOVE_LIGHT_SCREEN': [
        "Reduces damage taken",
        "from Special attacks.",
    ],
    'MOVE_SUPER_FANG': [
        "Halves the target's",
        "current HP.",
    ],
    'MOVE_CURSE': [
        "Sacrifices user HP to",
        "curse the target.",
    ],
    'MOVE_CONVERSION_2': [
        "Changes user type to",
        "resist last attack.",
    ],
    'MOVE_ZAP_CANNON': [
        "Deals damage and",
        "inflicts Paralysis.",
    ],
    'MOVE_FRUSTRATION': [
        "Deals physical damage",
        "to the target.",
    ],
    'MOVE_SAFEGUARD': [
        "Protects party from",
        "status conditions.",
    ],
    'MOVE_BATON_PASS': [
        "Switches out while",
        "passing stat boosts.",
    ],
    'MOVE_BEAT_UP': [
        "Attacks the target",
        "with all party allies.",
    ],
    'MOVE_SUPERPOWER': [
        "Deals heavy damage but",
        "lowers user stats.",
    ],
    'MOVE_ICE_BALL': [
        "Hits 5 turns with",
        "increasing power.",
    ],
    'MOVE_BULLET_SEED': [
        "Shoots 2 to 5 seeds",
        "at the target.",
    ],
    'MOVE_FRENZY_PLANT': [
        "Deals heavy damage",
        "requiring recharge.",
    ],
    'MOVE_ROCK_BLAST': [
        "Hurls 2 to 5 rocks",
        "at the target.",
    ],
}

def update_moves():
    for k, lines in REPLACEMENTS.items():
        assert len(lines) <= 2, f"{k} > 2 lines"
        for l in lines:
            assert len(l) <= 32, f"{k} line > 32: '{l}' ({len(l)})"

    with open('src/data/moves_info.h', 'r', encoding='utf-8') as f:
        content = f.read()

    for m_const, lines in REPLACEMENTS.items():
        # Match move entry description
        pattern = re.compile(
            r'(\[' + re.escape(m_const) + r'\]\s*=\s*\{.*?\.description\s*=\s*COMPOUND_STRING\()(.*?)(\),)',
            re.DOTALL
        )
        match = pattern.search(content)
        if match:
            formatted = f'\n            "{lines[0]}\\n"\n            "{lines[1]}"'
            replacement = match.group(1) + formatted + match.group(3)
            content = content[:match.start()] + replacement + content[match.end():]
            print(f"Updated {m_const}")
        else:
            print(f"Could not find {m_const}")

    with open('src/data/moves_info.h', 'w', encoding='utf-8', newline='\n') as f:
        f.write(content)
    print("All placeholder move descriptions successfully replaced!")

if __name__ == '__main__':
    update_moves()
