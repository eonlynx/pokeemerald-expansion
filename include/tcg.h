#ifndef GUARD_TCG_H
#define GUARD_TCG_H

#include "global.h"
#include "constants/items.h"
#include "constants/moves.h"
#include "constants/battle_move_effects.h"
#include "constants/tcg_cards.h"

#define MOVE_RETREAT MOVE_TELEPORT

// 1-to-1 Move Effect Mappings to Existing Vanilla Move Effects (using BattleScript_EffectHit)
#define EFFECT_TCG_COIN_DAMAGE_BONUS     EFFECT_FUSION_COMBO
#define EFFECT_TCG_SELF_DAMAGE_COIN      EFFECT_RECOIL_IF_MISS
#define EFFECT_TCG_DISCARD_USER_ENERGY   EFFECT_PUNISHMENT
#define EFFECT_TCG_DISCARD_TARGET_ENERGY EFFECT_ACROBATICS
#define EFFECT_TCG_BENCH_SNIPER          EFFECT_SNIPE_SHOT
#define EFFECT_TCG_SHIELD_NEXT_TURN      EFFECT_BODY_PRESS
#define EFFECT_TCG_HEAL_USER             EFFECT_POPULATION_BOMB
#define EFFECT_TCG_DISABLE_MOVE          EFFECT_REVELATION_DANCE
#define EFFECT_TCG_BLIND_TARGET          EFFECT_TERRAIN_PULSE
#define EFFECT_TCG_DAMAGE_MULTI_COIN     EFFECT_RETALIATE
#define EFFECT_TCG_SELF_DAMAGE_FIXED     EFFECT_LASH_OUT
#define EFFECT_TCG_DRAW_CARD             EFFECT_GRASSY_GLIDE
#define EFFECT_TCG_SCALING_ENERGY        EFFECT_ROUND
#define EFFECT_TCG_SCALING_BENCH         EFFECT_ECHOED_VOICE
#define EFFECT_TCG_SCALING_DAMAGE_SELF   EFFECT_BOLT_BEAK
#define EFFECT_TCG_SCALING_DAMAGE_TARGET EFFECT_PSYSHOCK
#define EFFECT_TCG_PLUS_20_NEXT_TURN     EFFECT_HYDRO_STEAM
#define EFFECT_TCG_COIN_OR_NOTHING       EFFECT_TRUMP_CARD
#define EFFECT_TCG_DISCARD_ALL_ENERGY    EFFECT_STORED_POWER
#define EFFECT_TCG_SWITCH_OPPONENT       EFFECT_RAGE_FIST
#define EFFECT_TCG_INFLICT_POISON        EFFECT_CORROSIVE_GAS
#define EFFECT_TCG_INFLICT_SLEEP         EFFECT_DARK_VOID
#define EFFECT_TCG_INFLICT_PARALYSIS     EFFECT_TAR_SHOT
#define EFFECT_TCG_INFLICT_CONFUSION     EFFECT_CONFUSE
#define EFFECT_TCG_INFLICT_BURN          EFFECT_BEAK_BLAST
#define EFFECT_TCG_MULTI_COIN_HIT        EFFECT_TCG_DAMAGE_MULTI_COIN
#define EFFECT_TCG_FORCE_SWITCH          EFFECT_TCG_SWITCH_OPPONENT
#define EFFECT_TCG_SELFDESTRUCT          EFFECT_TCG_SELF_DAMAGE_FIXED
#define EFFECT_TCG_ENERGY_BOOST          EFFECT_TCG_SCALING_ENERGY
#define EFFECT_TCG_RAGE_DAMAGE_BOOST     EFFECT_TCG_SCALING_DAMAGE_SELF

// 1-to-1 Trainer Item & Supporter Mappings to Existing Vanilla Items
#define ITEM_TCG_PROF_OAK                ITEM_LINKING_CORD
#define ITEM_TCG_BILL                    ITEM_EXP_SHARE
#define ITEM_TCG_SWITCH                  ITEM_ESCAPE_ROPE
#define ITEM_TCG_GUST_OF_WIND            ITEM_EJECT_BUTTON
#define ITEM_TCG_ENERGY_REMOVAL          ITEM_REPEL
#define ITEM_TCG_SUPER_ENERGY_REMOVAL    ITEM_SUPER_REPEL
#define ITEM_TCG_PLUSPOWER               ITEM_X_ATTACK
#define ITEM_TCG_DEFENDER                ITEM_X_DEFENSE
#define ITEM_TCG_SCOOP_UP                ITEM_EJECT_PACK
#define ITEM_TCG_SUPER_SCOOP_UP          ITEM_AIR_BALLOON
#define ITEM_TCG_COMPUTER_SEARCH         ITEM_UPGRADE
#define ITEM_TCG_GAMBLER                 ITEM_LUCKY_EGG
#define ITEM_TCG_MAINTENANCE             ITEM_LEFTOVERS
#define ITEM_TCG_ITEM_FINDER             ITEM_SCOPE_LENS
#define ITEM_TCG_DEVOLUTION_SPRAY        ITEM_EVERSTONE
#define ITEM_TCG_CLEFAIRY_DOLL           ITEM_POKE_DOLL
#define ITEM_TCG_MYSTERIOUS_FOSSIL       ITEM_ROOT_FOSSIL
#define ITEM_TCG_POKEMON_TRADER          ITEM_CLEANSE_TAG
#define ITEM_TCG_POKEMON_BREEDER         ITEM_SOOTHE_BELL
#define ITEM_TCG_POKEMON_CENTER          ITEM_MOOMOO_MILK
#define ITEM_TCG_LASS                    ITEM_DESTINY_KNOT
#define ITEM_TCG_MR_FUJI                 ITEM_SACRED_ASH
#define ITEM_TCG_IMPOSTER_PROF_OAK       ITEM_ODD_INCENSE
#define ITEM_TCG_IMPOSTER_OAK_REVENGE    ITEM_SMOKE_BALL
#define ITEM_TCG_RECYCLE                 ITEM_ETHER
#define ITEM_TCG_NIGHTLY_GARBAGE_RUN     ITEM_FULL_RESTORE
#define ITEM_TCG_ROCKET_SNEAK_ATTACK     ITEM_BLACK_GLASSES
#define ITEM_TCG_HERE_COMES_TEAM_ROCKET  ITEM_RAZOR_CLAW
#define ITEM_TCG_ROCKET_TRAP             ITEM_IRON_BALL
#define ITEM_TCG_BOSS_WAY                ITEM_KINGS_ROCK
#define ITEM_TCG_GOOP_GAS_ATTACK         ITEM_TOXIC_ORB
#define ITEM_TCG_BILLS_TELEPORTER        ITEM_AMULET_COIN
#define ITEM_TCG_BILLS_PC                ITEM_DUBIOUS_DISC
#define ITEM_TCG_CHALLENGE               ITEM_CHOICE_BAND
#define ITEM_TCG_SLEEP                   ITEM_FLAME_ORB
#define ITEM_TCG_COMPUTER_ERROR          ITEM_RED_CARD
#define ITEM_TCG_DIGGER                  ITEM_SOFT_SAND
#define ITEM_TCG_FOSSIL_EXCAVATION       ITEM_CLAW_FOSSIL
#define ITEM_TCG_IMAKUNI                 ITEM_FOCUS_BAND
#define ITEM_TCG_POKEMON_RETRANSFER      ITEM_METAL_COAT
#define ITEM_TCG_POKE_RECEIVER           ITEM_LIGHT_BALL
#define ITEM_TCG_POKEDEX                 ITEM_DEEP_SEA_TOOTH
#define ITEM_TCG_MASTER_RECEIVER         ITEM_DEEP_SEA_SCALE
#define ITEM_TCG_POKEMON_FLUTE           ITEM_BLUE_FLUTE

enum TcgCardType {
    CARD_TYPE_POKEMON_BASIC,
    CARD_TYPE_POKEMON_STAGE1,
    CARD_TYPE_POKEMON_STAGE2,
    CARD_TYPE_TRAINER_ITEM,
    CARD_TYPE_TRAINER_SUPPORTER,
};

enum TcgEnergyType {
    ENERGY_GRASS,     // 'G'
    ENERGY_FIRE,      // 'R' (Red / Fire)
    ENERGY_WATER,     // 'W'
    ENERGY_LIGHTNING, // 'L'
    ENERGY_PSYCHIC,   // 'P'
    ENERGY_FIGHTING,  // 'F' (Fighting)
    ENERGY_DARKNESS,  // 'D'
    ENERGY_METAL,     // 'M'
    ENERGY_COLORLESS, // 'C'
    NUM_ENERGY_TYPES
};

struct TcgAttackCost {
    u8 energyCount[NUM_ENERGY_TYPES];
};

struct TcgCardInfo {
    u16 cardId;              // Visible card ID (#121)
    const u8 *name;
    u16 species;             // Associated Gen 3 species (SPECIES_NONE for trainers)
    u16 preEvoSpecies;       // Required pre-evolution species on field (Stage 1/2)
    u16 equivItemId;         // Equivalent overworld / bag item ID (e.g. ITEM_POTION)
    u8 cardType;             // enum TcgCardType
    u8 energyType;           // Elemental energy type of the card
    u8 weaknessType;         // Elemental weakness type (+20 damage)
    u8 retreatCost;          // Retreat cost in colorless energy
    u16 maxHp;               // Fixed card HP
    u16 pokemonPowerId;      // Pokémon Power ID (occupies Slot 1 if != 0)
    const u8 *powerName;     // Pokémon Power name
    const u8 *powerDescription; // Pokémon Power 2-line description
    u16 move1;               // Move 1
    u16 move2;               // Move 2
    u8 move1Damage;          // Flat card attack 1 damage
    u8 move2Damage;          // Flat card attack 2 damage
    u16 move1Effect;         // Specific TCG move 1 effect (EFFECT_TCG_* or status)
    u16 move2Effect;         // Specific TCG move 2 effect (EFFECT_TCG_* or status)
    const u8 *move1Name;     // Card-specific attack 1 name
    const u8 *move1Description; // Card-specific attack 1 description
    const u8 *move2Name;     // Card-specific attack 2 name
    const u8 *move2Description; // Card-specific attack 2 description
    struct TcgAttackCost move1Cost;
    struct TcgAttackCost move2Cost;
    u8 encounterWeight;      // Wild encounter rarity weight (lower = rarer)
    bool8 isRareShiny;       // TRUE: renders shiny sprite & awards 2 prize points
    const u8 *description;
};

#define DECK_SIZE 20
#define TCG_DECK_SIZE DECK_SIZE
#define MAX_CUSTOM_DECKS 14
#define MAX_DEFAULT_DECKS 32
#define MAX_BENCH_SLOTS 3
#define MAX_FIELD_POKEMON 4

#define DEFAULT_DECK_BULBASAUR  0
#define DEFAULT_DECK_CHARMANDER 2
#define DEFAULT_DECK_SQUIRTLE   4

enum TcgPcStorageMode {
    TCG_PC_MODE_VIEW_ONLY = 0,
    TCG_PC_MODE_CURRENT_DECK,
    TCG_PC_MODE_DEFAULT_DECKS,
    TCG_PC_MODE_CUSTOM_DECKS,
};

struct TcgBattleState {
    u8 playerPrizePoints;
    u8 opponentPrizePoints;
    u8 playerPrizeTarget;
    u8 opponentPrizeTarget;
    u8 playerEnergyPool[NUM_ENERGY_TYPES];
    u8 opponentEnergyPool[NUM_ENERGY_TYPES];
    u8 playerDeckEnergyTypes[NUM_ENERGY_TYPES];
    u8 numPlayerDeckEnergyTypes;
    u8 opponentDeckEnergyTypes[NUM_ENERGY_TYPES];
    u8 numOpponentDeckEnergyTypes;
    u8 lastGeneratedEnergyType[NUM_BATTLE_SIDES];
    u8 nextGeneratedEnergyType[NUM_BATTLE_SIDES];
    u8 activeEnergyCount[MAX_BATTLERS_COUNT];
    u8 slotEnergyCount[NUM_BATTLE_SIDES][PARTY_SIZE];
    u8 slotEnergyByType[NUM_BATTLE_SIDES][PARTY_SIZE][NUM_ENERGY_TYPES];
    u8 retreatedThisTurn:1;
    u8 energyAttachedThisTurn:1;
    u8 supporterUsedThisTurn:1;
    u8 firstTurnFirstPlayer:1;
    u8 activeMonPlaced:1;
    u8 energyGeneratedThisTurn:1;
    u8 viewingHandInPartyMenu:1;
    u8 turnMonPlaced[PARTY_SIZE * 2];
    u8 turnMonEvolved[PARTY_SIZE * 2];
    bool8 powerUsedThisTurn[PARTY_SIZE];
    bool8 goopGasActive[NUM_BATTLE_SIDES];
    u16 playerHand[10];
    u8 playerHandCount;
    u16 opponentHand[10];
    u8 opponentHandCount;
    u16 playerDeckRemaining[DECK_SIZE];
    u8 playerDeckRemainingCount;
    u16 opponentDeckRemaining[DECK_SIZE];
    u8 opponentDeckRemainingCount;
    u16 playerDiscardPile[DECK_SIZE];
    u8 playerDiscardCount;
    u16 opponentDiscardPile[DECK_SIZE];
    u8 opponentDiscardCount;
    u8 plusPowerBonus[MAX_BATTLERS_COUNT];
    u8 defenderBonus[MAX_BATTLERS_COUNT];
    // Staged Turn Action Queue (PLAY sub-menu -> executed on END TURN)
    bool8 stagedEnergyAttached;
    u8 stagedEnergyTargetSlot;
    bool8 stagedPowerQueued;
    u8 stagedPowerSlot;
    bool8 stagedRetreatQueued;
    u8 stagedRetreatBenchSlot;
    bool8 stagedAttackQueued;
    u8 stagedAttackMoveSlot;
    u8 handScrollOffset;
    u8 pcStorageMode;
    u8 selectedFieldSide;
    u8 selectedFieldSlot;
    u8 fieldTargetBlinkState;
};

extern struct TcgBattleState gTcgBattleState;
extern const struct TcgCardInfo gTcgCards[];
extern const u16 gTcgCardCount;
extern const struct TcgDeck gDefaultDecks[MAX_DEFAULT_DECKS];
extern const u16 gDefaultDeckCount;
extern const struct TcgDeck gThematicDecks[];
extern const u16 gThematicDeckCount;

const struct TcgCardInfo *GetTcgCardInfo(u16 cardId);
void CreateTempMonFromCardId(struct Pokemon *mon, u16 cardId);
u16 GetMonCardId(const struct Pokemon *mon);
void SetMonCardId(struct Pokemon *mon, u16 cardId);
u16 GetCardIdFromSpecies(u16 species);
u16 GetCardIdFromItemId(u16 itemId);

u16 GetCardQuantityInBag(u16 cardId);
u16 CountCardIdInDeck(const struct TcgDeck *deck, u16 cardId);
bool8 ValidateDeck(const struct TcgDeck *deck);
void InitTcgSaveData(void);
void InitTcgBattleState(void);
void GenerateTurnEnergy(u8 side);
void RunPokemonCheckup(void);
bool8 CanMonEvolveThisTurn(u8 partyIndex);
void MarkMonEvolved(u8 partyIndex);
void MarkMonPlaced(u8 partyIndex);
bool8 CanPlayerRetreatThisTurn(void);
void BuildTemporaryTrainerDeck(u16 trainerId, struct TcgDeck *destDeck);
void UnlockGymLeaderDeck(u16 trainerId);
bool8 CanPlayerUseFieldHm(u16 itemHmId, u16 badgeFlag);
void GiveStarterDeck(u8 starterNum);
void Script_GiveStarterDeck(void);
bool8 ExecuteTrainerCardEffect(u16 cardId, u8 battler);
bool8 ExecutePokemonPower(u16 cardId, u8 slot, u8 battler);
bool8 HasEnoughEnergyForAttack(u8 side, u8 slot, const struct TcgAttackCost *cost);
void AttachTurnEnergyToSlot(u8 side, u8 slot);
void DiscardEnergyFromSlot(u8 side, u8 slot, u8 count);
void SwapSlotEnergies(u8 side, u8 slotA, u8 slotB);
void RecordDiscardedCard(u8 side, u16 cardId);
bool8 DrawCardForPlayer(void);
bool8 DrawCardForOpponent(void);
void RemoveCardFromPlayerHandAt(u8 handIndex);
bool8 TryPlaceOrEvolveFromHand(u8 handIndex, u8 *outFieldSlot, bool8 *outEvolved);
void SyncBattlerStructFromPartyMon(u8 battler);
void EnsureStarterDeckCardsInBag(void);
void SyncCurrentDeckToBox0(void);
void SyncBox0ToCurrentDeck(void);
void SyncDefaultDecksToBoxes(void);
void SyncCustomDecksToBoxes(void);
void SaveBoxesToCustomDecks(void);
u8 GetUnlockedDefaultDeckIndexForBox(u8 boxId);
bool8 CanBuildDefaultDeck(u8 deckIndex);
bool8 CanBuildCustomDeck(const struct TcgDeck *deck);
bool8 TryAddCardToCustomDeckBox(u8 boxId, u16 cardId);
void RestorePlayerPartyAfterBattle(void);
void UpdateTcgBenchHealthboxes(void);

#endif // GUARD_TCG_H
