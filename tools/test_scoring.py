import re
from test_deck_refactor import test_deck_refactor
from test_cards_pipeline import test_full_pipeline

cards_list, label_to_card = test_full_pipeline()
# Let's inspect scoring
print("Testing trainer to deck scoring...")
