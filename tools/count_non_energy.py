import re

with open('poketcg2-en/src/data/cards1.asm', 'r', encoding='latin-1') as f:
    c1 = f.read()

with open('poketcg2-en/src/data/cards2.asm', 'r', encoding='latin-1') as f:
    c2 = f.read()

all_cards = re.findall(r'([A-Za-z0-9_]+)Card:', c1) + re.findall(r'([A-Za-z0-9_]+)Card:', c2)
print("Total cards in TCG2:", len(all_cards))
non_energy = [c for c in all_cards if 'Energy' not in c and not c.startswith('GrassEnergy') and not c.startswith('FireEnergy') and not c.startswith('WaterEnergy') and not c.startswith('LightningEnergy') and not c.startswith('FightingEnergy') and not c.startswith('PsychicEnergy') and not c.startswith('DoubleColorlessEnergy') and not c.startswith('RainbowEnergy') and not c.startswith('PotionEnergy') and not c.startswith('FullHealEnergy') and not c.startswith('RecycleEnergy')]
print("Non-energy cards in TCG2:", len(non_energy))
