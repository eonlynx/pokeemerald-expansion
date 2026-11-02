#include "global.h"
#include "malloc.h"
#include "battle.h"
#include "battle_tower.h"
#include "battle_setup.h"
#include "ereader_helpers.h"
#include "event_data.h"
#include "event_scripts.h"
#include "frontier_util.h"
#include "fieldmap.h"
#include "field_message_box.h"
#include "international_string_util.h"
#include "item.h"
#include "main.h"
#include "menu.h"
#include "overworld.h"
#include "palette.h"
#include "pokemon.h"
#include "random.h"
#include "script.h"
#include "string_util.h"
#include "strings.h"
#include "text.h"
#include "trainer_hill.h"
#include "tv.h"
#include "window.h"
#include "util.h"
#include "constants/battle_ai.h"
#include "constants/event_object_movement.h"
#include "constants/event_objects.h"
#include "constants/items.h"
#include "constants/battle_frontier.h"
#include "constants/layouts.h"
#include "constants/moves.h"
#include "constants/trainers.h"
#include "constants/trainer_hill.h"
#include "constants/trainer_types.h"

struct FloorTrainers
{
    u8 name[HILL_TRAINERS_PER_FLOOR][TRAINER_NAME_LENGTH + 1];
    u8 facilityClass[HILL_TRAINERS_PER_FLOOR];
};

static EWRAM_DATA struct {
    u8 floorId;
    struct TrainerHillChallenge challenge;
    struct TrainerHillFloor floors[NUM_TRAINER_HILL_FLOORS];
} *sHillData = NULL;

static EWRAM_DATA struct FloorTrainers *sFloorTrainers = NULL;
EWRAM_DATA u32 *gTrainerHillVBlankCounter = NULL;

// This file's functions.
static void TrainerHillStartChallenge(void);
static void GetOwnerState(void);
static void GiveChallengePrize(void);
static void CheckFinalTime(void);
static void TrainerHillResumeTimer(void);
static void TrainerHillSetPlayerLost(void);
static void TrainerHillGetChallengeStatus(void);
static void BufferChallengeTime(void);
static void GetAllFloorsUsed(void);
static void GetInEReaderMode(void);
static void IsTrainerHillChallengeActive(void);
static void ShowTrainerHillPostBattleText(void);
static void SetAllTrainerFlags(void);
static void GetGameSaved(void);
static void SetGameSaved(void);
static void ClearGameSaved(void);
static void GetChallengeWon(void);
static void TrainerHillSetMode(void);
static void TrainerHillGetPartyMaxLevel(void);
static void TrainerHillSetLvlMode(void);
static void TrainerHillCheckFrontierBrain(void);
static void TrainerHillGiveBrainPrize(void);
static void TrainerHillGetSpokeToOwner(void);
static void TrainerHillSetRoofSpectatorGraphics(void);
static void TrainerHillBufferModeName(void);
static void TrainerHillSaveChallenge(void);
static void TrainerHillRetire(void);
static void SetUpDataStruct(void);
static void FreeDataStruct(void);
static void TrainerHillDummy(void);
#if FREE_TRAINER_HILL == FALSE
static void SetTimerValue(u32 *dst, u32 val);
static u32 GetTimerValue(u32 *src);
#endif //FREE_TRAINER_HILL
void SetTrainerHillMonLevel(struct Pokemon *mon, u8 level);

// const data
#include "data/battle_frontier/trainer_hill.h"

struct
{
    u8 trainerClass;
    u8 musicId;
} static const sTrainerClassesAndMusic[] =
{
    {TRAINER_CLASS_TEAM_AQUA, TRAINER_ENCOUNTER_MUSIC_AQUA},
    {TRAINER_CLASS_AQUA_ADMIN, TRAINER_ENCOUNTER_MUSIC_AQUA},
    {TRAINER_CLASS_AQUA_LEADER, TRAINER_ENCOUNTER_MUSIC_AQUA},
    {TRAINER_CLASS_AROMA_LADY, TRAINER_ENCOUNTER_MUSIC_FEMALE},
    {TRAINER_CLASS_BATTLE_GIRL, TRAINER_ENCOUNTER_MUSIC_INTENSE},
    {TRAINER_CLASS_SWIMMER_F, TRAINER_ENCOUNTER_MUSIC_FEMALE},
    {TRAINER_CLASS_POKEFAN, TRAINER_ENCOUNTER_MUSIC_TWINS},
    {TRAINER_CLASS_DRAGON_TAMER, TRAINER_ENCOUNTER_MUSIC_INTENSE},
    {TRAINER_CLASS_COOLTRAINER, TRAINER_ENCOUNTER_MUSIC_COOL},
    {TRAINER_CLASS_GUITARIST, TRAINER_ENCOUNTER_MUSIC_INTENSE},
    {TRAINER_CLASS_SAILOR, TRAINER_ENCOUNTER_MUSIC_MALE},
    {TRAINER_CLASS_TWINS, TRAINER_ENCOUNTER_MUSIC_TWINS},
    {TRAINER_CLASS_INTERVIEWER, TRAINER_ENCOUNTER_MUSIC_INTERVIEWER},
    {TRAINER_CLASS_RUIN_MANIAC, TRAINER_ENCOUNTER_MUSIC_HIKER},
    {TRAINER_CLASS_GENTLEMAN, TRAINER_ENCOUNTER_MUSIC_RICH},
    {TRAINER_CLASS_SWIMMER_M, TRAINER_ENCOUNTER_MUSIC_FEMALE},
    {TRAINER_CLASS_POKEMANIAC, TRAINER_ENCOUNTER_MUSIC_SUSPICIOUS},
    {TRAINER_CLASS_BLACK_BELT, TRAINER_ENCOUNTER_MUSIC_INTENSE},
    {TRAINER_CLASS_OLD_COUPLE, TRAINER_ENCOUNTER_MUSIC_INTENSE},
    {TRAINER_CLASS_BUG_MANIAC, TRAINER_ENCOUNTER_MUSIC_SUSPICIOUS},
    {TRAINER_CLASS_CAMPER, TRAINER_ENCOUNTER_MUSIC_MALE},
    {TRAINER_CLASS_KINDLER, TRAINER_ENCOUNTER_MUSIC_HIKER},
    {TRAINER_CLASS_TEAM_MAGMA, TRAINER_ENCOUNTER_MUSIC_MAGMA},
    {TRAINER_CLASS_MAGMA_ADMIN, TRAINER_ENCOUNTER_MUSIC_MAGMA},
    {TRAINER_CLASS_MAGMA_LEADER, TRAINER_ENCOUNTER_MUSIC_MAGMA},
    {TRAINER_CLASS_LASS, TRAINER_ENCOUNTER_MUSIC_FEMALE},
    {TRAINER_CLASS_BUG_CATCHER, TRAINER_ENCOUNTER_MUSIC_MALE},
    {TRAINER_CLASS_NINJA_BOY, TRAINER_ENCOUNTER_MUSIC_SUSPICIOUS},
    {TRAINER_CLASS_RICH_BOY, TRAINER_ENCOUNTER_MUSIC_RICH},
    {TRAINER_CLASS_HEX_MANIAC, TRAINER_ENCOUNTER_MUSIC_SUSPICIOUS},
    {TRAINER_CLASS_BEAUTY, TRAINER_ENCOUNTER_MUSIC_FEMALE},
    {TRAINER_CLASS_LADY, TRAINER_ENCOUNTER_MUSIC_FEMALE},
    {TRAINER_CLASS_PARASOL_LADY, TRAINER_ENCOUNTER_MUSIC_FEMALE},
    {TRAINER_CLASS_PICNICKER, TRAINER_ENCOUNTER_MUSIC_GIRL},
    {TRAINER_CLASS_PKMN_BREEDER, TRAINER_ENCOUNTER_MUSIC_FEMALE},
    {TRAINER_CLASS_COLLECTOR, TRAINER_ENCOUNTER_MUSIC_SUSPICIOUS},
    {TRAINER_CLASS_PKMN_RANGER, TRAINER_ENCOUNTER_MUSIC_COOL},
    {TRAINER_CLASS_RIVAL, TRAINER_ENCOUNTER_MUSIC_MALE},
    {TRAINER_CLASS_YOUNG_COUPLE, TRAINER_ENCOUNTER_MUSIC_GIRL},
    {TRAINER_CLASS_PSYCHIC, TRAINER_ENCOUNTER_MUSIC_INTENSE},
    {TRAINER_CLASS_SR_AND_JR, TRAINER_ENCOUNTER_MUSIC_TWINS},
    {TRAINER_CLASS_ELITE_FOUR, TRAINER_ENCOUNTER_MUSIC_FEMALE},
    {TRAINER_CLASS_YOUNGSTER, TRAINER_ENCOUNTER_MUSIC_MALE},
    {TRAINER_CLASS_EXPERT, TRAINER_ENCOUNTER_MUSIC_INTENSE},
    {TRAINER_CLASS_TRIATHLETE, TRAINER_ENCOUNTER_MUSIC_MALE},
    {TRAINER_CLASS_BIRD_KEEPER, TRAINER_ENCOUNTER_MUSIC_COOL},
    {TRAINER_CLASS_FISHERMAN, TRAINER_ENCOUNTER_MUSIC_HIKER},
    {TRAINER_CLASS_CHAMPION, TRAINER_ENCOUNTER_MUSIC_MALE},
    {TRAINER_CLASS_TUBER_M, TRAINER_ENCOUNTER_MUSIC_MALE},
    {TRAINER_CLASS_TUBER_F, TRAINER_ENCOUNTER_MUSIC_GIRL},
    {TRAINER_CLASS_SIS_AND_BRO, TRAINER_ENCOUNTER_MUSIC_SWIMMER},
    {TRAINER_CLASS_HIKER, TRAINER_ENCOUNTER_MUSIC_HIKER},
    {TRAINER_CLASS_LEADER, TRAINER_ENCOUNTER_MUSIC_FEMALE},
    {TRAINER_CLASS_SCHOOL_KID, TRAINER_ENCOUNTER_MUSIC_MALE},
};

static const u16 sEReader_Pal[] = INCGFX_U16("graphics/trainer_hill/ereader.pal", ".gbapal");
static const u8 sRecordWinColors[] = {TEXT_COLOR_TRANSPARENT, TEXT_COLOR_DARK_GRAY, TEXT_COLOR_LIGHT_GRAY};

static const struct TrainerHillChallenge *const sChallengeData[NUM_TRAINER_HILL_MODES] =
{
    [HILL_MODE_NORMAL]  = &sChallenge_Normal,
    [HILL_MODE_VARIETY] = &sChallenge_Variety,
    [HILL_MODE_UNIQUE]  = &sChallenge_Unique,
    [HILL_MODE_EXPERT]  = &sChallenge_Expert,
};

static const struct TrainerHillFloor *const UNUSED sFloorData[NUM_TRAINER_HILL_MODES] =
{
    [HILL_MODE_NORMAL]  = &sFloors_Normal[0],
    [HILL_MODE_VARIETY] = &sFloors_Variety[0],
    [HILL_MODE_UNIQUE]  = &sFloors_Unique[0],
    [HILL_MODE_EXPERT]  = &sFloors_Expert[0],
};

// Unused.
static const u8 *const sFloorStrings[] =
{
    gText_TrainerHill1F,
    gText_TrainerHill2F,
    gText_TrainerHill3F,
    gText_TrainerHill4F,
};

static void (*const sHillFunctions[])(void) =
{
    [TRAINER_HILL_FUNC_START]                 = TrainerHillStartChallenge,
    [TRAINER_HILL_FUNC_GET_OWNER_STATE]       = GetOwnerState,
    [TRAINER_HILL_FUNC_GIVE_PRIZE]            = GiveChallengePrize,
    [TRAINER_HILL_FUNC_CHECK_FINAL_TIME]      = CheckFinalTime,
    [TRAINER_HILL_FUNC_RESUME_TIMER]          = TrainerHillResumeTimer,
    [TRAINER_HILL_FUNC_SET_LOST]              = TrainerHillSetPlayerLost,
    [TRAINER_HILL_FUNC_GET_CHALLENGE_STATUS]  = TrainerHillGetChallengeStatus,
    [TRAINER_HILL_FUNC_GET_CHALLENGE_TIME]    = BufferChallengeTime,
    [TRAINER_HILL_FUNC_GET_ALL_FLOORS_USED]   = GetAllFloorsUsed,
    [TRAINER_HILL_FUNC_GET_IN_EREADER_MODE]   = GetInEReaderMode,
    [TRAINER_HILL_FUNC_IN_CHALLENGE]          = IsTrainerHillChallengeActive,
    [TRAINER_HILL_FUNC_POST_BATTLE_TEXT]      = ShowTrainerHillPostBattleText,
    [TRAINER_HILL_FUNC_SET_ALL_TRAINER_FLAGS] = SetAllTrainerFlags,
    [TRAINER_HILL_FUNC_GET_GAME_SAVED]        = GetGameSaved,
    [TRAINER_HILL_FUNC_SET_GAME_SAVED]        = SetGameSaved,
    [TRAINER_HILL_FUNC_CLEAR_GAME_SAVED]      = ClearGameSaved,
    [TRAINER_HILL_FUNC_GET_WON]               = GetChallengeWon,
    [TRAINER_HILL_FUNC_SET_MODE]              = TrainerHillSetMode,
    [TRAINER_HILL_FUNC_GET_PARTY_MAX_LEVEL]   = TrainerHillGetPartyMaxLevel,
    [TRAINER_HILL_FUNC_SET_LVL_MODE]          = TrainerHillSetLvlMode,
    [TRAINER_HILL_FUNC_CHECK_BRAIN]           = TrainerHillCheckFrontierBrain,
    [TRAINER_HILL_FUNC_GIVE_BRAIN_PRIZE]      = TrainerHillGiveBrainPrize,
    [TRAINER_HILL_FUNC_GET_SPOKE_TO_OWNER]    = TrainerHillGetSpokeToOwner,
    [TRAINER_HILL_FUNC_SET_SPECTATOR_GFX]     = TrainerHillSetRoofSpectatorGraphics,
    [TRAINER_HILL_FUNC_BUFFER_MODE_NAME]      = TrainerHillBufferModeName,
    [TRAINER_HILL_FUNC_SAVE_CHALLENGE]        = TrainerHillSaveChallenge,
    [TRAINER_HILL_FUNC_RETIRE]                = TrainerHillRetire,
};

static const u8 *const sModeStrings[NUM_TRAINER_HILL_MODES] =
{
    [HILL_MODE_NORMAL]  = gText_NormalTagMatch,
    [HILL_MODE_VARIETY] = gText_VarietyTagMatch,
    [HILL_MODE_UNIQUE]  = gText_UniqueTagMatch,
    [HILL_MODE_EXPERT]  = gText_ExpertTagMatch,
};

static const struct ObjectEventTemplate sTrainerObjectEventTemplate =
{
    .graphicsId = OBJ_EVENT_GFX_RIVAL_BRENDAN_NORMAL,
    .elevation = ELEVATION_DEFAULT,
    .movementType = MOVEMENT_TYPE_LOOK_AROUND,
    .movementRangeX = 1,
    .movementRangeY = 1,
    .trainerType = TRAINER_TYPE_NORMAL,
};

static const u32 sNextFloorMapNum[NUM_TRAINER_HILL_FLOORS] =
{
    [TRAINER_HILL_1F - 1] = MAP_NUM(MAP_TRAINER_HILL_2F),
    [TRAINER_HILL_2F - 1] = MAP_NUM(MAP_TRAINER_HILL_3F),
    [TRAINER_HILL_3F - 1] = MAP_NUM(MAP_TRAINER_HILL_4F),
    [TRAINER_HILL_4F - 1] = MAP_NUM(MAP_TRAINER_HILL_ROOF)
};
static const u8 UNUSED sTrainerPartySlots[HILL_TRAINERS_PER_FLOOR][PARTY_SIZE / 2] =
{
    {0, 1, 2},
    {3, 4, 5}
};

void CallTrainerHillFunction(void)
{
    SetUpDataStruct();
    sHillFunctions[gSpecialVar_0x8004]();
    FreeDataStruct();
}

void ResetTrainerHillResults(void)
{
#if FREE_TRAINER_HILL == FALSE
    s32 i, j;
#endif //FREE_TRAINER_HILL

    gSaveBlock2Ptr->frontier.savedGame = 0;
    gSaveBlock2Ptr->frontier.unk_EF9 = 0;
#if FREE_TRAINER_HILL == FALSE
    gSaveBlock1Ptr->trainerHill.bestTime = 0;
    for (i = 0; i < NUM_TRAINER_HILL_MODES; i++)
    {
        SetTimerValue(&gSaveBlock1Ptr->trainerHillTimes[i], HILL_MAX_TIME);
        for (j = 0; j < FRONTIER_LVL_MODE_COUNT; j++)
        {
            SetTimerValue(&gSaveBlock1Ptr->trainerHill.recordTimes[i][j], HILL_MAX_TIME);
            SetTimerValue(&gSaveBlock1Ptr->trainerHill.prevTimes[i][j], HILL_MAX_TIME);
            gSaveBlock1Ptr->trainerHill.recordStreaks[i][j] = 0;
            gSaveBlock1Ptr->trainerHill.prevStreaks[i][j] = 0;
            gSaveBlock1Ptr->trainerHill.winStreaks[i][j] = 0;
            gSaveBlock1Ptr->trainerHill.timesCleared[i][j] = 0;
        }
    }
    memset(gSaveBlock1Ptr->trainerHill.prevFirstTrainers, 0xFF, sizeof(gSaveBlock1Ptr->trainerHill.prevFirstTrainers));
    memset(gSaveBlock1Ptr->trainerHill.currentFloorTrainers, 0xFF, sizeof(gSaveBlock1Ptr->trainerHill.currentFloorTrainers));
    gSaveBlock1Ptr->trainerHill.gaugeCredits = 0;
    gSaveBlock1Ptr->trainerHill.hasDefeatedSilver = FALSE;
    gSaveBlock1Ptr->trainerHill.hasDefeatedGold = FALSE;
    gSaveBlock1Ptr->trainerHill.nextBrainThreshold = 200;
    gSaveBlock1Ptr->trainerHill.runBP = 0;
#endif //FREE_TRAINER_HILL
}

static u8 GetFloorId(void)
{
    return gMapHeader.mapLayoutId - LAYOUT_TRAINER_HILL_1F;
}

enum TrainerClassID GetTrainerHillOpponentClass(u16 trainerId)
{
    u8 id = trainerId - 1;

    return gFacilityClassToTrainerClass[sFloorTrainers->facilityClass[id]];
}

void GetTrainerHillTrainerName(u8 *dst, u16 trainerId)
{
    s32 i;
    u8 id = trainerId - 1;

    for (i = 0; i < TRAINER_NAME_LENGTH + 1; i++)
        dst[i] = sFloorTrainers->name[id][i];
}

u8 GetTrainerHillTrainerFrontSpriteId(u16 trainerId)
{
    u8 id, facilityClass;

    SetUpDataStruct();
    id = trainerId - 1;
    facilityClass = sHillData->floors[sHillData->floorId].trainers[id].facilityClass;
    FreeDataStruct();

    return gFacilityClassToPicIndex[facilityClass];
}

void InitTrainerHillBattleStruct(void)
{
    s32 i, j;

    SetUpDataStruct();
    sFloorTrainers = AllocZeroed(sizeof(*sFloorTrainers));

    for (i = 0; i < HILL_TRAINERS_PER_FLOOR; i++)
    {
        for (j = 0; j < TRAINER_NAME_LENGTH + 1; j++)
            sFloorTrainers->name[i][j] = sHillData->floors[sHillData->floorId].trainers[i].name[j];

        sFloorTrainers->facilityClass[i] = sHillData->floors[sHillData->floorId].trainers[i].facilityClass;
    }
#if FREE_TRAINER_HILL == FALSE
    if (!gSaveBlock1Ptr->trainerHill.spokeToOwner && gSaveBlock1Ptr->trainerHill.timer < HILL_MAX_TIME)
        SetTrainerHillVBlankCounter(&gSaveBlock1Ptr->trainerHill.timer);
#endif //FREE_TRAINER_HILL
    FreeDataStruct();
}

void FreeTrainerHillBattleStruct(void)
{
    TRY_FREE_AND_SET_NULL(sFloorTrainers);
}

#if FREE_TRAINER_HILL == FALSE
static void GenerateTrainerHillChallenge(u8 mode)
{
    u8 f, i, j;
    u8 t1Count = 0;
    u8 t2Count = 0;
    u8 eligibleT1[17];
    u8 eligibleT2[17];
    u8 chosenT1[NUM_TRAINER_HILL_FLOORS];
    u8 chosenT2[NUM_TRAINER_HILL_FLOORS];
    bool8 chosen[17];
    const struct TrainerHillCandidate *pool;

    if (mode >= NUM_TRAINER_HILL_MODES)
        mode = HILL_MODE_NORMAL;

    pool = sTrainerHillCandidates[mode];

    for (i = 0; i < 17; i++)
        chosen[i] = FALSE;

    // 1. Collect candidates eligible to be Trainer 1 (First trainer on floor; provides the map layout)
    // Must have a valid map (hasMap == TRUE).
    // Must NOT have been chosen as Trainer 1 in the previous challenge of this mode.
    for (i = 0; i < 17; i++)
    {
        bool8 usedPreviously;

        if (!pool[i].hasMap)
            continue;

        usedPreviously = FALSE;
        for (j = 0; j < NUM_TRAINER_HILL_FLOORS; j++)
        {
            if (gSaveBlock1Ptr->trainerHill.prevFirstTrainers[mode][j] == i)
            {
                usedPreviously = TRUE;
                break;
            }
        }
        if (!usedPreviously)
            eligibleT1[t1Count++] = i;
    }

    // Safety fallback: if fewer than 4 eligible (e.g. uninitialized save), allow any candidate with map
    if (t1Count < NUM_TRAINER_HILL_FLOORS)
    {
        t1Count = 0;
        for (i = 0; i < 17; i++)
        {
            if (pool[i].hasMap)
                eligibleT1[t1Count++] = i;
        }
    }

    // Randomly select 4 distinct Trainer 1s from eligibleT1
    for (f = 0; f < NUM_TRAINER_HILL_FLOORS; f++)
    {
        u8 idx = Random() % t1Count;
        u8 cand = eligibleT1[idx];
        chosen[cand] = TRUE;
        gSaveBlock1Ptr->trainerHill.prevFirstTrainers[mode][f] = cand;
        if (pool[cand].altTrainer != NULL && (Random() & 1))
            chosenT1[f] = cand | 0x80;
        else
            chosenT1[f] = cand;
        eligibleT1[idx] = eligibleT1[--t1Count];
    }

    // 2. Collect candidates eligible to be Trainer 2 (Second trainer on floor)
    // Any candidate (0..16) not chosen as Trainer 1 in this challenge.
    // (Can include previous run's Trainer 1s, and candidates without maps such as 58 and 64).
    for (i = 0; i < 17; i++)
    {
        if (!chosen[i])
            eligibleT2[t2Count++] = i;
    }

    // Randomly select 4 distinct Trainer 2s from eligibleT2
    for (f = 0; f < NUM_TRAINER_HILL_FLOORS; f++)
    {
        u8 idx = Random() % t2Count;
        u8 cand = eligibleT2[idx];
        chosen[cand] = TRUE;
        if (pool[cand].altTrainer != NULL && (Random() & 1))
            chosenT2[f] = cand | 0x80;
        else
            chosenT2[f] = cand;
        eligibleT2[idx] = eligibleT2[--t2Count];
    }

    // Save chosen trainers to SaveBlock
    for (f = 0; f < NUM_TRAINER_HILL_FLOORS; f++)
    {
        gSaveBlock1Ptr->trainerHill.currentFloorTrainers[f][0] = chosenT1[f];
        gSaveBlock1Ptr->trainerHill.currentFloorTrainers[f][1] = chosenT2[f];
    }

    // 3. Shuffle Pokémon for each of the 8 chosen trainers
    for (f = 0; f < NUM_TRAINER_HILL_FLOORS; f++)
    {
        for (j = 0; j < HILL_TRAINERS_PER_FLOOR; j++)
        {
            u8 candIdx = gSaveBlock1Ptr->trainerHill.currentFloorTrainers[f][j] & 0x7F;
            const struct TrainerHillTrainer *tr = &pool[candIdx].trainer;
            u8 validMons[PARTY_SIZE];
            u8 numValid = 0;
            u8 m;

            // Collect indices of all valid Pokémon (species != SPECIES_NONE)
            for (m = 0; m < PARTY_SIZE; m++)
            {
                if (tr->mons[m].species != SPECIES_NONE)
                    validMons[numValid++] = m;
            }

            // Shuffle valid mons using Fisher-Yates
            for (m = numValid; m > 1; m--)
            {
                u8 r = Random() % m;
                u8 tmp = validMons[r];
                validMons[r] = validMons[m - 1];
                validMons[m - 1] = tmp;
            }

            // Store chosen slots into monSlots
            for (m = 0; m < MULTI_PARTY_SIZE; m++)
            {
                if (numValid > 0)
                    gSaveBlock1Ptr->trainerHill.monSlots[f][j][m] = validMons[m % numValid];
                else
                    gSaveBlock1Ptr->trainerHill.monSlots[f][j][m] = m;
            }
        }
    }
}
#endif // FREE_TRAINER_HILL

static void SetUpDataStruct(void)
{
#if FREE_TRAINER_HILL == FALSE
    u8 f, cand1, cand2, mode;
    const struct TrainerHillCandidate *pool;

    if (sHillData != NULL) return;

    sHillData = AllocZeroed(sizeof(*sHillData));
    sHillData->floorId = gMapHeader.mapLayoutId - LAYOUT_TRAINER_HILL_1F;

    mode = gSaveBlock1Ptr->trainerHill.mode;
    if (mode >= NUM_TRAINER_HILL_MODES)
        mode = HILL_MODE_NORMAL;

    CpuCopy32(sChallengeData[mode], &sHillData->challenge, sizeof(sHillData->challenge));

    // If current floor trainers are uninitialized, generate challenge now
    if ((gSaveBlock1Ptr->trainerHill.currentFloorTrainers[0][0] & 0x7F) >= 17)
        GenerateTrainerHillChallenge(mode);

    pool = sTrainerHillCandidates[mode];
    for (f = 0; f < NUM_TRAINER_HILL_FLOORS; f++)
    {
        cand1 = gSaveBlock1Ptr->trainerHill.currentFloorTrainers[f][0];
        cand2 = gSaveBlock1Ptr->trainerHill.currentFloorTrainers[f][1];
        bool8 alt1 = (cand1 & 0x80) != 0;
        bool8 alt2 = (cand2 & 0x80) != 0;
        cand1 &= 0x7F;
        cand2 &= 0x7F;
        if (cand1 >= 17) cand1 = 0;
        if (cand2 >= 17) cand2 = 1;

        sHillData->floors[f].trainerNum1 = pool[cand1].trainerNum;
        sHillData->floors[f].trainerNum2 = pool[cand2].trainerNum;

        if (alt1 && pool[cand1].altTrainer != NULL)
            sHillData->floors[f].trainers[0] = *pool[cand1].altTrainer;
        else
            sHillData->floors[f].trainers[0] = pool[cand1].trainer;

        if (alt2 && pool[cand2].altTrainer != NULL)
            sHillData->floors[f].trainers[1] = *pool[cand2].altTrainer;
        else
            sHillData->floors[f].trainers[1] = pool[cand2].trainer;

        sHillData->floors[f].map = pool[cand1].map;
    }
#endif // FREE_TRAINER_HILL
}

static void FreeDataStruct(void)
{
    TRY_FREE_AND_SET_NULL(sHillData);
}

void CopyTrainerHillTrainerText(u8 which, u16 localId)
{
    u8 id, floorId;

    SetUpDataStruct();
    floorId = GetFloorId();
    id = localId - 1;

    switch (which)
    {
    case TRAINER_HILL_TEXT_INTRO:
        FrontierSpeechToString(sHillData->floors[floorId].trainers[id].speechBefore);
        break;
    case TRAINER_HILL_TEXT_PLAYER_LOST:
        FrontierSpeechToString(sHillData->floors[floorId].trainers[id].speechWin);
        break;
    case TRAINER_HILL_TEXT_PLAYER_WON:
        FrontierSpeechToString(sHillData->floors[floorId].trainers[id].speechLose);
        break;
    case TRAINER_HILL_TEXT_AFTER:
        FrontierSpeechToString(sHillData->floors[floorId].trainers[id].speechAfter);
        break;
    }

    FreeDataStruct();
}

static void TrainerHillStartChallenge(void)
{
    TrainerHillDummy();
#if FREE_TRAINER_HILL == FALSE
    u8 mode = gSaveBlock1Ptr->trainerHill.mode;
    u8 lvlMode = gSaveBlock1Ptr->trainerHill.lvlMode;

    GenerateTrainerHillChallenge(mode);

    if (mode < NUM_TRAINER_HILL_MODES && lvlMode < FRONTIER_LVL_MODE_COUNT)
    {
        if (gSaveBlock1Ptr->trainerHill.winStreaks[mode][lvlMode] == 0)
            gSaveBlock1Ptr->trainerHill.prevStreaks[mode][lvlMode] = 0;
    }

    if (!ReadTrainerHillAndValidate())
        gSaveBlock1Ptr->trainerHill.field_3D6E_0f = 1;
    else
        gSaveBlock1Ptr->trainerHill.field_3D6E_0f = 0;

    gSaveBlock1Ptr->trainerHill.unk_3D6C = 0;
    SetTrainerHillVBlankCounter(&gSaveBlock1Ptr->trainerHill.timer);
    gSaveBlock1Ptr->trainerHill.timer = 0;
    gSaveBlock1Ptr->trainerHill.spokeToOwner = 0;
    gSaveBlock1Ptr->trainerHill.checkedFinalTime = 0;
    gSaveBlock1Ptr->trainerHill.maybeECardScanDuringChallenge = 0;
    gSaveBlock2Ptr->frontier.trainerFlags = 0;
    gBattleOutcome = 0;
    gSaveBlock1Ptr->trainerHill.receivedPrize = 0;
    gSaveBlock1Ptr->trainerHill.runBP = 0;
    gSaveBlock1Ptr->trainerHill.wonBrainChallenge = 0;
    FlagSet(FLAG_HIDE_TRAINER_HILL_ROOF_WALLY);
    FlagSet(FLAG_HIDE_TRAINER_HILL_ROOF_SPECTATORS);
#endif //FREE_TRAINER_HILL
}

static void GetOwnerState(void)
{
#if FREE_TRAINER_HILL == FALSE
    ClearTrainerHillVBlankCounter();
    gSpecialVar_Result = 0;
    if (gSaveBlock1Ptr->trainerHill.spokeToOwner)
        gSpecialVar_Result++;
    if (gSaveBlock1Ptr->trainerHill.receivedPrize && gSaveBlock1Ptr->trainerHill.checkedFinalTime)
        gSpecialVar_Result++;

    gSaveBlock1Ptr->trainerHill.spokeToOwner = TRUE;
#endif //FREE_TRAINER_HILL
}

static u8 GetRunBP(u8 mode, u32 timer)
{
    u32 minutes;

    if (mode >= NUM_TRAINER_HILL_MODES)
        mode = HILL_MODE_NORMAL;

    minutes = timer / (60 * 60);

    // BP per run table by Time and Mode:
    // Time       Normal  Variety  Unique  Expert
    // >18 min       2       2        3       4
    // 16-18         2       3        4       6
    // 14-16         3       4        6       8
    // 13-14         4       6        7      10
    // 12-13         5       7        9      12
    // <12           6       8       10      14
    if (minutes >= 18)
    {
        static const u8 sBP_Over18[NUM_TRAINER_HILL_MODES] = { 2, 2, 3, 4 };
        return sBP_Over18[mode];
    }
    else if (minutes >= 16) // 16-18
    {
        static const u8 sBP_16To18[NUM_TRAINER_HILL_MODES] = { 2, 3, 4, 6 };
        return sBP_16To18[mode];
    }
    else if (minutes >= 14) // 14-16
    {
        static const u8 sBP_14To16[NUM_TRAINER_HILL_MODES] = { 3, 4, 6, 8 };
        return sBP_14To16[mode];
    }
    else if (minutes >= 13) // 13-14
    {
        static const u8 sBP_13To14[NUM_TRAINER_HILL_MODES] = { 4, 6, 7, 10 };
        return sBP_13To14[mode];
    }
    else if (minutes >= 12) // 12-13
    {
        static const u8 sBP_12To13[NUM_TRAINER_HILL_MODES] = { 5, 7, 9, 12 };
        return sBP_12To13[mode];
    }
    else // <12
    {
        static const u8 sBP_Under12[NUM_TRAINER_HILL_MODES] = { 6, 8, 10, 14 };
        return sBP_Under12[mode];
    }
}

static bool8 sIsNewRecord = FALSE;

static void UpdateTrainerHillClearRecords(void)
{
    u8 mode = gSaveBlock1Ptr->trainerHill.mode;
    u8 lvlMode = gSaveBlock1Ptr->trainerHill.lvlMode;
    u32 timer = gSaveBlock1Ptr->trainerHill.timer;
    u32 bestTime;

    if (mode >= NUM_TRAINER_HILL_MODES)
        mode = HILL_MODE_NORMAL;
    if (lvlMode >= FRONTIER_LVL_MODE_COUNT)
        lvlMode = FRONTIER_LVL_50;

    if (timer >= HILL_MAX_TIME)
        timer = HILL_MAX_TIME;

    if (gSaveBlock1Ptr->trainerHill.timesCleared[mode][lvlMode] < 0xFFFF)
        gSaveBlock1Ptr->trainerHill.timesCleared[mode][lvlMode]++;

    SetTimerValue(&gSaveBlock1Ptr->trainerHill.prevTimes[mode][lvlMode], timer);

    bestTime = GetTimerValue(&gSaveBlock1Ptr->trainerHill.recordTimes[mode][lvlMode]);
    if (bestTime == 0 || bestTime > HILL_MAX_TIME)
        bestTime = HILL_MAX_TIME;

    if (bestTime > timer || gSaveBlock1Ptr->trainerHill.timesCleared[mode][lvlMode] == 1)
    {
        sIsNewRecord = (bestTime > timer);
        SetTimerValue(&gSaveBlock1Ptr->trainerHill.bestTime, timer);
        SetTimerValue(&gSaveBlock1Ptr->trainerHill.recordTimes[mode][lvlMode], timer);
        gSaveBlock1Ptr->trainerHillTimes[mode] = gSaveBlock1Ptr->trainerHill.bestTime;
    }
    else
    {
        sIsNewRecord = FALSE;
    }

    if (gSaveBlock1Ptr->trainerHill.winStreaks[mode][lvlMode] < 0xFFFF)
        gSaveBlock1Ptr->trainerHill.winStreaks[mode][lvlMode]++;

    gSaveBlock1Ptr->trainerHill.prevStreaks[mode][lvlMode] = gSaveBlock1Ptr->trainerHill.winStreaks[mode][lvlMode];

    if (gSaveBlock1Ptr->trainerHill.winStreaks[mode][lvlMode] > gSaveBlock1Ptr->trainerHill.recordStreaks[mode][lvlMode])
        gSaveBlock1Ptr->trainerHill.recordStreaks[mode][lvlMode] = gSaveBlock1Ptr->trainerHill.winStreaks[mode][lvlMode];
}

static void GiveChallengePrize(void)
{
#if FREE_TRAINER_HILL == FALSE
    u16 points, cardPoints;

    if (gSaveBlock1Ptr->trainerHill.receivedPrize || gSaveBlock2Ptr->frontier.trainerFlags != 0xFF)
    {
        gSpecialVar_Result = 2;
        return;
    }

    UpdateTrainerHillClearRecords();
    points = gSaveBlock1Ptr->trainerHill.runBP;
    if (points == 0)
        points = GetRunBP(gSaveBlock1Ptr->trainerHill.mode, gSaveBlock1Ptr->trainerHill.timer);

    // Award Battle Points
    gSaveBlock2Ptr->frontier.battlePoints += points;
    if (gSaveBlock2Ptr->frontier.battlePoints > MAX_BATTLE_FRONTIER_POINTS)
        gSaveBlock2Ptr->frontier.battlePoints = MAX_BATTLE_FRONTIER_POINTS;

    cardPoints = gSaveBlock2Ptr->frontier.cardBattlePoints;
    cardPoints += points;
    if (cardPoints > 0xFFFF)
        cardPoints = 0xFFFF;
    gSaveBlock2Ptr->frontier.cardBattlePoints = cardPoints;

    IncrementDailyBattlePoints(points);

    ConvertIntToDecimalStringN(gStringVar1, points, STR_CONV_MODE_LEFT_ALIGN, 2);

    SetAllTrainerFlags();
    gSaveBlock1Ptr->trainerHill.receivedPrize = TRUE;
    gSaveBlock2Ptr->frontier.savedGame = FALSE;
    gSaveBlock2Ptr->frontier.unk_EF9 = 0;
    gSpecialVar_Result = 0;
#endif //FREE_TRAINER_HILL
}

// If bestTime > timer, the challenge was completed faster and its a new record
// Otherwise the owner says it was a slow time and to complete it faster next time
static void CheckFinalTime(void)
{
#if FREE_TRAINER_HILL == FALSE
    if (gSaveBlock1Ptr->trainerHill.checkedFinalTime || gSaveBlock2Ptr->frontier.trainerFlags != 0xFF)
    {
        gSpecialVar_Result = 2;
    }
    else
    {
        if (!gSaveBlock1Ptr->trainerHill.receivedPrize)
            UpdateTrainerHillClearRecords();

        if (sIsNewRecord)
            gSpecialVar_Result = 0;
        else
            gSpecialVar_Result = 1;
    }

    gSaveBlock1Ptr->trainerHill.checkedFinalTime = TRUE;
#endif //FREE_TRAINER_HILL
}

static void TrainerHillResumeTimer(void)
{
#if FREE_TRAINER_HILL == FALSE
    if (!InTrainerHillChallenge() || gSaveBlock1Ptr->trainerHill.spokeToOwner)
    {
        ClearTrainerHillVBlankCounter();
    }
    else
    {
        if (gSaveBlock1Ptr->trainerHill.timer >= HILL_MAX_TIME)
        {
            gSaveBlock1Ptr->trainerHill.timer = HILL_MAX_TIME;
            ClearTrainerHillVBlankCounter();
        }
        else
        {
            SetTrainerHillVBlankCounter(&gSaveBlock1Ptr->trainerHill.timer);
        }
    }
#endif //FREE_TRAINER_HILL
}

static void TrainerHillSetPlayerLost(void)
{
#if FREE_TRAINER_HILL == FALSE
    u8 mode = gSaveBlock1Ptr->trainerHill.mode;
    u8 lvlMode = gSaveBlock1Ptr->trainerHill.lvlMode;

    ClearTrainerHillVBlankCounter();

    if (mode < NUM_TRAINER_HILL_MODES && lvlMode < FRONTIER_LVL_MODE_COUNT)
        gSaveBlock1Ptr->trainerHill.winStreaks[mode][lvlMode] = 0;

    gSaveBlock1Ptr->trainerHill.hasLost = TRUE;
    gSaveBlock1Ptr->trainerHill.gaugeCredits = 0;
    gSaveBlock1Ptr->trainerHill.nextBrainThreshold = 200;
    gSaveBlock1Ptr->trainerHill.runBP = 0;
    gSaveBlock2Ptr->frontier.savedGame = FALSE;
#endif //FREE_TRAINER_HILL
}

static void TrainerHillGetChallengeStatus(void)
{
#if FREE_TRAINER_HILL == FALSE
    if (gSaveBlock1Ptr->trainerHill.hasLost)
    {
        // The player lost their last match.
        gSaveBlock1Ptr->trainerHill.hasLost = FALSE;
        gSaveBlock2Ptr->frontier.savedGame = FALSE;
        gSpecialVar_Result = TRAINER_HILL_PLAYER_STATUS_LOST;
    }
    else if (gSaveBlock1Ptr->trainerHill.wonBrainChallenge)
    {
        gSaveBlock1Ptr->trainerHill.wonBrainChallenge = FALSE;
        gSaveBlock2Ptr->frontier.savedGame = FALSE;
        gSpecialVar_Result = TRAINER_HILL_PLAYER_STATUS_BRAIN_WON;
    }
    else if (gSaveBlock1Ptr->trainerHill.maybeECardScanDuringChallenge)
    {
        // Unreachable code. Something relating to eCards?
        gSaveBlock1Ptr->trainerHill.maybeECardScanDuringChallenge = 0;
        gSaveBlock2Ptr->frontier.savedGame = FALSE;
        gSpecialVar_Result = TRAINER_HILL_PLAYER_STATUS_ECARD_SCANNED;
    }
    else if (gSaveBlock2Ptr->frontier.savedGame)
    {
        // Player quit or reset without finishing the challenge.
        u8 mode = gSaveBlock1Ptr->trainerHill.mode;
        u8 lvlMode = gSaveBlock1Ptr->trainerHill.lvlMode;

        ClearTrainerHillVBlankCounter();
        if (mode < NUM_TRAINER_HILL_MODES && lvlMode < FRONTIER_LVL_MODE_COUNT)
            gSaveBlock1Ptr->trainerHill.winStreaks[mode][lvlMode] = 0;
        gSaveBlock2Ptr->frontier.savedGame = FALSE;
        gSaveBlock1Ptr->trainerHill.gaugeCredits = 0;
        gSaveBlock1Ptr->trainerHill.nextBrainThreshold = 200;
        gSaveBlock1Ptr->trainerHill.runBP = 0;
        gSpecialVar_Result = TRAINER_HILL_PLAYER_STATUS_DIDNT_SAVE;
    }
    else
    {
        // Continue playing.
        gSpecialVar_Result = TRAINER_HILL_PLAYER_STATUS_NORMAL;
    }
#endif //FREE_TRAINER_HILL
}

static void BufferChallengeTime(void)
{
#if FREE_TRAINER_HILL == FALSE
    s32 total, minutes, secondsWhole, secondsFraction;

    total = gSaveBlock1Ptr->trainerHill.timer;
    if (total >= HILL_MAX_TIME)
        total = HILL_MAX_TIME;

    minutes = total / (60 * 60);
    total %= (60 * 60);
    secondsWhole = total / 60;
    total %= 60;
    secondsFraction = (total * 168) / 100;

    ConvertIntToDecimalStringN(gStringVar1, minutes, STR_CONV_MODE_RIGHT_ALIGN, 2);
    ConvertIntToDecimalStringN(gStringVar2, secondsWhole, STR_CONV_MODE_RIGHT_ALIGN, 2);
    ConvertIntToDecimalStringN(gStringVar3, secondsFraction, STR_CONV_MODE_LEADING_ZEROS, 2);
#endif //FREE_TRAINER_HILL
}

// Returns TRUE if all 4 floors are used
// Returns FALSE otherwise, and buffers the number of floors used
// The only time fewer than all 4 floors are used is for the JP-exclusive E-Reader and Default modes
static void GetAllFloorsUsed(void)
{
    SetUpDataStruct();
    if (sHillData->challenge.numFloors != NUM_TRAINER_HILL_FLOORS)
    {
        ConvertIntToDecimalStringN(gStringVar1, sHillData->challenge.numFloors, STR_CONV_MODE_LEFT_ALIGN, 1);
        gSpecialVar_Result = FALSE;
    }
    else
    {
        gSpecialVar_Result = TRUE;
    }

    FreeDataStruct();
}

// May have been dummied. Every time this is called a conditional for var result occurs afterwards
// Relation to E-Reader is an assumption, most dummied Trainer Hill code seems to be JP E-Reader mode related
static void GetInEReaderMode(void)
{
    SetUpDataStruct();
    gSpecialVar_Result = FALSE;
    FreeDataStruct();
}

bool8 InTrainerHillChallenge(void)
{
#if FREE_TRAINER_HILL == FALSE
    if (VarGet(VAR_TRAINER_HILL_IS_ACTIVE) == 0)
        return FALSE;
    else if (gSaveBlock1Ptr->trainerHill.spokeToOwner)
        return FALSE;
    else if (GetCurrentTrainerHillMapId() != 0)
        return TRUE;
    else
        return FALSE;
#else
    return FALSE;
#endif //FREE_TRAINER_HILL
}

static void IsTrainerHillChallengeActive(void)
{
    if (!InTrainerHillChallenge())
        gSpecialVar_Result = FALSE;
    else
        gSpecialVar_Result = TRUE;
}

static void TrainerHillDummy(void)
{

}

void PrintOnTrainerHillRecordsWindow(void)
{
#if FREE_TRAINER_HILL == FALSE
    s32 i, x, y;
    u32 total, minutes, secondsWhole, secondsFraction;

    SetUpDataStruct();
    FillWindowPixelBuffer(0, PIXEL_FILL(0));
    x = GetStringCenterAlignXOffset(FONT_NORMAL, gText_TimeBoard, 0xD0);
    AddTextPrinterParameterized3(0, FONT_NORMAL, x, 2, sRecordWinColors, TEXT_SKIP_DRAW, gText_TimeBoard);

    y = 18;
    for (i = 0; i < NUM_TRAINER_HILL_MODES; i++)
    {
        AddTextPrinterParameterized3(0, FONT_NORMAL, 0, y, sRecordWinColors, TEXT_SKIP_DRAW, sModeStrings[i]);
        y += 15;
        total = GetTimerValue(&gSaveBlock1Ptr->trainerHillTimes[i]);
        minutes = total / (60 * 60);
        total %= (60 * 60);
        ConvertIntToDecimalStringN(gStringVar1, minutes, STR_CONV_MODE_RIGHT_ALIGN, 2);
        secondsWhole = total / 60;
        total %= 60;
        ConvertIntToDecimalStringN(gStringVar2, secondsWhole, STR_CONV_MODE_RIGHT_ALIGN, 2);
        secondsFraction = (total * 168) / 100;
        ConvertIntToDecimalStringN(gStringVar3, secondsFraction, STR_CONV_MODE_LEADING_ZEROS, 2);
        StringExpandPlaceholders(StringCopy(gStringVar4, gText_TimeCleared), gText_XMinYDotZSec);
        x = GetStringRightAlignXOffset(FONT_NORMAL, gStringVar4, 0xD0);
        AddTextPrinterParameterized3(0, FONT_NORMAL, x, y, sRecordWinColors, TEXT_SKIP_DRAW, gStringVar4);
        y += 17;
    }

    PutWindowTilemap(0);
    CopyWindowToVram(0, COPYWIN_FULL);
    FreeDataStruct();
#endif //FREE_TRAINER_HILL
}

// Leftover from Fire Red / Leaf Green as in these games,
// the timer had to be xored by the encryption key in Sav2.
#if FREE_TRAINER_HILL == FALSE
static u32 GetTimerValue(u32 *src)
{
    return *src;
}

static void SetTimerValue(u32 *dst, u32 val)
{
    *dst = val;
}
#endif //FREE_TRAINER_HILL

void LoadTrainerHillObjectEventTemplates(void)
{
    u8 i, floorId;
    struct ObjectEventTemplate *eventTemplates = gSaveBlock1Ptr->objectEventTemplates;

    if (!LoadTrainerHillFloorObjectEventScripts())
        return;

    SetUpDataStruct();
    for (i = 0; i < HILL_TRAINERS_PER_FLOOR; i++)
        gSaveBlock2Ptr->frontier.trainerIds[i] = 0xFFFF;
    CpuFill32(0, gSaveBlock1Ptr->objectEventTemplates, sizeof(gSaveBlock1Ptr->objectEventTemplates));

    floorId = GetFloorId();
    for (i = 0; i < HILL_TRAINERS_PER_FLOOR; i++)
    {
        u8 bits;

        eventTemplates[i] = sTrainerObjectEventTemplate;
        eventTemplates[i].localId = i + 1;
        eventTemplates[i].graphicsId = FacilityClassToGraphicsId(sHillData->floors[floorId].trainers[i].facilityClass);
        eventTemplates[i].x = sHillData->floors[floorId].map.trainerCoords[i] & 0xF;
        eventTemplates[i].y = ((sHillData->floors[floorId].map.trainerCoords[i] >> 4) & 0xF) + HILL_FLOOR_HEIGHT_MARGIN;
        bits = i << 2;
        eventTemplates[i].movementType = ((sHillData->floors[floorId].map.trainerDirections >> bits) & 0xF) + MOVEMENT_TYPE_FACE_UP;
        eventTemplates[i].trainerRange_berryTreeId = (sHillData->floors[floorId].map.trainerRanges >> bits) & 0xF;
        eventTemplates[i].script = TrainerHill_EventScript_TrainerBattle;
        gSaveBlock2Ptr->frontier.trainerIds[i] = i + 1;
    }

    FreeDataStruct();
}

bool32 LoadTrainerHillFloorObjectEventScripts(void)
{
    SetUpDataStruct();
    // Something may have been dummied here
    FreeDataStruct();
    return TRUE;
}

static u16 GetMapDataForFloor(u8 floorId, u32 x, u32 y, u32 floorWidth) // floorWidth is always 16
{
    bool8 impassable;
    u16 metatileId;
    u16 elevation;

    impassable = (sHillData->floors[floorId].map.collisionData[y] >> (15 - x) & 1);
    metatileId = sHillData->floors[floorId].map.metatileData[floorWidth * y + x] + NUM_METATILES_IN_PRIMARY;
    elevation = PACK_ELEVATION(ELEVATION_DEFAULT);

    return PACK_COLLISION(impassable) | elevation | PACK_METATILE(metatileId);
}

void GenerateTrainerHillFloorLayout(u16 *mapArg)
{
    s32 y, x;
    const u16 *src;
    u16 *dst;
    u8 mapId = GetCurrentTrainerHillMapId();

    if (mapId == TRAINER_HILL_ENTRANCE)
    {
        InitMapFromSavedGame();
        return;
    }

    SetUpDataStruct();
    if (mapId == TRAINER_HILL_ROOF)
    {
        InitMapFromSavedGame();
        FreeDataStruct();
        return;
    }

    mapId = GetFloorId();
    src = gMapHeader.mapLayout->map;
    gBackupMapLayout.map = mapArg;
    // Dimensions include border area loaded beyond map
    gBackupMapLayout.width = HILL_FLOOR_WIDTH + 15;
    gBackupMapLayout.height = HILL_FLOOR_HEIGHT + 14;
    dst = mapArg + 224;

    // First 5 rows of the map (Entrance / Exit) are always the same
    for (y = 0; y < HILL_FLOOR_HEIGHT_MARGIN; y++)
    {
        for (x = 0; x < HILL_FLOOR_WIDTH; x++)
            dst[x] = src[x];
        dst += 31;
        src += 16;
    }

    // Load the 16x16 floor-specific layout
    for (y = 0; y < HILL_FLOOR_HEIGHT_MAIN; y++)
    {
        for (x = 0; x < HILL_FLOOR_WIDTH; x++)
            dst[x] = GetMapDataForFloor(mapId, x, y, HILL_FLOOR_WIDTH);
        dst += 31;
    }

    RunOnLoadMapScript();
    FreeDataStruct();
}

bool32 InTrainerHill(void)
{
    bool32 ret;

    if (gMapHeader.mapLayoutId == LAYOUT_TRAINER_HILL_1F
        || gMapHeader.mapLayoutId == LAYOUT_TRAINER_HILL_2F
        || gMapHeader.mapLayoutId == LAYOUT_TRAINER_HILL_3F
        || gMapHeader.mapLayoutId == LAYOUT_TRAINER_HILL_4F)
        ret = TRUE;
    else
        ret = FALSE;

    return ret;
}

u8 GetCurrentTrainerHillMapId(void)
{
    u8 mapId;

    if (gMapHeader.mapLayoutId == LAYOUT_TRAINER_HILL_1F)
        mapId = TRAINER_HILL_1F;
    else if (gMapHeader.mapLayoutId == LAYOUT_TRAINER_HILL_2F)
        mapId = TRAINER_HILL_2F;
    else if (gMapHeader.mapLayoutId == LAYOUT_TRAINER_HILL_3F)
        mapId = TRAINER_HILL_3F;
    else if (gMapHeader.mapLayoutId == LAYOUT_TRAINER_HILL_4F)
        mapId = TRAINER_HILL_4F;
    else if (gMapHeader.mapLayoutId == LAYOUT_TRAINER_HILL_ROOF)
        mapId = TRAINER_HILL_ROOF;
    else if (gMapHeader.mapLayoutId == LAYOUT_TRAINER_HILL_ENTRANCE)
        mapId = TRAINER_HILL_ENTRANCE;
    else
        mapId = 0;

    return mapId;
}

static bool32 UNUSED OnTrainerHillRoof(void)
{
    bool32 onRoof;

    if (gMapHeader.mapLayoutId == LAYOUT_TRAINER_HILL_ROOF)
        onRoof = TRUE;
    else
        onRoof = FALSE;

    return onRoof;
}

const struct WarpEvent* SetWarpDestinationTrainerHill4F(void)
{
    const struct MapHeader *header = Overworld_GetMapHeaderByGroupAndId(MAP_GROUP(MAP_TRAINER_HILL_4F), MAP_NUM(MAP_TRAINER_HILL_4F));

    return &header->events->warps[1];
}

// For warping from the roof in challenges where the 4F is not the final challenge floor
// This would only occur in the JP-exclusive Default and E-Reader challenges
const struct WarpEvent* SetWarpDestinationTrainerHillFinalFloor(u8 warpEventId)
{
    u8 numFloors;
    const struct MapHeader *header;

    if (warpEventId == 1)
        return &gMapHeader.events->warps[1];

    numFloors = GetNumFloorsInTrainerHillChallenge();
    if (numFloors == 0 || numFloors > NUM_TRAINER_HILL_FLOORS)
        numFloors = NUM_TRAINER_HILL_FLOORS;

    header = Overworld_GetMapHeaderByGroupAndId(MAP_GROUP(MAP_TRAINER_HILL_4F), sNextFloorMapNum[numFloors - 1]);
    return &header->events->warps[0];
}

u16 LocalIdToHillTrainerId(u8 localId)
{
    return gSaveBlock2Ptr->frontier.trainerIds[localId - 1];
}

bool8 GetHillTrainerFlag(u8 objectEventId)
{
    u32 trainerIndexStart = GetFloorId() * HILL_TRAINERS_PER_FLOOR;
    u8 bitId = gObjectEvents[objectEventId].localId - 1 + trainerIndexStart;

    return gSaveBlock2Ptr->frontier.trainerFlags & (1u << bitId);
}

void SetHillTrainerFlag(void)
{
    u8 i;
    u8 trainerIndexStart = GetFloorId() * HILL_TRAINERS_PER_FLOOR;

    for (i = 0; i < HILL_TRAINERS_PER_FLOOR; i++)
    {
        if (gSaveBlock2Ptr->frontier.trainerIds[i] == TRAINER_BATTLE_PARAM.opponentA)
        {
            gSaveBlock2Ptr->frontier.trainerFlags |= 1u << (trainerIndexStart + i);
            break;
        }
    }

    if (gBattleTypeFlags & BATTLE_TYPE_TWO_OPPONENTS)
    {
        for (i = 0; i < HILL_TRAINERS_PER_FLOOR; i++)
        {
            if (gSaveBlock2Ptr->frontier.trainerIds[i] == TRAINER_BATTLE_PARAM.opponentB)
            {
                gSaveBlock2Ptr->frontier.trainerFlags |= 1u << (trainerIndexStart + i);
                break;
            }
        }
    }
}

const u8 *GetTrainerHillTrainerScript(void)
{
    return TrainerHill_EventScript_TrainerBattle;
}

static void ShowTrainerHillPostBattleText(void)
{
    CopyTrainerHillTrainerText(TRAINER_HILL_TEXT_AFTER, gSpecialVar_LastTalked);
    ShowFieldMessageFromBuffer();
}

static void CreateNPCTrainerHillParty(u16 trainerId, enum BattleTrainer trainer)
{
    u8 trId, level;
    s32 i, floorId;

    if (trainerId == 0 || trainerId > HILL_TRAINERS_PER_FLOOR)
        return;

    trId = trainerId - 1;
    SetUpDataStruct();
    if (gSaveBlock1Ptr->trainerHill.lvlMode == FRONTIER_LVL_50)
    {
        level = FRONTIER_MAX_LEVEL_50;
    }
    else
    {
        level = GetHighestLevelInPlayerParty();
        if (level < FRONTIER_MIN_LEVEL_OPEN)
            level = FRONTIER_MIN_LEVEL_OPEN;
    }
    floorId = GetFloorId();
    if (floorId >= NUM_TRAINER_HILL_FLOORS)
        floorId = 0;

    for (i = 0; i < MULTI_PARTY_SIZE; i++)
    {
        u8 id = gSaveBlock1Ptr->trainerHill.monSlots[floorId][trId][i];
        struct Pokemon *mon = &gParties[trainer][i];

        if (id >= PARTY_SIZE)
            id = i;

        CreateBattleTowerMon(mon, &sHillData->floors[floorId].trainers[trId].mons[id]);
        SetTrainerHillMonLevel(mon, level);
    }

    FreeDataStruct();
}

void FillHillTrainerParty(void)
{
    ZeroEnemyPartyMons();
    CreateNPCTrainerHillParty(TRAINER_BATTLE_PARAM.opponentA, B_TRAINER_OPPONENT_A);
}

void FillHillTrainersParties(void)
{
    ZeroEnemyPartyMons();
    CreateNPCTrainerHillParty(TRAINER_BATTLE_PARAM.opponentA, B_TRAINER_OPPONENT_A);
    CreateNPCTrainerHillParty(TRAINER_BATTLE_PARAM.opponentB, B_TRAINER_OPPONENT_B);
}

u8 GetTrainerEncounterMusicIdInTrainerHill(u16 trainerId)
{
    s32 i;
    u8 trId, facilityClass;

    SetUpDataStruct();
    trId = trainerId - 1;
    facilityClass = sHillData->floors[sHillData->floorId].trainers[trId].facilityClass;
    FreeDataStruct();

    for (i = 0; i < ARRAY_COUNT(sTrainerClassesAndMusic); i++)
    {
        if (sTrainerClassesAndMusic[i].trainerClass == gFacilityClassToTrainerClass[facilityClass])
            return sTrainerClassesAndMusic[i].musicId;
    }

    return 0;
}

void SetTrainerHillMonLevel(struct Pokemon *mon, u8 level)
{
    enum Species species = GetMonData(mon, MON_DATA_SPECIES);
    u32 exp = gExperienceTables[gSpeciesInfo[species].growthRate][level];

    SetMonData(mon, MON_DATA_EXP, &exp);
    SetMonData(mon, MON_DATA_LEVEL, &level);
    CalculateMonStats(mon);
}

u8 GetNumFloorsInTrainerHillChallenge(void)
{
    u8 floors;

    SetUpDataStruct();
    floors = sHillData->challenge.numFloors;
    FreeDataStruct();

    return floors;
}

static void SetAllTrainerFlags(void)
{
    gSaveBlock2Ptr->frontier.trainerFlags = 0xFF;
}

// Palette never loaded, OnTrainerHillEReaderChallengeFloor always FALSE
void TryLoadTrainerHillEReaderPalette(void)
{
    if (OnTrainerHillEReaderChallengeFloor() == TRUE)
        LoadPalette(sEReader_Pal, BG_PLTT_ID(7), PLTT_SIZE_4BPP);
}

static void GetGameSaved(void)
{
    gSpecialVar_Result = gSaveBlock2Ptr->frontier.savedGame;
}

static void SetGameSaved(void)
{
    gSaveBlock2Ptr->frontier.savedGame = TRUE;
}

static void ClearGameSaved(void)
{
    gSaveBlock2Ptr->frontier.savedGame = FALSE;
}

// Always FALSE
bool32 OnTrainerHillEReaderChallengeFloor(void)
{
    if (!InTrainerHillChallenge() || GetCurrentTrainerHillMapId() == TRAINER_HILL_ENTRANCE)
        return FALSE;

    GetInEReaderMode();
    if (gSpecialVar_Result == FALSE)
        return FALSE;
    else
        return TRUE;
}

static void GetChallengeWon(void)
{
#if FREE_TRAINER_HILL == FALSE
    if (gSaveBlock1Ptr->trainerHill.hasLost)
        gSpecialVar_Result = FALSE;
    else
        gSpecialVar_Result = TRUE;
#endif //FREE_TRAINER_HILL
}

static void TrainerHillSetMode(void)
{
#if FREE_TRAINER_HILL == FALSE
    u8 mode = gSpecialVar_0x8005;
    u8 lvlMode = gSaveBlock1Ptr->trainerHill.lvlMode;
    u32 bestTime;

    if (mode >= NUM_TRAINER_HILL_MODES)
        mode = HILL_MODE_NORMAL;
    if (lvlMode >= FRONTIER_LVL_MODE_COUNT)
        lvlMode = FRONTIER_LVL_50;

    gSaveBlock1Ptr->trainerHill.mode = mode;
    bestTime = GetTimerValue(&gSaveBlock1Ptr->trainerHill.recordTimes[mode][lvlMode]);
    if (bestTime == 0 || bestTime > HILL_MAX_TIME)
        bestTime = HILL_MAX_TIME;
    gSaveBlock1Ptr->trainerHill.bestTime = bestTime;
#endif //FREE_TRAINER_HILL
}

static void TrainerHillGetPartyMaxLevel(void)
{
    gSpecialVar_Result = GetHighestLevelInPlayerParty();
}

static void TrainerHillSetLvlMode(void)
{
#if FREE_TRAINER_HILL == FALSE
    gSaveBlock1Ptr->trainerHill.lvlMode = gSpecialVar_0x8005;
    gSaveBlock2Ptr->frontier.lvlMode = gSpecialVar_0x8005;
#endif //FREE_TRAINER_HILL
}

#define HILL_GAUGE_SILVER_THRESHOLD 200 // 2.0 credits
#define HILL_GAUGE_GOLD_THRESHOLD   650 // 6.5 credits
#define HILL_GAUGE_GOLD_INCREMENT   450 // +4.5 credits per subsequent Gold

static void TrainerHillCheckFrontierBrain(void)
{
#if FREE_TRAINER_HILL == FALSE
    u32 minutes;
    u16 baseCredits;
    u16 multiplier;
    u16 earned;
    u8 mode;

    ClearTrainerHillVBlankCounter();
    if (gSaveBlock1Ptr->trainerHill.timer > HILL_MAX_TIME)
        gSaveBlock1Ptr->trainerHill.timer = HILL_MAX_TIME;

    if (gSaveBlock1Ptr->trainerHill.hasLost 
        || gSaveBlock1Ptr->trainerHill.receivedPrize
        || gSaveBlock2Ptr->frontier.trainerFlags != 0xFF)
    {
        gSpecialVar_Result = TRAINER_HILL_BRAIN_NONE;
        return;
    }

    mode = gSaveBlock1Ptr->trainerHill.mode;
    if (mode >= NUM_TRAINER_HILL_MODES)
        mode = HILL_MODE_NORMAL;

    // Cache the BP for this run so Wally can award it combined with the 10 BP
    gSaveBlock1Ptr->trainerHill.runBP = GetRunBP(mode, gSaveBlock1Ptr->trainerHill.timer);

    minutes = gSaveBlock1Ptr->trainerHill.timer / (60 * 60);

    // Base credits by time bracket:
    // <12 min: 1.0 (100)
    // 12-13:   0.8 (80)
    // 13-14:   0.6 (60)
    // 14-16:   0.4 (40)
    // 16-18:   0.2 (20)
    // >18:     0.0 (0)
    if (minutes >= 18)
        baseCredits = 0;
    else if (minutes >= 16)
        baseCredits = 20;
    else if (minutes >= 14)
        baseCredits = 40;
    else if (minutes >= 13)
        baseCredits = 60;
    else if (minutes >= 12)
        baseCredits = 80;
    else
        baseCredits = 100;

    // Mode multipliers:
    // Normal:  x0.5  (50)
    // Variety: x0.75 (75)
    // Unique:  x1.0  (100)
    // Expert:  x1.5  (150)
    static const u16 sModeMultipliers[NUM_TRAINER_HILL_MODES] = { 50, 75, 100, 150 };
    multiplier = sModeMultipliers[mode];

    earned = (baseCredits * multiplier) / 100;
    gSaveBlock1Ptr->trainerHill.gaugeCredits += earned;
    if (gSaveBlock1Ptr->trainerHill.gaugeCredits > 60000)
        gSaveBlock1Ptr->trainerHill.gaugeCredits = 60000;

    if (gSaveBlock1Ptr->trainerHill.nextBrainThreshold < HILL_GAUGE_SILVER_THRESHOLD)
        gSaveBlock1Ptr->trainerHill.nextBrainThreshold = HILL_GAUGE_SILVER_THRESHOLD;

    // Check Brain appearance:
    if (gSaveBlock1Ptr->trainerHill.gaugeCredits >= gSaveBlock1Ptr->trainerHill.nextBrainThreshold)
    {
        gSaveBlock1Ptr->trainerHill.spokeToOwner = TRUE;
        if (gSaveBlock1Ptr->trainerHill.nextBrainThreshold == HILL_GAUGE_SILVER_THRESHOLD)
        {
            if (!gSaveBlock1Ptr->trainerHill.hasDefeatedSilver)
                gSpecialVar_Result = TRAINER_HILL_BRAIN_SILVER;
            else
                gSpecialVar_Result = TRAINER_HILL_BRAIN_STREAK;
            return;
        }
        else // Gold (6.5 credits, 11.0 credits, etc.)
        {
            if (!gSaveBlock1Ptr->trainerHill.hasDefeatedGold)
                gSpecialVar_Result = TRAINER_HILL_BRAIN_GOLD;
            else
                gSpecialVar_Result = TRAINER_HILL_BRAIN_STREAK_LONG;
            return;
        }
    }

    gSpecialVar_Result = TRAINER_HILL_BRAIN_NONE;
#endif //FREE_TRAINER_HILL
}

static void TrainerHillGiveBrainPrize(void)
{
#if FREE_TRAINER_HILL == FALSE
    u16 points;
    u16 cardPoints;

    UpdateTrainerHillClearRecords();
    points = 10 + gSaveBlock1Ptr->trainerHill.runBP;

    gSaveBlock2Ptr->frontier.battlePoints += points;
    if (gSaveBlock2Ptr->frontier.battlePoints > MAX_BATTLE_FRONTIER_POINTS)
        gSaveBlock2Ptr->frontier.battlePoints = MAX_BATTLE_FRONTIER_POINTS;

    cardPoints = gSaveBlock2Ptr->frontier.cardBattlePoints;
    cardPoints += points;
    if (cardPoints > 0xFFFF)
        cardPoints = 0xFFFF;
    gSaveBlock2Ptr->frontier.cardBattlePoints = cardPoints;

    IncrementDailyBattlePoints(points);

    ConvertIntToDecimalStringN(gStringVar1, points, STR_CONV_MODE_LEFT_ALIGN, 2);

    if (gSaveBlock1Ptr->trainerHill.nextBrainThreshold == HILL_GAUGE_SILVER_THRESHOLD)
    {
        gSaveBlock1Ptr->trainerHill.hasDefeatedSilver = TRUE;
        FlagSet(FLAG_SYS_HILL_SILVER);
        gSaveBlock1Ptr->trainerHill.nextBrainThreshold = HILL_GAUGE_GOLD_THRESHOLD; // 6.5 credits
    }
    else
    {
        gSaveBlock1Ptr->trainerHill.hasDefeatedGold = TRUE;
        FlagSet(FLAG_SYS_HILL_GOLD);
        gSaveBlock1Ptr->trainerHill.nextBrainThreshold += HILL_GAUGE_GOLD_INCREMENT; // +4.5 credits
    }

    SetAllTrainerFlags();
    gSaveBlock1Ptr->trainerHill.receivedPrize = TRUE;
    gSaveBlock1Ptr->trainerHill.wonBrainChallenge = TRUE;
    gSaveBlock2Ptr->frontier.savedGame = FALSE;
    gSaveBlock2Ptr->frontier.unk_EF9 = 0;
#endif //FREE_TRAINER_HILL
}

static void TrainerHillGetSpokeToOwner(void)
{
#if FREE_TRAINER_HILL == FALSE
    gSpecialVar_Result = gSaveBlock1Ptr->trainerHill.spokeToOwner;
#else
    gSpecialVar_Result = TRUE;
#endif
}

static void TrainerHillSetRoofSpectatorGraphics(void)
{
#if FREE_TRAINER_HILL == FALSE
    u8 mode = gSaveBlock1Ptr->trainerHill.mode;
    u8 f, j;
    const struct TrainerHillCandidate *pool;

    if (mode >= NUM_TRAINER_HILL_MODES)
        mode = HILL_MODE_NORMAL;

    if ((gSaveBlock1Ptr->trainerHill.currentFloorTrainers[0][0] & 0x7F) >= 17)
        GenerateTrainerHillChallenge(mode);

    pool = sTrainerHillCandidates[mode];
    for (f = 0; f < NUM_TRAINER_HILL_FLOORS; f++)
    {
        for (j = 0; j < HILL_TRAINERS_PER_FLOOR; j++)
        {
            u8 cand = gSaveBlock1Ptr->trainerHill.currentFloorTrainers[f][j];
            bool8 isAlt = (cand & 0x80) != 0;
            cand &= 0x7F;
            if (cand < 17)
            {
                u8 facilityClass = (isAlt && pool[cand].altTrainer != NULL) ? pool[cand].altTrainer->facilityClass : pool[cand].trainer.facilityClass;
                u16 gfxId = FacilityClassToGraphicsId(facilityClass);
                VarSet(VAR_OBJ_GFX_ID_0 + (f * 2 + j), gfxId);
            }
        }
    }
#endif //FREE_TRAINER_HILL
}

static void TrainerHillBufferModeName(void)
{
    u8 mode = gSaveBlock1Ptr->trainerHill.mode;
    if (mode >= NUM_TRAINER_HILL_MODES)
        mode = HILL_MODE_NORMAL;
    StringCopy(gStringVar1, sModeStrings[mode]);
}

static void TrainerHillSaveChallenge(void)
{
#if FREE_TRAINER_HILL == FALSE
    s16 x = 19;
    s16 y = 1;

    if (GetCurrentTrainerHillMapId() == TRAINER_HILL_ENTRANCE)
    {
        x = 3;
        y = 11;
    }

    SetDynamicWarpWithCoords(0, MAP_GROUP(MAP_TRAINER_HILL_ENTRANCE), MAP_NUM(MAP_TRAINER_HILL_ENTRANCE), WARP_ID_NONE, x, y);
    gSaveBlock2Ptr->frontier.savedGame = FALSE;
    SaveGameFrontier();
#endif
}

static void TrainerHillRetire(void)
{
#if FREE_TRAINER_HILL == FALSE
    u8 mode = gSaveBlock1Ptr->trainerHill.mode;
    u8 lvlMode = gSaveBlock1Ptr->trainerHill.lvlMode;

    ClearTrainerHillVBlankCounter();

    if (mode < NUM_TRAINER_HILL_MODES && lvlMode < FRONTIER_LVL_MODE_COUNT)
        gSaveBlock1Ptr->trainerHill.winStreaks[mode][lvlMode] = 0;

    gSaveBlock1Ptr->trainerHill.hasLost = FALSE;
    gSaveBlock1Ptr->trainerHill.gaugeCredits = 0;
    gSaveBlock1Ptr->trainerHill.nextBrainThreshold = 200;
    gSaveBlock1Ptr->trainerHill.runBP = 0;
    gSaveBlock2Ptr->frontier.savedGame = FALSE;
#endif
}




