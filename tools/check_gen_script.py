import re

with open('tools/generate_tcg_data.py', 'r', encoding='utf-8') as f:
    text = f.read()

# Let's verify where finalize_variant is
print("finalize_variant found:", "finalize_variant" in text)
