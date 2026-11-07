#!/usr/bin/env python3
import glob

files = glob.glob('poketcg2-en/src/text/**/*.asm', recursive=True) + glob.glob('poketcg/src/text/**/*.asm', recursive=True)
print("Files found:", len(files))
if files:
    with open(files[0], 'r', encoding='latin-1') as f:
        print(f"Sample from {files[0]}:")
        for i in range(25):
            print(f.readline(), end='')
