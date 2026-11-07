#!/usr/bin/env python3
"""
Inspect and remove dangling #else ... #endif blocks in src/data/moves_info.h
"""
with open('src/data/moves_info.h', 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_lines = []
i = 0
removed_count = 0
while i < len(lines):
    line = lines[i]
    s = line.strip()
    if s.startswith('#else') and i > 0 and lines[i-1].strip().endswith('),'):
        # This #else directly follows a closed .description = COMPOUND_STRING(...),
        # Collect until #endif
        start = i
        while i < len(lines) and not lines[i].strip().startswith('#endif'):
            i += 1
        # Skip the #endif too
        if i < len(lines):
            i += 1
        removed_count += 1
        print(f"Removed dangling block at lines {start+1}-{i}")
        continue
    new_lines.append(line)
    i += 1

with open('src/data/moves_info.h', 'w', encoding='utf-8', newline='\n') as f:
    f.writelines(new_lines)

print(f"Removed {removed_count} dangling #else/#endif blocks.")
