#include "global.h"
#include "tcg.h"
#include "item.h"
#include "pokemon.h"
#include "data.h"
#include "battle.h"
#include "battle_setup.h"
#include "random.h"
#include "event_data.h"
#include "pokemon_storage_system.h"
#include "string_util.h"
#include "constants/items.h"
#include "constants/species.h"
#include "constants/moves.h"
#include "constants/tcg_cards.h"
#include "constants/battle.h"
#include "constants/trainers.h"
#include "constants/flags.h"
#include "constants/opponents.h"
#include "constants/characters.h"

#include "data/tcg_cards.h"
#include "data/tcg_decks.h"
#include "data/trainer_tcg_decks.h"

struct TcgBattleState gTcgBattleState;

const struct TcgCardInfo *GetTcgCardInfo(u16 cardId)
{
    if (cardId == 0 || cardId > gTcgCardCount)
        return NULL;
    return &gTcgCards[cardId];
}

u16 GetMonCardId(const struct Pokemon *mon)
{
    return (u16)(GetMonData((struct Pokemon *)mon, MON_DATA_EXP) & 0xFFFF);
}

void SetMonCardId(struct Pokemon *mon, u16 cardId)
{
    u32 val = cardId;
    SetMonData(mon, MON_DATA_EXP, &val);
}

void CreateTempMonFromCardId(struct Pokemon *mon, u16 cardId)
{
    const struct TcgCardInfo *info = GetTcgCardInfo(cardId);
    ZeroMonData(mon);
    if (!info)
        return;

    u16 species;
    if (info->cardType == CARD_TYPE_TRAINER_ITEM || info->cardType == CARD_TYPE_TRAINER_SUPPORTER)
        species = SPECIES_UNOWN;
    else
        species = info->species != SPECIES_NONE ? info->species : SPECIES_BULBASAUR;

    CreateMon(mon, species, 1, 0, (struct OriginalTrainerId){0});

    u8 nickname[POKEMON_NAME_LENGTH + 1];
    StringCopyN(nickname, info->name, POKEMON_NAME_LENGTH);
    nickname[POKEMON_NAME_LENGTH] = EOS;
    SetMonData(mon, MON_DATA_NICKNAME, nickname);

    u16 hp = info->maxHp > 0 ? info->maxHp : 50;
    SetMonData(mon, MON_DATA_MAX_HP, &hp);
    SetMonData(mon, MON_DATA_HP, &hp);
    SetMonCardId(mon, cardId);

    if (info->isRareShiny)
    {
        bool32 isShiny = TRUE;
        SetMonData(mon, MON_DATA_IS_SHINY, &isShiny);
    }

    if (info->cardType == CARD_TYPE_TRAINER_ITEM || info->cardType == CARD_TYPE_TRAINER_SUPPORTER)
    {
        u16 none = MOVE_NONE;
        SetMonData(mon, MON_DATA_MOVE1, &none);
        SetMonData(mon, MON_DATA_MOVE2, &none);
        SetMonData(mon, MON_DATA_MOVE3, &none);
        SetMonData(mon, MON_DATA_MOVE4, &none);
        return;
    }

    // Populate combat moves from TCG Card
    u16 m1 = MOVE_NONE;
    u16 m2 = MOVE_NONE;
    u16 m3 = MOVE_NONE;
    u16 m4 = MOVE_RETREAT;
    if (info->pokemonPowerId != 0)
    {
        // Pokémon Power occupies Slot 1 (MOVE_HELPING_HAND marker)
        m1 = MOVE_HELPING_HAND;
        m2 = info->move1 != MOVE_NONE ? info->move1 : MOVE_TACKLE;
        m3 = info->move2;
    }
    else
    {
        m1 = info->move1 != MOVE_NONE ? info->move1 : MOVE_TACKLE;
        m2 = info->move2;
        m3 = MOVE_NONE;
    }

    SetMonData(mon, MON_DATA_MOVE1, &m1);
    SetMonData(mon, MON_DATA_MOVE2, &m2);
    SetMonData(mon, MON_DATA_MOVE3, &m3);
    SetMonData(mon, MON_DATA_MOVE4, &m4);

    u8 maxPp = 99;
    SetMonData(mon, MON_DATA_PP1, &maxPp);
    SetMonData(mon, MON_DATA_PP2, &maxPp);
    SetMonData(mon, MON_DATA_PP3, &maxPp);
    SetMonData(mon, MON_DATA_PP4, &maxPp);
}

u16 GetCardIdFromItemId(u16 itemId)
{
    if (itemId == ITEM_NONE)
        return 0;

    switch (itemId)
    {
    case ITEM_POKE_DOLL:
        return CARD_CLEFAIRY_DOLL;
    case ITEM_ESCAPE_ROPE:
        return CARD_SWITCH;
    case ITEM_ITEMFINDER:
        return CARD_ITEM_FINDER;
    case ITEM_X_ATTACK:
        return CARD_PLUSPOWER;
    case ITEM_X_DEFEND:
    case ITEM_GUARD_SPEC:
        return CARD_DEFENDER;
    case ITEM_HELIX_FOSSIL:
    case ITEM_DOME_FOSSIL:
    case ITEM_OLD_AMBER:
        return CARD_MYSTERIOUS_FOSSIL;
    case ITEM_MAX_POTION:
    case ITEM_FULL_RESTORE:
        return CARD_POKEMON_CENTER;
    case ITEM_HYPER_POTION:
    case ITEM_ENERGY_ROOT:
        return CARD_SUPER_POTION;
    case ITEM_ENERGYPOWDER:
        return CARD_POTION;
    case ITEM_HEAL_POWDER:
        return CARD_FULL_HEAL;
    case ITEM_REVIVAL_HERB:
        return CARD_REVIVE;
    case ITEM_MAX_REVIVE:
        return CARD_MAX_REVIVE;
    case ITEM_ETHER:
    case ITEM_MAX_ETHER:
        return CARD_RECYCLE;
    case ITEM_ELIXIR:
    case ITEM_MAX_ELIXIR:
        return CARD_NIGHTLY_GARBAGE_RUN;
    }

    for (u16 i = 1; i <= gTcgCardCount; i++)
    {
        if (gTcgCards[i].equivItemId == itemId)
            return i;
    }
    return 0;
}

u16 GetCardQuantityInBag(u16 cardId)
{
    const struct TcgCardInfo *info = GetTcgCardInfo(cardId);
    if (!info)
        return 0;

    u8 pocketId = POCKET_TCG_POKEMON;
    if (info->cardType == CARD_TYPE_TRAINER_ITEM)
        pocketId = POCKET_TCG_ITEMS;
    else if (info->cardType == CARD_TYPE_TRAINER_SUPPORTER)
        pocketId = POCKET_TCG_SUPPORTERS;

    struct BagPocket *pocket = &gBagPockets[pocketId];
    u16 total = 0;
    for (u32 i = 0; i < pocket->capacity; i++)
    {
        struct ItemSlot slot = BagPocket_GetSlotData(pocket, i);
        if (slot.itemId == (enum Item)cardId)
            total += slot.quantity;
    }
    return total;
}

u16 CountCardIdInDeck(const struct TcgDeck *deck, u16 cardId)
{
    if (!deck || cardId == 0)
        return 0;

    u16 count = 0;
    for (u32 i = 0; i < DECK_SIZE; i++)
    {
        if (deck->cards[i] == cardId)
            count++;
    }
    return count;
}

bool8 ValidateDeck(const struct TcgDeck *deck)
{
    if (!deck)
        return FALSE;

    u16 totalCards = 0;
    bool8 hasBasic = FALSE;

    for (u32 i = 0; i < DECK_SIZE; i++)
    {
        u16 cid = deck->cards[i];
        if (cid != 0)
        {
            totalCards++;
            const struct TcgCardInfo *info = GetTcgCardInfo(cid);
            if (info && info->cardType == CARD_TYPE_POKEMON_BASIC)
            {
                // TCG Pocket: Fossils are items that become basics on field, but DO NOT count as valid basic for deck building or opening hand
                if (info->species != SPECIES_NONE && cid != CARD_MYSTERIOUS_FOSSIL)
                    hasBasic = TRUE;
            }
        }
    }

    // Condition 1: Exactly 20 cards
    if (totalCards != DECK_SIZE)
        return FALSE;

    // Condition 2: Has at least 1 Basic Pokémon
    if (!hasBasic)
        return FALSE;

    // Condition 3 & 4: Sufficient bag quantity and Max 2 copies per species/name
    for (u32 i = 0; i < DECK_SIZE; i++)
    {
        u16 cid = deck->cards[i];
        if (cid == 0)
            continue;

        const struct TcgCardInfo *info = GetTcgCardInfo(cid);
        if (!info)
            return FALSE;

        // Check bag quantity
        u16 countInDeck = CountCardIdInDeck(deck, cid);
        if (countInDeck > GetCardQuantityInBag(cid))
            return FALSE;

        // Check max 2 per species
        if (info->species != SPECIES_NONE)
        {
            u16 speciesCount = 0;
            for (u32 j = 0; j < DECK_SIZE; j++)
            {
                const struct TcgCardInfo *otherInfo = GetTcgCardInfo(deck->cards[j]);
                if (otherInfo && otherInfo->species == info->species)
                    speciesCount++;
            }
            if (speciesCount > 2)
                return FALSE;
        }
    }

    return TRUE;
}

void InitTcgSaveData(void)
{
    gSaveBlock1Ptr->isCurrentDeckDefault = TRUE;
    gSaveBlock1Ptr->currentDeckIndex = 0;
    gSaveBlock1Ptr->unlockedDefaultDecksMask = 0x1; // First deck unlocked by default

    for (u32 i = 0; i < MAX_CUSTOM_DECKS; i++)
    {
        gSaveBlock1Ptr->customDecks[i].name[0] = CHAR_D;
        gSaveBlock1Ptr->customDecks[i].name[1] = CHAR_E;
        gSaveBlock1Ptr->customDecks[i].name[2] = CHAR_C;
        gSaveBlock1Ptr->customDecks[i].name[3] = CHAR_K;
        gSaveBlock1Ptr->customDecks[i].name[4] = CHAR_SPACE;
        gSaveBlock1Ptr->customDecks[i].name[5] = CHAR_1 + (i % 9);
        gSaveBlock1Ptr->customDecks[i].name[6] = EOS;
        gSaveBlock1Ptr->customDecks[i].wallpaper = 0;
        for (u32 j = 0; j < DECK_SIZE; j++)
            gSaveBlock1Ptr->customDecks[i].cards[j] = 0;
    }
}

// Rig Trainer opening hand based on vanilla party
void RigTrainerOpeningHand(u16 *hand, u8 handSize, const u16 *deck, u8 deckSize, u16 trainerId)
{
    // Ensure trainer opening hand contains their signature basics & trainer items
    for (u8 i = 0; i < handSize; i++)
    {
        const struct TcgCardInfo *info = GetTcgCardInfo(hand[i]);
        if (info && info->cardType == CARD_TYPE_POKEMON_BASIC && info->species != SPECIES_NONE && info->cardId != CARD_MYSTERIOUS_FOSSIL)
            return; // Already has a valid basic
    }

    // Find first non-fossil basic in deck and swap into slot 0
    for (u8 d = 0; d < deckSize; d++)
    {
        const struct TcgCardInfo *info = GetTcgCardInfo(deck[d]);
        if (info && info->cardType == CARD_TYPE_POKEMON_BASIC && info->species != SPECIES_NONE && info->cardId != CARD_MYSTERIOUS_FOSSIL)
        {
            hand[0] = deck[d];
            break;
        }
    }
}

// Calculate Prize points target for asymmetric victory
u8 GetTrainerPrizePointsTarget(u8 vanillaPartyCount, bool8 isPlayerTarget)
{
    if (isPlayerTarget)
    {
        // Player needs to KO all N pokemon of the rival
        return vanillaPartyCount > 0 ? vanillaPartyCount : 1;
    }
    else
    {
        // Rival needs to KO max(3, N) pokemon of the player
        return vanillaPartyCount > 3 ? vanillaPartyCount : 3;
    }
}

u16 GetCardIdFromSpecies(u16 species)
{
    if (species == SPECIES_NONE)
        return 0;

    u16 fallbackId = 0;
    for (u16 i = 1; i <= gTcgCardCount; i++)
    {
        if (gTcgCards[i].species == species)
        {
            if (gTcgCards[i].cardType == CARD_TYPE_POKEMON_BASIC)
                return i;
            if (fallbackId == 0)
                fallbackId = i;
        }
    }
    return fallbackId;
}

void GiveStarterDeck(u8 starterNum)
{
    u8 deckIndex;
    if (starterNum == 0)
        deckIndex = DEFAULT_DECK_BULBASAUR;
    else if (starterNum == 1)
        deckIndex = DEFAULT_DECK_SQUIRTLE;
    else
        deckIndex = DEFAULT_DECK_CHARMANDER;

    gSaveBlock1Ptr->isCurrentDeckDefault = TRUE;
    gSaveBlock1Ptr->currentDeckIndex = deckIndex;
    gSaveBlock1Ptr->unlockedDefaultDecksMask |= (1 << deckIndex);

    const struct TcgDeck *deck = &gDefaultDecks[deckIndex];
    u16 firstBasicId = 0;
    for (u32 i = 0; i < DECK_SIZE; i++)
    {
        u16 cid = deck->cards[i];
        if (cid != 0)
        {
            AddCardToBag(cid, 1);
            const struct TcgCardInfo *info = GetTcgCardInfo(cid);
            if (firstBasicId == 0 && info && info->cardType == CARD_TYPE_POKEMON_BASIC && info->species != SPECIES_NONE && cid != CARD_MYSTERIOUS_FOSSIL)
                firstBasicId = cid;
        }
    }
    if (firstBasicId != 0)
    {
        CreateTempMonFromCardId(&gParties[B_TRAINER_PLAYER][0], firstBasicId);
        gSaveBlock1Ptr->playerParty[0] = gParties[B_TRAINER_PLAYER][0];
        for (u32 i = 1; i < PARTY_SIZE; i++)
        {
            ZeroMonData(&gParties[B_TRAINER_PLAYER][i]);
            ZeroMonData(&gSaveBlock1Ptr->playerParty[i]);
        }
        gPartiesCount[B_TRAINER_PLAYER] = 1;
        gSaveBlock1Ptr->playerPartyCount = 1;
    }
    FlagSet(FLAG_SYS_POKEMON_GET);
}

void Script_GiveStarterDeck(void)
{
    GiveStarterDeck(VarGet(VAR_STARTER_MON));
}

bool8 CanPlayerUseFieldHm(u16 itemHmId, u16 badgeFlag)
{
    if (!FlagGet(badgeFlag))
        return FALSE;

    if (!CheckBagHasItem(itemHmId, 1))
        return FALSE;

    const struct TcgDeck *deck;
    if (gSaveBlock1Ptr->isCurrentDeckDefault)
    {
        if (gSaveBlock1Ptr->currentDeckIndex >= MAX_DEFAULT_DECKS)
            return FALSE;
        deck = &gDefaultDecks[gSaveBlock1Ptr->currentDeckIndex];
    }
    else
    {
        if (gSaveBlock1Ptr->currentDeckIndex >= MAX_CUSTOM_DECKS)
            return FALSE;
        deck = &gSaveBlock1Ptr->customDecks[gSaveBlock1Ptr->currentDeckIndex];
    }

    for (u32 i = 0; i < DECK_SIZE; i++)
    {
        u16 cid = deck->cards[i];
        if (cid == 0)
            continue;

        const struct TcgCardInfo *info = GetTcgCardInfo(cid);
        if (!info || info->species == SPECIES_NONE)
            continue;

        switch (itemHmId)
        {
        case ITEM_HM01: // CUT
        case ITEM_HM04: // STRENGTH
        case ITEM_HM06: // ROCK SMASH
            if (info->energyType == ENERGY_GRASS || info->energyType == ENERGY_FIGHTING || info->energyType == ENERGY_COLORLESS)
                return TRUE;
            break;
        case ITEM_HM02: // FLY
            if (info->energyType == ENERGY_COLORLESS)
                return TRUE;
            break;
        case ITEM_HM03: // SURF
        case ITEM_HM07: // WATERFALL
            if (info->energyType == ENERGY_WATER)
                return TRUE;
            break;
        case ITEM_HM05: // FLASH
            if (info->energyType == ENERGY_LIGHTNING || info->energyType == ENERGY_PSYCHIC)
                return TRUE;
            break;
        default:
            return TRUE;
        }
    }

    return FALSE;
}

static struct Pokemon sSavedOverworldParty[PARTY_SIZE];
static u8 sSavedOverworldPartyCount = 0;
static bool8 sPartyIsBackedUp = FALSE;

void RestorePlayerPartyAfterBattle(void)
{
    if (sPartyIsBackedUp)
    {
        for (u32 i = 0; i < PARTY_SIZE; i++)
        {
            gParties[B_TRAINER_PLAYER][i] = sSavedOverworldParty[i];
            gSaveBlock1Ptr->playerParty[i] = sSavedOverworldParty[i];
        }
        gPartiesCount[B_TRAINER_PLAYER] = sSavedOverworldPartyCount;
        gSaveBlock1Ptr->playerPartyCount = sSavedOverworldPartyCount;
        sPartyIsBackedUp = FALSE;
    }
}

static void PopulateBoxWithDeck(u8 boxId, const struct TcgDeck *deck)
{
    if (gPokemonStoragePtr == NULL || boxId >= TOTAL_BOXES_COUNT)
        return;

    if (deck == NULL)
    {
        StringCopyN(gPokemonStoragePtr->boxNames[boxId], COMPOUND_STRING("LOCKED"), BOX_NAME_LENGTH);
        gPokemonStoragePtr->boxNames[boxId][BOX_NAME_LENGTH] = EOS;
        gPokemonStoragePtr->boxWallpapers[boxId] = 0;
        for (u32 i = 0; i < IN_BOX_COUNT; i++)
            ZeroBoxMonData(&gPokemonStoragePtr->boxes[boxId][i]);
        return;
    }

    StringCopyN(gPokemonStoragePtr->boxNames[boxId], deck->name, BOX_NAME_LENGTH);
    gPokemonStoragePtr->boxNames[boxId][BOX_NAME_LENGTH] = EOS;
    gPokemonStoragePtr->boxWallpapers[boxId] = deck->wallpaper;

    for (u32 i = 0; i < IN_BOX_COUNT; i++)
    {
        if (i < DECK_SIZE && deck->cards[i] != 0)
        {
            u16 cid = deck->cards[i];
            const struct TcgCardInfo *info = GetTcgCardInfo(cid);
            if (info)
            {
                u16 species = (info->species != SPECIES_NONE) ? info->species : SPECIES_UNOWN;
                CreateBoxMon(&gPokemonStoragePtr->boxes[boxId][i], species, 1, 0, (struct OriginalTrainerId){0});
                u32 expVal = cid;
                SetBoxMonData(&gPokemonStoragePtr->boxes[boxId][i], MON_DATA_EXP, &expVal);

                u8 nickname[POKEMON_NAME_LENGTH + 1];
                StringCopyN(nickname, info->name, POKEMON_NAME_LENGTH);
                nickname[POKEMON_NAME_LENGTH] = EOS;
                SetBoxMonData(&gPokemonStoragePtr->boxes[boxId][i], MON_DATA_NICKNAME, nickname);
            }
            else
            {
                ZeroBoxMonData(&gPokemonStoragePtr->boxes[boxId][i]);
            }
        }
        else
        {
            ZeroBoxMonData(&gPokemonStoragePtr->boxes[boxId][i]);
        }
    }
}

void SyncCurrentDeckToBox0(void)
{
    if (gPokemonStoragePtr == NULL)
        return;

    const struct TcgDeck *deck;
    if (gSaveBlock1Ptr->isCurrentDeckDefault)
    {
        if (gSaveBlock1Ptr->currentDeckIndex >= MAX_DEFAULT_DECKS)
            gSaveBlock1Ptr->currentDeckIndex = 0;
        deck = &gDefaultDecks[gSaveBlock1Ptr->currentDeckIndex];
    }
    else
    {
        if (gSaveBlock1Ptr->currentDeckIndex >= MAX_CUSTOM_DECKS)
            gSaveBlock1Ptr->currentDeckIndex = 0;
        deck = &gSaveBlock1Ptr->customDecks[gSaveBlock1Ptr->currentDeckIndex];
    }

    PopulateBoxWithDeck(0, deck);
}

u8 GetUnlockedDefaultDeckIndexForBox(u8 boxId)
{
    if (boxId >= TOTAL_BOXES_COUNT)
        return 0xFF;

    u8 found = 0;
    for (u8 idx = 0; idx < MAX_DEFAULT_DECKS; idx++)
    {
        if (gSaveBlock1Ptr->unlockedDefaultDecksMask & (1u << idx))
        {
            if (found == boxId)
                return idx;
            found++;
        }
    }
    return 0xFF;
}

void SyncDefaultDecksToBoxes(void)
{
    if (gPokemonStoragePtr == NULL)
        return;

    EnsureStarterDeckCardsInBag();
    for (u8 boxId = 0; boxId < TOTAL_BOXES_COUNT; boxId++)
    {
        u8 deckIdx = GetUnlockedDefaultDeckIndexForBox(boxId);
        if (deckIdx < MAX_DEFAULT_DECKS)
            PopulateBoxWithDeck(boxId, &gDefaultDecks[deckIdx]);
        else
            PopulateBoxWithDeck(boxId, NULL);
    }
}

void SyncCustomDecksToBoxes(void)
{
    if (gPokemonStoragePtr == NULL)
        return;

    for (u8 boxId = 0; boxId < TOTAL_BOXES_COUNT; boxId++)
    {
        if (boxId < MAX_CUSTOM_DECKS)
            PopulateBoxWithDeck(boxId, &gSaveBlock1Ptr->customDecks[boxId]);
        else
            PopulateBoxWithDeck(boxId, NULL);
    }
}

void SaveBoxesToCustomDecks(void)
{
    if (gPokemonStoragePtr == NULL)
        return;

    for (u8 boxId = 0; boxId < MAX_CUSTOM_DECKS && boxId < TOTAL_BOXES_COUNT; boxId++)
    {
        struct TcgDeck *deck = &gSaveBlock1Ptr->customDecks[boxId];
        StringCopyN(deck->name, gPokemonStoragePtr->boxNames[boxId], BOX_NAME_LENGTH);
        deck->name[BOX_NAME_LENGTH] = EOS;
        deck->wallpaper = gPokemonStoragePtr->boxWallpapers[boxId];

        u32 writeIdx = 0;
        for (u32 pos = 0; pos < IN_BOX_COUNT; pos++)
        {
            u16 species = GetBoxMonDataAt(boxId, pos, MON_DATA_SPECIES);
            u16 cid = (u16)(GetBoxMonDataAt(boxId, pos, MON_DATA_EXP) & 0xFFFF);
            if (species != SPECIES_NONE && cid != 0 && writeIdx < DECK_SIZE)
                deck->cards[writeIdx++] = cid;
        }
        while (writeIdx < DECK_SIZE)
            deck->cards[writeIdx++] = 0;
    }
}

void SyncBox0ToCurrentDeck(void)
{
    if (gTcgBattleState.pcStorageMode == TCG_PC_MODE_CUSTOM_DECKS)
        SaveBoxesToCustomDecks();
}

bool8 CanBuildDefaultDeck(u8 deckIndex)
{
    if (deckIndex >= MAX_DEFAULT_DECKS)
        return FALSE;
    return ValidateDeck(&gDefaultDecks[deckIndex]);
}

bool8 CanBuildCustomDeck(const struct TcgDeck *deck)
{
    return ValidateDeck(deck);
}

bool8 TryAddCardToCustomDeckBox(u8 boxId, u16 cardId)
{
    if (boxId >= MAX_CUSTOM_DECKS || cardId == 0)
        return FALSE;

    const struct TcgCardInfo *info = GetTcgCardInfo(cardId);
    if (!info)
        return FALSE;

    SaveBoxesToCustomDecks();
    struct TcgDeck *deck = &gSaveBlock1Ptr->customDecks[boxId];

    // Check total cards in deck < 20
    u32 count = 0;
    u32 sameCardCount = 0;
    u32 sameSpeciesCount = 0;
    for (u32 i = 0; i < DECK_SIZE; i++)
    {
        u16 cid = deck->cards[i];
        if (cid != 0)
        {
            count++;
            if (cid == cardId)
                sameCardCount++;
            const struct TcgCardInfo *other = GetTcgCardInfo(cid);
            if (info->species != SPECIES_NONE && other && other->species == info->species)
                sameSpeciesCount++;
        }
    }

    if (count >= DECK_SIZE)
        return FALSE;
    if (sameCardCount >= 2)
        return FALSE;
    if (info->species != SPECIES_NONE && sameSpeciesCount >= 2)
        return FALSE;
    if (sameCardCount + 1 > GetCardQuantityInBag(cardId))
        return FALSE;

    for (u32 i = 0; i < DECK_SIZE; i++)
    {
        if (deck->cards[i] == 0)
        {
            deck->cards[i] = cardId;
            break;
        }
    }

    PopulateBoxWithDeck(boxId, deck);
    return TRUE;
}

void EnsureStarterDeckCardsInBag(void)
{
    struct BagPocket *legPocket = &gBagPockets[POCKET_ITEMS_LEG];
    bool8 cleaned = FALSE;
    for (u32 i = 0; i < legPocket->capacity; i++)
    {
        struct ItemSlot slot = BagPocket_GetSlotData(legPocket, i);
        if (slot.itemId > ITEM_NONE && slot.itemId <= 25)
        {
            struct ItemSlot emptySlot = { .itemId = ITEM_NONE, .quantity = 0 };
            BagPocket_SetSlotData(legPocket, i, emptySlot);
            cleaned = TRUE;
        }
    }
    if (cleaned)
    {
        CompactItemsInBagPocket(POCKET_ITEMS_LEG);
    }

    // Auto-heal legacy saves that had outdated starter deck indices
    if (FlagGet(FLAG_SYS_POKEMON_GET))
    {
        u16 starterChoice = VarGet(VAR_STARTER_MON);
        if (starterChoice == 1 && (gSaveBlock1Ptr->currentDeckIndex == 5 || gSaveBlock1Ptr->currentDeckIndex < 10))
        {
            gSaveBlock1Ptr->currentDeckIndex = DEFAULT_DECK_SQUIRTLE;
            gSaveBlock1Ptr->unlockedDefaultDecksMask |= (1 << DEFAULT_DECK_SQUIRTLE);
        }
        else if (starterChoice == 0 && (gSaveBlock1Ptr->currentDeckIndex == 7 || gSaveBlock1Ptr->currentDeckIndex < 6))
        {
            gSaveBlock1Ptr->currentDeckIndex = DEFAULT_DECK_BULBASAUR;
            gSaveBlock1Ptr->unlockedDefaultDecksMask |= (1 << DEFAULT_DECK_BULBASAUR);
        }
        else if (starterChoice == 2 && (gSaveBlock1Ptr->currentDeckIndex == 3 || gSaveBlock1Ptr->currentDeckIndex < 6))
        {
            gSaveBlock1Ptr->currentDeckIndex = DEFAULT_DECK_CHARMANDER;
            gSaveBlock1Ptr->unlockedDefaultDecksMask |= (1 << DEFAULT_DECK_CHARMANDER);
        }
    }

    struct BagPocket *pokePocket = &gBagPockets[POCKET_TCG_POKEMON];
    u16 cardCount = 0;
    for (u32 i = 0; i < pokePocket->capacity; i++)
    {
        struct ItemSlot slot = BagPocket_GetSlotData(pokePocket, i);
        if (slot.itemId != ITEM_NONE && slot.quantity > 0)
            cardCount += slot.quantity;
    }

    if (cardCount == 0 && (FlagGet(FLAG_SYS_POKEMON_GET) || gSaveBlock1Ptr->unlockedDefaultDecksMask != 0))
    {
        u8 deckIndex = gSaveBlock1Ptr->currentDeckIndex;
        if (deckIndex >= MAX_DEFAULT_DECKS)
            deckIndex = 0;
        const struct TcgDeck *deck = &gDefaultDecks[deckIndex];
        for (u32 i = 0; i < DECK_SIZE; i++)
        {
            u16 cid = deck->cards[i];
            if (cid != 0)
                AddCardToBag(cid, 1);
        }
    }

    if (!gMain.inBattle && FlagGet(FLAG_SYS_POKEMON_GET) && gPartiesCount[B_TRAINER_PLAYER] == 0)
    {
        u8 deckIndex = gSaveBlock1Ptr->currentDeckIndex;
        if (deckIndex >= MAX_DEFAULT_DECKS)
            deckIndex = 0;
        const struct TcgDeck *deck = &gDefaultDecks[deckIndex];
        for (u32 i = 0; i < DECK_SIZE; i++)
        {
            const struct TcgCardInfo *info = GetTcgCardInfo(deck->cards[i]);
            if (info && info->cardType == CARD_TYPE_POKEMON_BASIC && info->species != SPECIES_NONE && deck->cards[i] != CARD_MYSTERIOUS_FOSSIL)
            {
                CreateTempMonFromCardId(&gParties[B_TRAINER_PLAYER][0], deck->cards[i]);
                gSaveBlock1Ptr->playerParty[0] = gParties[B_TRAINER_PLAYER][0];
                gPartiesCount[B_TRAINER_PLAYER] = 1;
                gSaveBlock1Ptr->playerPartyCount = 1;
                break;
            }
        }
    }
}

void InitTcgBattleState(void)
{
    memset(&gTcgBattleState, 0, sizeof(gTcgBattleState));

    EnsureStarterDeckCardsInBag();

    if (!sPartyIsBackedUp)
    {
        for (u32 i = 0; i < PARTY_SIZE; i++)
            sSavedOverworldParty[i] = gParties[B_TRAINER_PLAYER][i];
        sSavedOverworldPartyCount = gPartiesCount[B_TRAINER_PLAYER];
        sPartyIsBackedUp = TRUE;
    }

    const struct TcgDeck *playerDeck;
    if (gSaveBlock1Ptr->isCurrentDeckDefault)
    {
        if (gSaveBlock1Ptr->currentDeckIndex >= MAX_DEFAULT_DECKS)
            gSaveBlock1Ptr->currentDeckIndex = 0;
        playerDeck = &gDefaultDecks[gSaveBlock1Ptr->currentDeckIndex];
    }
    else
    {
        if (gSaveBlock1Ptr->currentDeckIndex >= MAX_CUSTOM_DECKS)
            gSaveBlock1Ptr->currentDeckIndex = 0;
        playerDeck = &gSaveBlock1Ptr->customDecks[gSaveBlock1Ptr->currentDeckIndex];
        if (!ValidateDeck(playerDeck))
            playerDeck = &gDefaultDecks[0];
    }

    for (u32 i = 0; i < DECK_SIZE; i++)
    {
        u16 cid = playerDeck->cards[i];
        if (cid == 0)
            continue;

        const struct TcgCardInfo *info = GetTcgCardInfo(cid);
        if (!info)
            continue;

        for (u32 t = 0; t < NUM_ENERGY_TYPES; t++)
        {
            if (t != ENERGY_COLORLESS && (info->move1Cost.energyCount[t] > 0 || info->move2Cost.energyCount[t] > 0))
            {
                bool8 exists = FALSE;
                for (u32 k = 0; k < gTcgBattleState.numPlayerDeckEnergyTypes; k++)
                {
                    if (gTcgBattleState.playerDeckEnergyTypes[k] == t)
                    {
                        exists = TRUE;
                        break;
                    }
                }
                if (!exists && gTcgBattleState.numPlayerDeckEnergyTypes < NUM_ENERGY_TYPES)
                    gTcgBattleState.playerDeckEnergyTypes[gTcgBattleState.numPlayerDeckEnergyTypes++] = t;
            }
        }
    }

    if (gTcgBattleState.numPlayerDeckEnergyTypes == 0)
        gTcgBattleState.playerDeckEnergyTypes[gTcgBattleState.numPlayerDeckEnergyTypes++] = ENERGY_GRASS;

    u16 tempDeck[DECK_SIZE];
    for (u32 i = 0; i < DECK_SIZE; i++)
        tempDeck[i] = playerDeck->cards[i];

    for (s32 i = DECK_SIZE - 1; i > 0; i--)
    {
        u32 j = Random() % (i + 1);
        u16 tmp = tempDeck[i];
        tempDeck[i] = tempDeck[j];
        tempDeck[j] = tmp;
    }

    s32 basicIdx = -1;
    for (u32 i = 0; i < DECK_SIZE; i++)
    {
        const struct TcgCardInfo *info = GetTcgCardInfo(tempDeck[i]);
        if (info && info->cardType == CARD_TYPE_POKEMON_BASIC && info->species != SPECIES_NONE && info->cardId != CARD_MYSTERIOUS_FOSSIL)
        {
            basicIdx = i;
            break;
        }
    }

    if (basicIdx > 0)
    {
        u16 tmp = tempDeck[0];
        tempDeck[0] = tempDeck[basicIdx];
        tempDeck[basicIdx] = tmp;
    }

    // 5-card opening hand goes into playerHand[0..4]
    for (u32 i = 0; i < 5; i++)
        gTcgBattleState.playerHand[i] = tempDeck[i];
    gTcgBattleState.playerHandCount = 5;

    // Remaining 15 cards go into playerDeckRemaining[0..14]
    for (u32 i = 0; i < 15; i++)
        gTcgBattleState.playerDeckRemaining[i] = tempDeck[5 + i];
    gTcgBattleState.playerDeckRemainingCount = 15;

    // Initialize Field slot 0 with tempDeck[0] as a safe placeholder until the player chooses their Active Pokémon in DoBattleIntro
    CreateTempMonFromCardId(&gParties[B_TRAINER_PLAYER][0], tempDeck[0]);
    for (u32 i = 1; i < PARTY_SIZE; i++)
        ZeroMonData(&gParties[B_TRAINER_PLAYER][i]);
    gPartiesCount[B_TRAINER_PLAYER] = 1;
    gTcgBattleState.activeMonPlaced = FALSE;

    // Pre-generate preview of next energy type
    gTcgBattleState.nextGeneratedEnergyType[B_SIDE_PLAYER] =
        gTcgBattleState.playerDeckEnergyTypes[Random() % gTcgBattleState.numPlayerDeckEnergyTypes];

    if (gBattleTypeFlags & BATTLE_TYPE_TRAINER)
    {
        u8 oppCount = gPartiesCount[B_TRAINER_OPPONENT_A];
        if (oppCount == 0)
            oppCount = 1;

        for (u32 m = 0; m < oppCount; m++)
        {
            u16 oppSpecies = GetMonData(&gParties[B_TRAINER_OPPONENT_A][m], MON_DATA_SPECIES);
            u16 oppCardId = GetCardIdFromSpecies(oppSpecies);
            if (oppCardId != 0)
                CreateTempMonFromCardId(&gParties[B_TRAINER_OPPONENT_A][m], oppCardId);
        }

        // Also build the opponent's 20-card thematic deck for hand/deck interactions
        struct TcgDeck oppDeck;
        BuildTemporaryTrainerDeck(TRAINER_BATTLE_PARAM.opponentA, &oppDeck);
        for (u32 i = 0; i < 5; i++)
            gTcgBattleState.opponentHand[i] = oppDeck.cards[i];
        gTcgBattleState.opponentHandCount = 5;
        for (u32 i = 0; i < 15; i++)
            gTcgBattleState.opponentDeckRemaining[i] = oppDeck.cards[5 + i];
        gTcgBattleState.opponentDeckRemainingCount = 15;

        for (u32 m = 0; m < oppCount; m++)
        {
            u16 cid = GetMonCardId(&gParties[B_TRAINER_OPPONENT_A][m]);
            const struct TcgCardInfo *info = GetTcgCardInfo(cid);
            if (!info) continue;
            for (u32 t = 0; t < NUM_ENERGY_TYPES; t++)
            {
                if (t != ENERGY_COLORLESS && (info->move1Cost.energyCount[t] > 0 || info->move2Cost.energyCount[t] > 0))
                {
                    bool8 exists = FALSE;
                    for (u32 k = 0; k < gTcgBattleState.numOpponentDeckEnergyTypes; k++)
                    {
                        if (gTcgBattleState.opponentDeckEnergyTypes[k] == t)
                        {
                            exists = TRUE;
                            break;
                        }
                    }
                    if (!exists && gTcgBattleState.numOpponentDeckEnergyTypes < NUM_ENERGY_TYPES)
                        gTcgBattleState.opponentDeckEnergyTypes[gTcgBattleState.numOpponentDeckEnergyTypes++] = t;
                }
            }
        }

        if (gTcgBattleState.numOpponentDeckEnergyTypes == 0)
            gTcgBattleState.opponentDeckEnergyTypes[gTcgBattleState.numOpponentDeckEnergyTypes++] = ENERGY_GRASS;

        gTcgBattleState.playerPrizeTarget = oppCount;
        gTcgBattleState.opponentPrizeTarget = 3;
    }
    else
    {
        u16 wildSpecies = GetMonData(&gParties[B_TRAINER_OPPONENT_A][0], MON_DATA_SPECIES);
        u16 cardId = GetCardIdFromSpecies(wildSpecies);
        if (cardId != 0)
            CreateTempMonFromCardId(&gParties[B_TRAINER_OPPONENT_A][0], cardId);
        gPartiesCount[B_TRAINER_OPPONENT_A] = 1;

        const struct TcgCardInfo *info = GetTcgCardInfo(cardId);
        if (info && info->energyType != ENERGY_COLORLESS)
            gTcgBattleState.opponentDeckEnergyTypes[gTcgBattleState.numOpponentDeckEnergyTypes++] = info->energyType;
        else
            gTcgBattleState.opponentDeckEnergyTypes[gTcgBattleState.numOpponentDeckEnergyTypes++] = ENERGY_GRASS;

        gTcgBattleState.playerPrizeTarget = 1;
        gTcgBattleState.opponentPrizeTarget = 3;
    }

    gTcgBattleState.nextGeneratedEnergyType[B_SIDE_OPPONENT] =
        gTcgBattleState.opponentDeckEnergyTypes[Random() % gTcgBattleState.numOpponentDeckEnergyTypes];
}

void GenerateTurnEnergy(u8 side)
{
    if (side == B_SIDE_PLAYER)
    {
        if (gBattleTurnCounter == 0 && gTcgBattleState.firstTurnFirstPlayer)
            return; // Turn 1 first player does not generate energy

        if (gTcgBattleState.numPlayerDeckEnergyTypes == 0)
            return;

        u8 chosenType = gTcgBattleState.nextGeneratedEnergyType[B_SIDE_PLAYER];
        if (chosenType >= NUM_ENERGY_TYPES)
            chosenType = gTcgBattleState.playerDeckEnergyTypes[Random() % gTcgBattleState.numPlayerDeckEnergyTypes];

        gTcgBattleState.lastGeneratedEnergyType[B_SIDE_PLAYER] = chosenType;
        gTcgBattleState.nextGeneratedEnergyType[B_SIDE_PLAYER] =
            gTcgBattleState.playerDeckEnergyTypes[Random() % gTcgBattleState.numPlayerDeckEnergyTypes];

        gTcgBattleState.playerEnergyPool[chosenType]++;
        gTcgBattleState.energyGeneratedThisTurn = TRUE;
    }
    else
    {
        if (gTcgBattleState.numOpponentDeckEnergyTypes > 0)
        {
            u8 chosenType = gTcgBattleState.nextGeneratedEnergyType[B_SIDE_OPPONENT];
            if (chosenType >= NUM_ENERGY_TYPES)
                chosenType = gTcgBattleState.opponentDeckEnergyTypes[Random() % gTcgBattleState.numOpponentDeckEnergyTypes];

            gTcgBattleState.lastGeneratedEnergyType[B_SIDE_OPPONENT] = chosenType;
            gTcgBattleState.nextGeneratedEnergyType[B_SIDE_OPPONENT] =
                gTcgBattleState.opponentDeckEnergyTypes[Random() % gTcgBattleState.numOpponentDeckEnergyTypes];

            gTcgBattleState.opponentEnergyPool[chosenType]++;
            gTcgBattleState.slotEnergyCount[B_SIDE_OPPONENT][0]++;
            gTcgBattleState.slotEnergyByType[B_SIDE_OPPONENT][0][chosenType]++;
            u8 battler = GetBattlerAtPosition(B_POSITION_OPPONENT_LEFT);
            if (battler < gBattlersCount)
                gTcgBattleState.activeEnergyCount[battler] = gTcgBattleState.slotEnergyCount[B_SIDE_OPPONENT][0];
        }
    }
}

void AttachTurnEnergyToSlot(u8 side, u8 slot)
{
    if (side >= NUM_BATTLE_SIDES || slot >= PARTY_SIZE)
        return;

    u8 energyType = gTcgBattleState.lastGeneratedEnergyType[side];
    if (energyType >= NUM_ENERGY_TYPES)
        energyType = ENERGY_GRASS;

    gTcgBattleState.slotEnergyCount[side][slot]++;
    gTcgBattleState.slotEnergyByType[side][slot][energyType]++;
    gTcgBattleState.energyAttachedThisTurn = TRUE;

    if (slot == 0)
    {
        u8 battler = GetBattlerAtPosition(side == B_SIDE_PLAYER ? B_POSITION_PLAYER_LEFT : B_POSITION_OPPONENT_LEFT);
        if (battler < gBattlersCount)
            gTcgBattleState.activeEnergyCount[battler] = gTcgBattleState.slotEnergyCount[side][0];
    }
}

void DiscardEnergyFromSlot(u8 side, u8 slot, u8 count)
{
    if (side >= NUM_BATTLE_SIDES || slot >= PARTY_SIZE || count == 0)
        return;

    for (u8 c = 0; c < count; c++)
    {
        if (gTcgBattleState.slotEnergyCount[side][slot] == 0)
            break;

        gTcgBattleState.slotEnergyCount[side][slot]--;
        for (u8 t = 0; t < NUM_ENERGY_TYPES; t++)
        {
            if (gTcgBattleState.slotEnergyByType[side][slot][t] > 0)
            {
                gTcgBattleState.slotEnergyByType[side][slot][t]--;
                break;
            }
        }
    }

    if (slot == 0)
    {
        u8 battler = GetBattlerAtPosition(side == B_SIDE_PLAYER ? B_POSITION_PLAYER_LEFT : B_POSITION_OPPONENT_LEFT);
        if (battler < gBattlersCount)
            gTcgBattleState.activeEnergyCount[battler] = gTcgBattleState.slotEnergyCount[side][0];
    }
}

void SwapSlotEnergies(u8 side, u8 slotA, u8 slotB)
{
    if (side >= NUM_BATTLE_SIDES || slotA >= PARTY_SIZE || slotB >= PARTY_SIZE || slotA == slotB)
        return;

    u8 tmpCount = gTcgBattleState.slotEnergyCount[side][slotA];
    gTcgBattleState.slotEnergyCount[side][slotA] = gTcgBattleState.slotEnergyCount[side][slotB];
    gTcgBattleState.slotEnergyCount[side][slotB] = tmpCount;

    for (u8 t = 0; t < NUM_ENERGY_TYPES; t++)
    {
        u8 tmpType = gTcgBattleState.slotEnergyByType[side][slotA][t];
        gTcgBattleState.slotEnergyByType[side][slotA][t] = gTcgBattleState.slotEnergyByType[side][slotB][t];
        gTcgBattleState.slotEnergyByType[side][slotB][t] = tmpType;
    }

    if (side == B_SIDE_PLAYER)
    {
        u8 tmpPlaced = gTcgBattleState.turnMonPlaced[slotA];
        gTcgBattleState.turnMonPlaced[slotA] = gTcgBattleState.turnMonPlaced[slotB];
        gTcgBattleState.turnMonPlaced[slotB] = tmpPlaced;

        u8 tmpEvolved = gTcgBattleState.turnMonEvolved[slotA];
        gTcgBattleState.turnMonEvolved[slotA] = gTcgBattleState.turnMonEvolved[slotB];
        gTcgBattleState.turnMonEvolved[slotB] = tmpEvolved;
    }

    u8 battler = GetBattlerAtPosition(side == B_SIDE_PLAYER ? B_POSITION_PLAYER_LEFT : B_POSITION_OPPONENT_LEFT);
    if (battler < gBattlersCount)
        gTcgBattleState.activeEnergyCount[battler] = gTcgBattleState.slotEnergyCount[side][0];
}

bool8 HasEnoughEnergyForAttack(u8 side, u8 slot, const struct TcgAttackCost *cost)
{
    if (!cost || side >= NUM_BATTLE_SIDES || slot >= PARTY_SIZE)
        return TRUE;

    u8 totalRequired = 0;
    for (u32 t = 0; t < NUM_ENERGY_TYPES; t++)
    {
        u8 req = cost->energyCount[t];
        totalRequired += req;
        if (t != ENERGY_COLORLESS && req > 0)
        {
            // Charizard Energy Burn allows all energies to count as Fire
            u16 activeCid = (side == B_SIDE_PLAYER) ? GetMonCardId(&gParties[B_TRAINER_PLAYER][slot]) : GetMonCardId(&gParties[B_TRAINER_OPPONENT_A][slot]);
            if (activeCid == CARD_CHARIZARD && t == ENERGY_FIRE)
                continue;
            if (gTcgBattleState.slotEnergyByType[side][slot][t] < req)
                return FALSE;
        }
    }

    return (gTcgBattleState.slotEnergyCount[side][slot] >= totalRequired);
}

void RecordDiscardedCard(u8 side, u16 cardId)
{
    if (cardId == 0)
        return;

    if (side == B_SIDE_PLAYER)
    {
        if (gTcgBattleState.playerDiscardCount < DECK_SIZE)
            gTcgBattleState.playerDiscardPile[gTcgBattleState.playerDiscardCount++] = cardId;
    }
    else
    {
        if (gTcgBattleState.opponentDiscardCount < DECK_SIZE)
            gTcgBattleState.opponentDiscardPile[gTcgBattleState.opponentDiscardCount++] = cardId;
    }
}

bool8 DrawCardForPlayer(void)
{
    if (gTcgBattleState.playerDeckRemainingCount == 0)
        return FALSE; // TCG Pocket: no deck-out loss

    u16 drawn = gTcgBattleState.playerDeckRemaining[0];
    for (u32 i = 0; i + 1 < gTcgBattleState.playerDeckRemainingCount; i++)
        gTcgBattleState.playerDeckRemaining[i] = gTcgBattleState.playerDeckRemaining[i + 1];
    gTcgBattleState.playerDeckRemaining[gTcgBattleState.playerDeckRemainingCount - 1] = 0;
    gTcgBattleState.playerDeckRemainingCount--;

    if (gTcgBattleState.playerHandCount < 10)
    {
        gTcgBattleState.playerHand[gTcgBattleState.playerHandCount++] = drawn;
        return TRUE;
    }
    return FALSE;
}

bool8 DrawCardForOpponent(void)
{
    if (gTcgBattleState.opponentDeckRemainingCount == 0)
        return FALSE;

    u16 drawn = gTcgBattleState.opponentDeckRemaining[0];
    for (u32 i = 0; i + 1 < gTcgBattleState.opponentDeckRemainingCount; i++)
        gTcgBattleState.opponentDeckRemaining[i] = gTcgBattleState.opponentDeckRemaining[i + 1];
    gTcgBattleState.opponentDeckRemaining[gTcgBattleState.opponentDeckRemainingCount - 1] = 0;
    gTcgBattleState.opponentDeckRemainingCount--;

    if (gTcgBattleState.opponentHandCount < 10)
    {
        gTcgBattleState.opponentHand[gTcgBattleState.opponentHandCount++] = drawn;
        return TRUE;
    }
    return FALSE;
}

void RemoveCardFromPlayerHandAt(u8 handIndex)
{
    if (handIndex >= gTcgBattleState.playerHandCount)
        return;

    for (u32 i = handIndex; i + 1 < gTcgBattleState.playerHandCount; i++)
        gTcgBattleState.playerHand[i] = gTcgBattleState.playerHand[i + 1];
    gTcgBattleState.playerHand[gTcgBattleState.playerHandCount - 1] = 0;
    gTcgBattleState.playerHandCount--;

    if (gTcgBattleState.handScrollOffset > 0 && gTcgBattleState.handScrollOffset + 6 > gTcgBattleState.playerHandCount)
        gTcgBattleState.handScrollOffset--;
}

bool8 TryPlaceOrEvolveFromHand(u8 handIndex, u8 *outFieldSlot, bool8 *outEvolved)
{
    if (handIndex >= gTcgBattleState.playerHandCount)
        return FALSE;

    u16 cardId = gTcgBattleState.playerHand[handIndex];
    const struct TcgCardInfo *info = GetTcgCardInfo(cardId);
    if (!info)
        return FALSE;

    if (outEvolved)
        *outEvolved = FALSE;

    // 1. Basic Pokémon (or Mysterious Fossil / Clefairy Doll)
    if (info->cardType == CARD_TYPE_POKEMON_BASIC || cardId == CARD_MYSTERIOUS_FOSSIL || cardId == CARD_CLEFAIRY_DOLL)
    {
        if (!gTcgBattleState.activeMonPlaced)
        {
            if (cardId == CARD_MYSTERIOUS_FOSSIL || cardId == CARD_CLEFAIRY_DOLL)
                return FALSE; // Cannot start battle with a fossil/doll as initial Active
            CreateTempMonFromCardId(&gParties[B_TRAINER_PLAYER][0], cardId);
            gPartiesCount[B_TRAINER_PLAYER] = 1;
            gTcgBattleState.activeMonPlaced = TRUE;
            MarkMonPlaced(0);
            RemoveCardFromPlayerHandAt(handIndex);
            if (outFieldSlot)
                *outFieldSlot = 0;
            return TRUE;
        }

        // Otherwise place onto the first open Bench slot (1..3, max 4 Field Pokémon total)
        for (u8 slot = 1; slot < MAX_FIELD_POKEMON; slot++)
        {
            if (GetMonData(&gParties[B_TRAINER_PLAYER][slot], MON_DATA_SPECIES) == SPECIES_NONE
             || GetMonData(&gParties[B_TRAINER_PLAYER][slot], MON_DATA_HP) == 0)
            {
                CreateTempMonFromCardId(&gParties[B_TRAINER_PLAYER][slot], cardId);
                if (slot >= gPartiesCount[B_TRAINER_PLAYER])
                    gPartiesCount[B_TRAINER_PLAYER] = slot + 1;
                MarkMonPlaced(slot);
                RemoveCardFromPlayerHandAt(handIndex);
                if (outFieldSlot)
                    *outFieldSlot = slot;
                return TRUE;
            }
        }
        return FALSE;
    }

    // 2. Stage 1 / Stage 2 Evolution
    if ((info->cardType == CARD_TYPE_POKEMON_STAGE1 || info->cardType == CARD_TYPE_POKEMON_STAGE2)
        && info->preEvoSpecies != SPECIES_NONE)
    {
        for (u8 slot = 0; slot < MAX_FIELD_POKEMON; slot++)
        {
            struct Pokemon *fieldMon = &gParties[B_TRAINER_PLAYER][slot];
            u16 fieldSpecies = GetMonData(fieldMon, MON_DATA_SPECIES);
            u16 fieldHp = GetMonData(fieldMon, MON_DATA_HP);
            u16 fieldMaxHp = GetMonData(fieldMon, MON_DATA_MAX_HP);
            u16 fieldCid = GetMonCardId(fieldMon);

            bool8 matchesPreEvo = (fieldSpecies == info->preEvoSpecies);
            if (fieldCid == CARD_MYSTERIOUS_FOSSIL && (info->species == SPECIES_OMANYTE || info->species == SPECIES_KABUTO || info->species == SPECIES_AERODACTYL))
                matchesPreEvo = TRUE;

            if (fieldHp > 0 && matchesPreEvo && CanMonEvolveThisTurn(slot))
            {
                u16 damageTaken = (fieldMaxHp > fieldHp) ? (fieldMaxHp - fieldHp) : 0;
                CreateTempMonFromCardId(fieldMon, cardId);
                u16 newMaxHp = GetMonData(fieldMon, MON_DATA_MAX_HP);
                u16 newHp = (newMaxHp > damageTaken) ? (newMaxHp - damageTaken) : 10;
                SetMonData(fieldMon, MON_DATA_HP, &newHp);

                // Evolution cures all status conditions on Active Pokémon
                u32 zeroStatus = 0;
                SetMonData(fieldMon, MON_DATA_STATUS, &zeroStatus);
                if (slot == 0)
                {
                    u8 playerBattler = GetBattlerAtPosition(B_POSITION_PLAYER_LEFT);
                    if (playerBattler < gBattlersCount)
                    {
                        gBattleMons[playerBattler].species = GetMonData(fieldMon, MON_DATA_SPECIES);
                        gBattleMons[playerBattler].maxHP = newMaxHp;
                        gBattleMons[playerBattler].hp = newHp;
                        gBattleMons[playerBattler].status1 = 0;
                        gBattleMons[playerBattler].volatiles.confusionTimer = 0;
                        for (u8 m = 0; m < MAX_MON_MOVES; m++)
                            gBattleMons[playerBattler].moves[m] = GetMonData(fieldMon, MON_DATA_MOVE1 + m);
                    }
                }

                MarkMonEvolved(slot);
                RemoveCardFromPlayerHandAt(handIndex);
                if (outFieldSlot)
                    *outFieldSlot = slot;
                if (outEvolved)
                    *outEvolved = TRUE;
                return TRUE;
            }
        }
    }

    return FALSE;
}

bool8 ExecutePokemonPower(u16 cardId, u8 slot, u8 battler)
{
    const struct TcgCardInfo *info = GetTcgCardInfo(cardId);
    if (!info || info->pokemonPowerId == 0 || slot >= PARTY_SIZE)
        return FALSE;

    u8 side = GetBattlerSide(battler);
    if (gTcgBattleState.goopGasActive[side] || gTcgBattleState.goopGasActive[side ^ 1])
        return FALSE;

    // Check Muk's Toxic Gas on either Active Pokémon
    for (u8 b = 0; b < gBattlersCount; b++)
    {
        if (IsBattlerAlive(b) && GetMonCardId(GetBattlerMon(b)) == CARD_MUK)
            return FALSE;
    }

    // Active Pokémon cannot use Pokémon Powers while Asleep, Paralyzed, or Confused
    if (slot == 0)
    {
        if ((gBattleMons[battler].status1 & (STATUS1_SLEEP | STATUS1_PARALYSIS))
         || gBattleMons[battler].volatiles.confusionTimer > 0)
            return FALSE;
    }

    if (gTcgBattleState.powerUsedThisTurn[slot])
        return FALSE;

    gTcgBattleState.powerUsedThisTurn[slot] = TRUE;
    u8 oppBattler = GetBattlerAtPosition(B_POSITION_OPPONENT_LEFT);

    switch (info->species)
    {
    case SPECIES_BLASTOISE: // Rain Dance: attach 1 Water energy to Active Pokémon
        gTcgBattleState.slotEnergyCount[B_SIDE_PLAYER][0]++;
        gTcgBattleState.slotEnergyByType[B_SIDE_PLAYER][0][ENERGY_WATER]++;
        gTcgBattleState.activeEnergyCount[battler] = gTcgBattleState.slotEnergyCount[B_SIDE_PLAYER][0];
        return TRUE;
    case SPECIES_CHARIZARD: // Energy Burn: convert all attached energy on Charizard to Fire
    {
        u8 total = gTcgBattleState.slotEnergyCount[B_SIDE_PLAYER][slot];
        for (u8 t = 0; t < NUM_ENERGY_TYPES; t++)
            gTcgBattleState.slotEnergyByType[B_SIDE_PLAYER][slot][t] = 0;
        gTcgBattleState.slotEnergyByType[B_SIDE_PLAYER][slot][ENERGY_FIRE] = total;
        return TRUE;
    }
    case SPECIES_VENUSAUR: // Energy Trans: move 1 Grass energy from Bench to Active
        for (u8 b = 1; b < MAX_FIELD_POKEMON; b++)
        {
            if (gTcgBattleState.slotEnergyByType[B_SIDE_PLAYER][b][ENERGY_GRASS] > 0)
            {
                gTcgBattleState.slotEnergyByType[B_SIDE_PLAYER][b][ENERGY_GRASS]--;
                gTcgBattleState.slotEnergyCount[B_SIDE_PLAYER][b]--;
                gTcgBattleState.slotEnergyByType[B_SIDE_PLAYER][0][ENERGY_GRASS]++;
                gTcgBattleState.slotEnergyCount[B_SIDE_PLAYER][0]++;
                gTcgBattleState.activeEnergyCount[battler] = gTcgBattleState.slotEnergyCount[B_SIDE_PLAYER][0];
                return TRUE;
            }
        }
        return TRUE;
    case SPECIES_ALAKAZAM: // Damage Swap
    case SPECIES_SLOWBRO:  // Strange Behavior
    case SPECIES_VILEPLUME:// Heal
    case SPECIES_GOLDUCK:
    case SPECIES_STARMIE:
    case SPECIES_BUTTERFREE:
    {
        u16 curHp = gBattleMons[battler].hp;
        u16 maxHp = gBattleMons[battler].maxHP;
        if (curHp > 0 && curHp < maxHp)
        {
            curHp = (curHp + 10 > maxHp) ? maxHp : (curHp + 10);
            gBattleMons[battler].hp = curHp;
            SetMonData(&gParties[B_TRAINER_PLAYER][0], MON_DATA_HP, &curHp);
        }
        return TRUE;
    }
    case SPECIES_GENGAR: // Curse: move 10 HP damage to opponent Active
    case SPECIES_ZAPDOS: // Peal of Thunder
    case SPECIES_ELECTRODE:
        if (oppBattler < gBattlersCount && gBattleMons[oppBattler].hp > 10)
        {
            gBattleMons[oppBattler].hp -= 10;
            SetMonData(&gParties[B_TRAINER_OPPONENT_A][gBattlerPartyIndexes[oppBattler]], MON_DATA_HP, &gBattleMons[oppBattler].hp);
        }
        return TRUE;
    default:
        // Default utility Pokémon Power: draw 1 card or grant +10 PlusPower bonus
        if (!DrawCardForPlayer())
            gTcgBattleState.plusPowerBonus[battler] += 10;
        return TRUE;
    }
}

void RunPokemonCheckup(void)
{
    for (u8 battler = 0; battler < gBattlersCount; battler++)
    {
        if (!IsBattlerAlive(battler))
            continue;

        // Poison (10 HP) and Burn (20 HP + coin flip cure) are executed via
        // HandleEndTurnPoison and HandleEndTurnBurn so healthbar animations and faint scripts run properly.

        // 3. Asleep: coin flip (Heads wakes up)
        if (gBattleMons[battler].status1 & STATUS1_SLEEP)
        {
            if (Random() & 1)
                gBattleMons[battler].status1 &= ~STATUS1_SLEEP;
        }

        // 4. Paralyzed: lasts 1 turn, cures at end of owner's turn
        if (gBattleMons[battler].status1 & STATUS1_PARALYSIS)
        {
            gBattleMons[battler].status1 &= ~STATUS1_PARALYSIS;
        }

        SetMonData(GetBattlerMon(battler), MON_DATA_HP, &gBattleMons[battler].hp);
        SetMonData(GetBattlerMon(battler), MON_DATA_STATUS, &gBattleMons[battler].status1);

        gTcgBattleState.defenderBonus[battler] = 0;
    }

    for (u8 i = 0; i < PARTY_SIZE; i++)
        gTcgBattleState.powerUsedThisTurn[i] = FALSE;

    gTcgBattleState.supporterUsedThisTurn = 0;
    gTcgBattleState.retreatedThisTurn = 0;
    gTcgBattleState.energyAttachedThisTurn = 0;
    gTcgBattleState.stagedEnergyAttached = FALSE;
    gTcgBattleState.stagedPowerQueued = FALSE;
    gTcgBattleState.stagedRetreatQueued = FALSE;
    gTcgBattleState.stagedAttackQueued = FALSE;
}

bool8 CanMonEvolveThisTurn(u8 partyIndex)
{
    if (gBattleTurnCounter == 0)
        return FALSE; // Cannot evolve on turn 1

    if (gTcgBattleState.turnMonPlaced[partyIndex] == gBattleTurnCounter)
        return FALSE; // Cannot evolve on the turn placed

    if (gTcgBattleState.turnMonEvolved[partyIndex] == gBattleTurnCounter)
        return FALSE; // Max 1 evolution per mon per turn

    return TRUE;
}

void MarkMonEvolved(u8 partyIndex)
{
    if (partyIndex < ARRAY_COUNT(gTcgBattleState.turnMonEvolved))
        gTcgBattleState.turnMonEvolved[partyIndex] = gBattleTurnCounter;
}

void MarkMonPlaced(u8 partyIndex)
{
    if (partyIndex < ARRAY_COUNT(gTcgBattleState.turnMonPlaced))
        gTcgBattleState.turnMonPlaced[partyIndex] = gBattleTurnCounter;
}

bool8 CanPlayerRetreatThisTurn(void)
{
    if (gTcgBattleState.retreatedThisTurn)
        return FALSE;

    // Must have at least 1 alive bench mon
    for (u32 i = 1; i < MAX_FIELD_POKEMON; i++)
    {
        if (GetMonData(&gParties[B_TRAINER_PLAYER][i], MON_DATA_SPECIES) != SPECIES_NONE
         && GetMonData(&gParties[B_TRAINER_PLAYER][i], MON_DATA_HP) > 0)
        {
            return TRUE;
        }
    }

    return FALSE;
}

void BuildTemporaryTrainerDeck(u16 trainerId, struct TcgDeck *destDeck)
{
    if (!destDeck)
        return;

    u16 deckIndex = 0;
    if (trainerId < TRAINERS_COUNT)
        deckIndex = gTrainerToDeckMap[trainerId];

    if (deckIndex >= gThematicDeckCount)
        deckIndex = 0;

    const struct TcgDeck *chosen = &gThematicDecks[deckIndex];
    for (u32 i = 0; i < DECK_SIZE; i++)
        destDeck->cards[i] = chosen->cards[i];
    for (u32 i = 0; i < 16; i++)
        destDeck->name[i] = chosen->name[i];
    destDeck->wallpaper = chosen->wallpaper;
}

void UnlockGymLeaderDeck(u16 trainerId)
{
    u8 deckIndex = 0xFF;
    switch (trainerId)
    {
    case TRAINER_LEADER_BROCK:
        deckIndex = 10; // Brock's Geodude / Onix deck
        break;
    case TRAINER_LEADER_MISTY:
        deckIndex = 4;  // Misty's Staryu / Starmie deck
        break;
    case TRAINER_LEADER_LT_SURGE:
        deckIndex = 8;  // Surge's Pikachu / Electabuzz deck
        break;
    case TRAINER_LEADER_ERIKA:
        deckIndex = 6;  // Erika's Oddish / Tangela deck
        break;
    case TRAINER_LEADER_KOGA:
        deckIndex = 12; // Koga's Koffing / Grimer deck
        break;
    case TRAINER_LEADER_SABRINA:
        deckIndex = 14; // Sabrina's Abra / Mr. Mime deck
        break;
    case TRAINER_LEADER_BLAINE:
        deckIndex = 3;  // Blaine's Vulpix / Magmar deck
        break;
    case TRAINER_LEADER_GIOVANNI:
    case TRAINER_BOSS_GIOVANNI:
    case TRAINER_BOSS_GIOVANNI_2:
        deckIndex = 16; // Giovanni's Rhyhorn /Kangaskhan deck
        break;
    case TRAINER_ELITE_FOUR_LORELEI:
    case TRAINER_ELITE_FOUR_LORELEI_2:
        deckIndex = 22;
        break;
    case TRAINER_ELITE_FOUR_BRUNO:
    case TRAINER_ELITE_FOUR_BRUNO_2:
        deckIndex = 24;
        break;
    case TRAINER_ELITE_FOUR_AGATHA:
    case TRAINER_ELITE_FOUR_AGATHA_2:
        deckIndex = 26;
        break;
    case TRAINER_ELITE_FOUR_LANCE:
    case TRAINER_ELITE_FOUR_LANCE_2:
        deckIndex = 28;
        break;
    case TRAINER_CHAMPION_FIRST_SQUIRTLE:
    case TRAINER_CHAMPION_FIRST_BULBASAUR:
    case TRAINER_CHAMPION_FIRST_CHARMANDER:
    case TRAINER_CHAMPION_REMATCH_SQUIRTLE:
    case TRAINER_CHAMPION_REMATCH_BULBASAUR:
    case TRAINER_CHAMPION_REMATCH_CHARMANDER:
        deckIndex = 30;
        break;
    default:
        return;
    }

    if (deckIndex < MAX_DEFAULT_DECKS)
        gSaveBlock1Ptr->unlockedDefaultDecksMask |= (1u << deckIndex);
}

void SyncBattlerStructFromPartyMon(u8 battler)
{
    if (battler >= MAX_BATTLERS_COUNT)
        return;

    struct Pokemon *mon = GetBattlerMon(battler);
    if (mon == NULL)
        return;

    enum Species species = GetMonData(mon, MON_DATA_SPECIES);
    gBattleMons[battler].species = species;
    gBattleMons[battler].item = GetMonData(mon, MON_DATA_HELD_ITEM);
    for (u32 i = 0; i < MAX_MON_MOVES; i++)
    {
        gBattleMons[battler].moves[i] = GetMonData(mon, MON_DATA_MOVE1 + i);
        gBattleMons[battler].pp[i] = GetMonData(mon, MON_DATA_PP1 + i);
    }
    gBattleMons[battler].ppBonuses = GetMonData(mon, MON_DATA_PP_BONUSES);
    gBattleMons[battler].friendship = GetMonData(mon, MON_DATA_FRIENDSHIP);
    gBattleMons[battler].experience = GetMonData(mon, MON_DATA_EXP);
    gBattleMons[battler].hpIV = GetMonData(mon, MON_DATA_HP_IV);
    gBattleMons[battler].attackIV = GetMonData(mon, MON_DATA_ATK_IV);
    gBattleMons[battler].defenseIV = GetMonData(mon, MON_DATA_DEF_IV);
    gBattleMons[battler].speedIV = GetMonData(mon, MON_DATA_SPEED_IV);
    gBattleMons[battler].spAttackIV = GetMonData(mon, MON_DATA_SPATK_IV);
    gBattleMons[battler].spDefenseIV = GetMonData(mon, MON_DATA_SPDEF_IV);
    gBattleMons[battler].personality = GetMonData(mon, MON_DATA_PERSONALITY);
    gBattleMons[battler].status1 = GetMonData(mon, MON_DATA_STATUS);
    gBattleMons[battler].level = GetMonData(mon, MON_DATA_LEVEL);
    gBattleMons[battler].hp = GetMonData(mon, MON_DATA_HP);
    gBattleMons[battler].maxHP = GetMonData(mon, MON_DATA_MAX_HP);
    gBattleMons[battler].attack = GetMonData(mon, MON_DATA_ATK);
    gBattleMons[battler].defense = GetMonData(mon, MON_DATA_DEF);
    gBattleMons[battler].speed = GetMonData(mon, MON_DATA_SPEED);
    gBattleMons[battler].spAttack = GetMonData(mon, MON_DATA_SPATK);
    gBattleMons[battler].spDefense = GetMonData(mon, MON_DATA_SPDEF);
    gBattleMons[battler].abilityNum = GetMonData(mon, MON_DATA_ABILITY_NUM);
    gBattleMons[battler].otId = GetMonData(mon, MON_DATA_OT_ID);
    GetMonData(mon, MON_DATA_NICKNAME, gBattleMons[battler].nickname);
    gBattleMons[battler].types[0] = GetSpeciesType(species, 0);
    gBattleMons[battler].types[1] = GetSpeciesType(species, 1);
    gBattleMons[battler].types[2] = TYPE_MYSTERY;
    gBattleMons[battler].ability = GetAbilityBySpecies(species, gBattleMons[battler].abilityNum);
    if (species != SPECIES_NONE && gBattleMons[battler].hp > 0)
        gAbsentBattlerFlags &= ~(1u << battler);
}
