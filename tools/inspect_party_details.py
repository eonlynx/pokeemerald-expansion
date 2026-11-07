import re
from test_cards_pipeline import test_full_pipeline

# 1. Parse trainers_frlg.party
with open('src/data/trainers_frlg.party', 'r', encoding='latin-1') as f:
    frlg_party = f.read()

trainers_blocks = re.split(r'===\s*(TRAINER_[A-Z0-9_]+)\s*===', frlg_party)
trainer_data = {}
for i in range(1, len(trainers_blocks), 2):
    t_id = trainers_blocks[i]
    t_body = trainers_blocks[i+1]
    
    t_class = ""
    m_class = re.search(r'Class:\s*([^\n\r]+)', t_body)
    if m_class: t_class = m_class.group(1).strip()
    
    species_found = []
    for l in t_body.splitlines():
        l_str = l.strip()
        if l_str and not any(l_str.startswith(x) for x in ['Name:', 'Class:', 'Pic:', 'Gender:', 'Music:', 'Double Battle:', 'AI:', 'Level:', 'IVs:', 'EVs:', 'Moves:', 'Ability:', 'Item:', 'Ball:', 'Nature:', 'Shiny:']):
            species_found.append(l_str.replace(' ', '_').upper())
            
    trainer_data[t_id] = {
        'class': t_class,
        'species': species_found
    }

print(f"Total parsed trainers: {len(trainer_data)}")
print("Sample Ben:", trainer_data.get('TRAINER_YOUNGSTER_BEN'))
print("Sample Brock:", trainer_data.get('TRAINER_LEADER_BROCK'))
