#include "global.h"
#include "tcg.h"
#include "pokemon.h"
#include "battle.h"
#include "battle_controllers.h"
#include "random.h"
#include "sound.h"
#include "constants/songs.h"
#include "constants/tcg_cards.h"
#define sPlayerParty (gParties[B_TRAINER_PLAYER])
#define sEnemyParty  (gParties[B_TRAINER_OPPONENT_A])

static void DrawCardsToPlayerHand(u8 count)
{
    while (count > 0 && gTcgBattleState.playerDeckRemainingCount > 0 && gTcgBattleState.playerHandCount < 10)
    {
        DrawCardForPlayer();
        count--;
    }
}

static void DrawSpecificCardToPlayerHand(bool8 basicOnly, bool8 pokemonOnly, bool8 trainerOnly)
{
    for (u32 i = 0; i < gTcgBattleState.playerDeckRemainingCount; i++)
    {
        u16 cid = gTcgBattleState.playerDeckRemaining[i];
        const struct TcgCardInfo *info = GetTcgCardInfo(cid);
        if (!info)
            continue;

        bool8 match = TRUE;
        if (basicOnly && (info->cardType != CARD_TYPE_POKEMON_BASIC || info->species == SPECIES_NONE || cid == CARD_MYSTERIOUS_FOSSIL))
            match = FALSE;
        if (pokemonOnly && info->species == SPECIES_NONE)
            match = FALSE;
        if (trainerOnly && info->cardType != CARD_TYPE_TRAINER_ITEM && info->cardType != CARD_TYPE_TRAINER_SUPPORTER)
            match = FALSE;

        if (match && gTcgBattleState.playerHandCount < 10)
        {
            for (u32 j = i; j + 1 < gTcgBattleState.playerDeckRemainingCount; j++)
                gTcgBattleState.playerDeckRemaining[j] = gTcgBattleState.playerDeckRemaining[j + 1];
            gTcgBattleState.playerDeckRemaining[gTcgBattleState.playerDeckRemainingCount - 1] = 0;
            gTcgBattleState.playerDeckRemainingCount--;
            gTcgBattleState.playerHand[gTcgBattleState.playerHandCount++] = cid;
            return;
        }
    }
    DrawCardsToPlayerHand(1);
}

bool8 ExecuteTrainerCardEffect(u16 cardId, u8 battler)
{
    const struct TcgCardInfo *info = GetTcgCardInfo(cardId);
    if (!info)
        return FALSE;

    u8 opponent = battler ^ 1;

    // Supporter restriction: only 1 Supporter per turn
    if (info->cardType == CARD_TYPE_TRAINER_SUPPORTER)
    {
        if (gTcgBattleState.supporterUsedThisTurn)
        {
            PlaySE(SE_FAILURE);
            return FALSE;
        }
    }

    bool8 success = FALSE;

    switch (cardId)
    {
    case CARD_PROFESSOR_OAK:
        // Discard all remaining cards in playerHand and draw 5 cards
        for (u32 i = 0; i < gTcgBattleState.playerHandCount; i++)
            RecordDiscardedCard(B_SIDE_PLAYER, gTcgBattleState.playerHand[i]);
        gTcgBattleState.playerHandCount = 0;
        gTcgBattleState.handScrollOffset = 0;
        DrawCardsToPlayerHand(5);
        PlaySE(SE_SELECT);
        success = TRUE;
        break;

    case CARD_BILL:
        DrawCardsToPlayerHand(2);
        PlaySE(SE_SELECT);
        success = TRUE;
        break;

    case CARD_BILLS_TELEPORTER:
        if ((Random() & 1) == 0)
            DrawCardsToPlayerHand(4);
        PlaySE(SE_SELECT);
        success = TRUE;
        break;

    case CARD_POKE_RECEIVER:
        if ((Random() & 1) == 0)
            DrawSpecificCardToPlayerHand(TRUE, TRUE, FALSE);
        PlaySE(SE_USE_ITEM);
        success = TRUE;
        break;

    case CARD_MASTER_BALL:
    case CARD_BILLS_PC:
    case CARD_POKEMON_TRADER:
    case CARD_THE_BOSSS_WAY:
    case CARD_MOON_STONE:
        DrawSpecificCardToPlayerHand(FALSE, TRUE, FALSE);
        PlaySE(SE_SELECT);
        success = TRUE;
        break;

    case CARD_COMPUTER_SEARCH:
        if (gTcgBattleState.playerHandCount > 0)
        {
            RecordDiscardedCard(B_SIDE_PLAYER, gTcgBattleState.playerHand[gTcgBattleState.playerHandCount - 1]);
            RemoveCardFromPlayerHandAt(gTcgBattleState.playerHandCount - 1);
        }
        DrawCardsToPlayerHand(1);
        PlaySE(SE_SELECT);
        success = TRUE;
        break;

    case CARD_ITEM_FINDER:
        if (gTcgBattleState.playerHandCount > 0)
        {
            RecordDiscardedCard(B_SIDE_PLAYER, gTcgBattleState.playerHand[gTcgBattleState.playerHandCount - 1]);
            RemoveCardFromPlayerHandAt(gTcgBattleState.playerHandCount - 1);
        }
        if (gTcgBattleState.playerDiscardCount > 0 && gTcgBattleState.playerHandCount < 10)
        {
            u16 rec = gTcgBattleState.playerDiscardPile[--gTcgBattleState.playerDiscardCount];
            gTcgBattleState.playerHand[gTcgBattleState.playerHandCount++] = rec;
        }
        else
        {
            DrawSpecificCardToPlayerHand(FALSE, FALSE, TRUE);
        }
        PlaySE(SE_SELECT);
        success = TRUE;
        break;

    case CARD_POTION:
        if (gBattleMons[battler].hp < gBattleMons[battler].maxHP)
        {
            gBattleMons[battler].hp += 20;
            if (gBattleMons[battler].hp > gBattleMons[battler].maxHP)
                gBattleMons[battler].hp = gBattleMons[battler].maxHP;
            SetMonData(&sPlayerParty[0], MON_DATA_HP, &gBattleMons[battler].hp);
            PlaySE(SE_USE_ITEM);
            success = TRUE;
            break;
        }
        PlaySE(SE_FAILURE);
        return FALSE;

    case CARD_SUPER_POTION:
        if (gBattleMons[battler].hp < gBattleMons[battler].maxHP)
        {
            gBattleMons[battler].hp += 40;
            if (gBattleMons[battler].hp > gBattleMons[battler].maxHP)
                gBattleMons[battler].hp = gBattleMons[battler].maxHP;
            SetMonData(&sPlayerParty[0], MON_DATA_HP, &gBattleMons[battler].hp);
            DiscardEnergyFromSlot(B_SIDE_PLAYER, 0, 1);
            PlaySE(SE_USE_ITEM);
            success = TRUE;
            break;
        }
        PlaySE(SE_FAILURE);
        return FALSE;

    case CARD_FULL_HEAL:
        if (gBattleMons[battler].status1 != 0 || (gBattleMons[battler].status2 & STATUS2_CONFUSION) || gBattleMons[battler].volatiles.confusionTimer > 0)
        {
            gBattleMons[battler].status1 = 0;
            gBattleMons[battler].status2 &= ~STATUS2_CONFUSION;
            gBattleMons[battler].volatiles.confusionTimer = 0;
            u32 zeroStatus = 0;
            SetMonData(&sPlayerParty[0], MON_DATA_STATUS, &zeroStatus);
            PlaySE(SE_USE_ITEM);
            success = TRUE;
            break;
        }
        PlaySE(SE_FAILURE);
        return FALSE;

    case CARD_PLUSPOWER:
        gTcgBattleState.plusPowerBonus[battler] += 10;
        PlaySE(SE_SELECT);
        success = TRUE;
        break;

    case CARD_DEFENDER:
        gTcgBattleState.defenderBonus[battler] += 20;
        PlaySE(SE_SELECT);
        success = TRUE;
        break;

    case CARD_ENERGY_REMOVAL:
        DiscardEnergyFromSlot(B_SIDE_OPPONENT, 0, 1);
        PlaySE(SE_USE_ITEM);
        success = TRUE;
        break;

    case CARD_SUPER_ENERGY_REMOVAL:
        DiscardEnergyFromSlot(B_SIDE_PLAYER, 0, 1);
        DiscardEnergyFromSlot(B_SIDE_OPPONENT, 0, 2);
        PlaySE(SE_USE_ITEM);
        success = TRUE;
        break;

    case CARD_SWITCH:
        for (u32 i = 1; i < MAX_FIELD_POKEMON; i++)
        {
            u16 spec = GetMonData(&sPlayerParty[i], MON_DATA_SPECIES);
            u16 hp = GetMonData(&sPlayerParty[i], MON_DATA_HP);
            if (spec != SPECIES_NONE && hp > 0)
            {
                struct Pokemon temp = sPlayerParty[0];
                sPlayerParty[0] = sPlayerParty[i];
                sPlayerParty[i] = temp;
                SwapSlotEnergies(B_SIDE_PLAYER, 0, i);
                gBattleMons[battler].species = GetMonData(&sPlayerParty[0], MON_DATA_SPECIES);
                gBattleMons[battler].hp = GetMonData(&sPlayerParty[0], MON_DATA_HP);
                gBattleMons[battler].maxHP = GetMonData(&sPlayerParty[0], MON_DATA_MAX_HP);
                gBattleMons[battler].status1 = 0;
                gBattleMons[battler].status2 &= ~STATUS2_CONFUSION;
                for (u8 m = 0; m < MAX_MON_MOVES; m++)
                    gBattleMons[battler].moves[m] = GetMonData(&sPlayerParty[0], MON_DATA_MOVE1 + m);
                PlaySE(SE_SELECT);
                success = TRUE;
                break;
            }
        }
        if (!success)
        {
            PlaySE(SE_FAILURE);
            return FALSE;
        }
        break;

    case CARD_GUST_OF_WIND:
        for (u32 i = 1; i < PARTY_SIZE; i++)
        {
            u16 spec = GetMonData(&sEnemyParty[i], MON_DATA_SPECIES);
            u16 hp = GetMonData(&sEnemyParty[i], MON_DATA_HP);
            if (spec != SPECIES_NONE && hp > 0)
            {
                struct Pokemon temp = sEnemyParty[0];
                sEnemyParty[0] = sEnemyParty[i];
                sEnemyParty[i] = temp;
                SwapSlotEnergies(B_SIDE_OPPONENT, 0, i);
                if (opponent < gBattlersCount)
                {
                    gBattleMons[opponent].species = GetMonData(&sEnemyParty[0], MON_DATA_SPECIES);
                    gBattleMons[opponent].hp = GetMonData(&sEnemyParty[0], MON_DATA_HP);
                    gBattleMons[opponent].maxHP = GetMonData(&sEnemyParty[0], MON_DATA_MAX_HP);
                    gBattleMons[opponent].status1 = 0;
                    for (u8 m = 0; m < MAX_MON_MOVES; m++)
                        gBattleMons[opponent].moves[m] = GetMonData(&sEnemyParty[0], MON_DATA_MOVE1 + m);
                }
                PlaySE(SE_SELECT);
                success = TRUE;
                break;
            }
        }
        if (!success)
        {
            PlaySE(SE_FAILURE);
            return FALSE;
        }
        break;

    case CARD_REVIVE:
    case CARD_MAX_REVIVE:
        for (u32 d = 0; d < gTcgBattleState.playerDiscardCount; d++)
        {
            u16 discCid = gTcgBattleState.playerDiscardPile[d];
            const struct TcgCardInfo *discInfo = GetTcgCardInfo(discCid);
            if (discInfo && discInfo->cardType == CARD_TYPE_POKEMON_BASIC && discInfo->species != SPECIES_NONE)
            {
                for (u8 slot = 1; slot < MAX_FIELD_POKEMON; slot++)
                {
                    if (GetMonData(&sPlayerParty[slot], MON_DATA_SPECIES) == SPECIES_NONE
                     || GetMonData(&sPlayerParty[slot], MON_DATA_HP) == 0)
                    {
                        CreateTempMonFromCardId(&sPlayerParty[slot], discCid);
                        if (cardId == CARD_REVIVE)
                        {
                            u16 halfHp = GetMonData(&sPlayerParty[slot], MON_DATA_MAX_HP) / 2;
                            if (halfHp < 10) halfHp = 10;
                            SetMonData(&sPlayerParty[slot], MON_DATA_HP, &halfHp);
                        }
                        if (slot >= gPartiesCount[B_TRAINER_PLAYER])
                            gPartiesCount[B_TRAINER_PLAYER] = slot + 1;
                        for (u32 k = d; k + 1 < gTcgBattleState.playerDiscardCount; k++)
                            gTcgBattleState.playerDiscardPile[k] = gTcgBattleState.playerDiscardPile[k + 1];
                        gTcgBattleState.playerDiscardCount--;
                        PlaySE(SE_USE_ITEM);
                        success = TRUE;
                        break;
                    }
                }
                if (success)
                    break;
            }
        }
        if (!success)
        {
            // Fallback: heal Active Pokémon by 30 HP if no fainted Basic in discard
            if (gBattleMons[battler].hp < gBattleMons[battler].maxHP)
            {
                u16 heal = (cardId == CARD_MAX_REVIVE) ? gBattleMons[battler].maxHP : (gBattleMons[battler].hp + 30);
                if (heal > gBattleMons[battler].maxHP)
                    heal = gBattleMons[battler].maxHP;
                gBattleMons[battler].hp = heal;
                SetMonData(&sPlayerParty[0], MON_DATA_HP, &heal);
                PlaySE(SE_USE_ITEM);
                success = TRUE;
            }
            else
            {
                PlaySE(SE_FAILURE);
                return FALSE;
            }
        }
        break;

    case CARD_POKE_FLUTE:
        if (gBattleMons[battler].status1 & STATUS1_SLEEP)
            gBattleMons[battler].status1 &= ~STATUS1_SLEEP;
        if (opponent < gBattlersCount && (gBattleMons[opponent].status1 & STATUS1_SLEEP))
            gBattleMons[opponent].status1 &= ~STATUS1_SLEEP;
        PlaySE(SE_USE_ITEM);
        success = TRUE;
        break;

    case CARD_GAMBLER:
        for (u32 i = 0; i < gTcgBattleState.playerHandCount; i++)
        {
            if (gTcgBattleState.playerDeckRemainingCount < DECK_SIZE)
                gTcgBattleState.playerDeckRemaining[gTcgBattleState.playerDeckRemainingCount++] = gTcgBattleState.playerHand[i];
        }
        gTcgBattleState.playerHandCount = 0;
        gTcgBattleState.handScrollOffset = 0;
        if ((Random() & 1) == 0)
            DrawCardsToPlayerHand(8);
        else
            DrawCardsToPlayerHand(1);
        PlaySE(SE_SELECT);
        success = TRUE;
        break;

    case CARD_SCOOP_UP:
    case CARD_SUPER_SCOOP_UP:
        if (cardId == CARD_SUPER_SCOOP_UP && (Random() & 1) != 0)
        {
            PlaySE(SE_FAILURE);
            success = TRUE; // Card consumed on Tails
            break;
        }
        for (u32 i = 1; i < MAX_FIELD_POKEMON; i++)
        {
            if (GetMonData(&sPlayerParty[i], MON_DATA_SPECIES) != SPECIES_NONE && GetMonData(&sPlayerParty[i], MON_DATA_HP) > 0)
            {
                u16 benchCid = GetMonCardId(&sPlayerParty[i]);
                if (benchCid != 0 && gTcgBattleState.playerHandCount < 10)
                    gTcgBattleState.playerHand[gTcgBattleState.playerHandCount++] = benchCid;
                ZeroMonData(&sPlayerParty[i]);
                DiscardEnergyFromSlot(B_SIDE_PLAYER, i, 99);
                PlaySE(SE_SELECT);
                success = TRUE;
                break;
            }
        }
        if (!success)
        {
            PlaySE(SE_FAILURE);
            return FALSE;
        }
        break;

    case CARD_IMAKUNI:
        gBattleMons[battler].status2 |= STATUS2_CONFUSION;
        gBattleMons[battler].volatiles.confusionTimer = 3;
        PlaySE(SE_USE_ITEM);
        success = TRUE;
        break;

    case CARD_POKEMON_CENTER:
        gBattleMons[battler].hp = gBattleMons[battler].maxHP;
        SetMonData(&sPlayerParty[0], MON_DATA_HP, &gBattleMons[battler].maxHP);
        DiscardEnergyFromSlot(B_SIDE_PLAYER, 0, 99);
        for (u32 i = 1; i < MAX_FIELD_POKEMON; i++)
        {
            u16 maxHp = GetMonData(&sPlayerParty[i], MON_DATA_MAX_HP);
            if (GetMonData(&sPlayerParty[i], MON_DATA_SPECIES) != SPECIES_NONE && GetMonData(&sPlayerParty[i], MON_DATA_HP) > 0)
            {
                SetMonData(&sPlayerParty[i], MON_DATA_HP, &maxHp);
                DiscardEnergyFromSlot(B_SIDE_PLAYER, i, 99);
            }
        }
        PlaySE(SE_USE_ITEM);
        success = TRUE;
        break;

    case CARD_SLEEP:
        if ((Random() & 1) == 0 && opponent < gBattlersCount)
        {
            gBattleMons[opponent].status1 |= STATUS1_SLEEP;
            PlaySE(SE_USE_ITEM);
        }
        else
        {
            PlaySE(SE_FAILURE);
        }
        success = TRUE;
        break;

    case CARD_POKEDEX:
    case CARD_FOSSIL_EXCAVATION:
    case CARD_POKEMON_BREEDER:
    case CARD_POKEMON_RETRANSFER:
    case CARD_DEVOLUTION_SPRAY:
    case CARD_MAINTENANCE:
        DrawCardsToPlayerHand(1);
        PlaySE(SE_SELECT);
        success = TRUE;
        break;

    case CARD_RECYCLE:
        if ((Random() & 1) == 0 && gTcgBattleState.playerDiscardCount > 0 && gTcgBattleState.playerHandCount < 10)
        {
            u16 rec = gTcgBattleState.playerDiscardPile[--gTcgBattleState.playerDiscardCount];
            gTcgBattleState.playerHand[gTcgBattleState.playerHandCount++] = rec;
        }
        PlaySE(SE_SELECT);
        success = TRUE;
        break;

    case CARD_NIGHTLY_GARBAGE_RUN:
        for (u8 c = 0; c < 3 && gTcgBattleState.playerDiscardCount > 0 && gTcgBattleState.playerDeckRemainingCount < DECK_SIZE; c++)
        {
            u16 rec = gTcgBattleState.playerDiscardPile[--gTcgBattleState.playerDiscardCount];
            gTcgBattleState.playerDeckRemaining[gTcgBattleState.playerDeckRemainingCount++] = rec;
        }
        PlaySE(SE_SELECT);
        success = TRUE;
        break;

    case CARD_CHALLENGE:
    case CARD_COMPUTER_ERROR:
    case CARD_HERE_COMES_TEAM_ROCKET:
        DrawCardsToPlayerHand(2);
        DrawCardForOpponent();
        PlaySE(SE_SELECT);
        success = TRUE;
        break;

    case CARD_MR_FUJI:
        for (u32 i = 1; i < MAX_FIELD_POKEMON; i++)
        {
            if (GetMonData(&sPlayerParty[i], MON_DATA_SPECIES) != SPECIES_NONE && GetMonData(&sPlayerParty[i], MON_DATA_HP) > 0)
            {
                u16 benchCid = GetMonCardId(&sPlayerParty[i]);
                if (benchCid != 0 && gTcgBattleState.playerDeckRemainingCount < DECK_SIZE)
                    gTcgBattleState.playerDeckRemaining[gTcgBattleState.playerDeckRemainingCount++] = benchCid;
                ZeroMonData(&sPlayerParty[i]);
                DiscardEnergyFromSlot(B_SIDE_PLAYER, i, 99);
                PlaySE(SE_SELECT);
                success = TRUE;
                break;
            }
        }
        if (!success)
        {
            PlaySE(SE_FAILURE);
            return FALSE;
        }
        break;

    case CARD_GOOP_GAS_ATTACK:
        gTcgBattleState.goopGasActive[B_SIDE_OPPONENT] = TRUE;
        PlaySE(SE_USE_ITEM);
        success = TRUE;
        break;

    case CARD_DIGGER:
        if (opponent < gBattlersCount && (Random() & 1) == 0)
        {
            if (gBattleMons[opponent].hp > 10)
                gBattleMons[opponent].hp -= 10;
            else
                gBattleMons[opponent].hp = 1;
            SetMonData(&sEnemyParty[gBattlerPartyIndexes[opponent]], MON_DATA_HP, &gBattleMons[opponent].hp);
        }
        else if (gBattleMons[battler].hp > 10)
        {
            gBattleMons[battler].hp -= 10;
            SetMonData(&sPlayerParty[0], MON_DATA_HP, &gBattleMons[battler].hp);
        }
        PlaySE(SE_USE_ITEM);
        success = TRUE;
        break;

    case CARD_LASS:
    case CARD_IMPOSTER_PROF_OAK:
    case CARD_IMPOSTER_OAK_REVENGE:
    case CARD_ROCKET_SNEAK_ATTACK:
    case CARD_THE_ROCKETS_TRAP:
        if (gTcgBattleState.opponentHandCount > 0)
            gTcgBattleState.opponentHandCount--;
        PlaySE(SE_SELECT);
        success = TRUE;
        break;

    default:
        PlaySE(SE_SELECT);
        success = TRUE;
        break;
    }

    if (success)
    {
        if (info->cardType == CARD_TYPE_TRAINER_SUPPORTER)
            gTcgBattleState.supporterUsedThisTurn = 1;
        RecordDiscardedCard(B_SIDE_PLAYER, cardId);
    }

    return success;
}
