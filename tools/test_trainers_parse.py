import re
from collections import Counter, defaultdict

# Test deck restructuring and complementary deck synthesis
with open('src/data/trainers_frlg.party', 'r', encoding='latin-1') as f:
    frlg_party = f.read()

trainers = re.split(r'===\s*(TRAINER_[A-Z0-9_]+)\s*===', frlg_party)
print(f"Total blocks in trainers_frlg.party: {len(trainers)}")

parsed_trainers = {}
for i in range(1, len(trainers), 2):
    t_id = trainers[i]
    t_body = trainers[i+1]
    
    # Extract species
    species_found = []
    lines = t_body.splitlines()
    for l in lines:
        l_str = l.strip()
        if l_str and not any(l_str.startswith(x) for x in ['Name:', 'Class:', 'Pic:', 'Gender:', 'Music:', 'Double Battle:', 'AI:', 'Level:', 'IVs:', 'EVs:', 'Moves:', 'Ability:', 'Item:', 'Ball:', 'Nature:', 'Shiny:']):
            # likely species
            species_found.append(l_str.replace(' ', '_').upper())
    parsed_trainers[t_id] = species_found

print(f"Parsed {len(parsed_trainers)} trainers from party file.")
sample_keys = list(parsed_trainers.keys())[:5]
for k in sample_keys:
    print(k, parsed_trainers[k])
