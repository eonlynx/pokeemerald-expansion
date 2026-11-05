#include "global.h"
#include "time_events.h"
#include "event_data.h"
#include "field_weather.h"
#include "pokemon.h"
#include "random.h"
#include "overworld.h"
#include "rtc.h"
#include "script.h"
#include "task.h"
#include "item.h"
#include "constants/items.h"
#include "constants/layouts.h"
#include "field_player_avatar.h"

#define MIRAGE_ISLAND_SALT 0x0300714C // Adress of the mirage island var in vanilla Emerald

static u32 GetMirageRnd(void)
{
    #if OW_USE_DAILY_SEED_FOR_VANILLA_VARIABLES == FALSE
    u32 hi = VarGet(VAR_MIRAGE_RND_H);
    u32 lo = VarGet(VAR_MIRAGE_RND_L);
    return (hi << 16) | lo;
    #else
    rng_value_t localRngState = LocalRandomSeed(gSaveBlock1Ptr->dailySeed ^ MIRAGE_ISLAND_SALT);
    return LocalRandom32(&localRngState);
    #endif
}

static void SetMirageRnd(u32 rnd)
{
    #if OW_USE_DAILY_SEED_FOR_VANILLA_VARIABLESD == FALSE
    VarSet(VAR_MIRAGE_RND_H, rnd >> 16);
    VarSet(VAR_MIRAGE_RND_L, rnd);
    #endif
}

void UpdateMirageRnd(u16 days)
{
    s32 rnd = GetMirageRnd();
    while (days)
    {
        rnd = ISO_RANDOMIZE2(rnd);
        days--;
    }
    SetMirageRnd(rnd);
}

bool8 IsWishCharmActive(void)
{
    if (!CheckBagHasItem(ITEM_WISH_CHARM, 1))
        return FALSE;

#if OW_FLAG_WISH_CHARM_INFINITE != 0
    if (FlagGet(OW_FLAG_WISH_CHARM_INFINITE))
        return TRUE;
#endif

    if (FlagGet(FLAG_WISH_CHARM_EXPIRED))
        return FALSE;

    u16 visitDay = VarGet(VAR_WISH_CHARM_VISIT_DAY);
    if (visitDay != 0)
    {
        u16 currentDay = VarGet(VAR_DAYS) + 1;
        if (currentDay != visitDay)
        {
            FlagSet(FLAG_WISH_CHARM_EXPIRED);
            return FALSE;
        }
    }

    return TRUE;
}

void UpdateMirageIslandWishCharmStep(void)
{
    if (gSaveBlock1Ptr->location.mapGroup == MAP_GROUP(MAP_ROUTE130)
     && gSaveBlock1Ptr->location.mapNum == MAP_NUM(MAP_ROUTE130)
     && gSaveBlock1Ptr->mapLayoutId == LAYOUT_ROUTE130_MIRAGE_ISLAND)
    {
        if (!TestPlayerAvatarFlags(PLAYER_AVATAR_FLAG_SURFING))
        {
            if (CheckBagHasItem(ITEM_WISH_CHARM, 1) && !FlagGet(FLAG_WISH_CHARM_VISITED))
            {
                FlagSet(FLAG_WISH_CHARM_VISITED);
                VarSet(VAR_WISH_CHARM_VISIT_DAY, VarGet(VAR_DAYS) + 1);
            }
        }
    }
}

void UpdateMirageIslandWishCharmDaily(void)
{
    if (FlagGet(FLAG_WISH_CHARM_VISITED))
    {
        FlagSet(FLAG_WISH_CHARM_EXPIRED);
    }
}

bool8 IsMirageIslandPresent(void)
{
    if (IsWishCharmActive())
        return TRUE;

    u16 rnd = GetMirageRnd() >> 16;
    int i;

    for (i = 0; i < PARTY_SIZE; i++)
        if (GetMonData(&gParties[B_TRAINER_PLAYER][i], MON_DATA_SPECIES) && (GetMonData(&gParties[B_TRAINER_PLAYER][i], MON_DATA_PERSONALITY) & 0xFFFF) == rnd)
            return TRUE;

    return FALSE;
}

void UpdateShoalTideFlag(void)
{
    static const u8 tide[] =
    {
        1, // 00
        1, // 01
        1, // 02
        0, // 03
        0, // 04
        0, // 05
        0, // 06
        0, // 07
        0, // 08
        1, // 09
        1, // 10
        1, // 11
        1, // 12
        1, // 13
        1, // 14
        0, // 15
        0, // 16
        0, // 17
        0, // 18
        0, // 19
        0, // 20
        1, // 21
        1, // 22
        1, // 23
    };

    if (IsMapTypeOutdoors(GetLastUsedWarpMapType()))
    {
        RtcCalcLocalTime();
        if (tide[gLocalTime.hours])
            FlagSet(FLAG_SYS_SHOAL_TIDE);
        else
            FlagClear(FLAG_SYS_SHOAL_TIDE);
    }
}

static void Task_WaitWeather(u8 taskId)
{
    if (IsWeatherChangeComplete())
    {
        ScriptContext_Enable();
        DestroyTask(taskId);
    }
}

void WaitWeather(void)
{
    CreateTask(Task_WaitWeather, 80);
}

void InitBirchState(void)
{
    *GetVarPointer(VAR_BIRCH_STATE) = 0;
}

void UpdateBirchState(u16 days)
{
    u16 *state = GetVarPointer(VAR_BIRCH_STATE);
    *state += days;
    *state %= 7;
}
