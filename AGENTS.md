# AGENTS.md - Offline Minigames Expansion (Pokémon Jump & Dodrio's Berry Picking)

This document provides a comprehensive technical overview and architectural guide of the offline/solo implementation for **Pokémon Jump** and **Dodrio's Berry Picking** in Mossdeep City Game Corner (`pokeemerald-expansion`). It details the design decisions, bug fixes, AI bot mechanics, and file structure for any developer or AI assistant maintaining or extending this codebase.

---

## 1. Overview & Objectives

In vanilla Pokémon Emerald, the Game Corner on 1F of Mossdeep City offers two wireless minigames:
1. **Pokémon Jump** (up to 5 players)
2. **Dodrio's Berry Picking** (up to 5 players)

In the original game, both minigames strictly required a Game Boy Advance Wireless Adapter and at least one other connected player, rendering them inaccessible in single-player or emulators without network link configurations.

### Key Goals:
- **Solo Play with AI Companions:** Allow playing completely offline without a Wireless Adapter or link partners.
- **Maximum Participant Support:** Run both minigames with the full 5-player maximum (`MAX_RFU_PLAYERS = 5`), populating positions 1 through 4 with intelligent CPU-controlled Pokémon / Dodrios.
- **Wireless Multiplayer Intact:** Keep the original Wireless Link flow fully functional for when players want to play via Wireless Adapter.
- **Difficulty Selection:** Offer *Normal* and *Hard* difficulty settings prior to launching the minigame (in addition to the games' natural progressive speed curves).
- **Graceful Save and Exit:** Integrate offline saving (`Task_LinkFullSave`) and proper overworld map warp return triggers when exiting the minigames.

---

## 2. Architecture & Flow

### 2.1. Dialogue & Menu Flow (`data/scripts/cable_club.inc`)
When speaking with the Old Man attendant at Mossdeep Game Corner 1F:
1. Attendant greets the player and displays `MULTI_WIRELESS_MINIGAME` ("POKéMON JUMP", "DODRIO BERRY-PICKING", "EXIT").
2. The script checks party eligibility first:
   - For Pokémon Jump: `special IsPokemonJumpSpeciesInParty` checks if the player owns a jumping-eligible species $\le$ 28 inches without ungrounded movement.
   - For Dodrio Berry Picking: `special IsDodrioInParty` verifies if Dodrio is in the party.
   - If not met, the attendant offers an explanation of the entry requirements.
3. If requirements are met, the attendant asks:
   > *"Which mode would you like to play?"* (`MossdeepCity_GameCorner_1F_Text_PlaySoloOrLink`)
   - `MULTI_MINIGAME_MODE`:
     - **SOLO PLAY**
     - **WIRELESS LINK**
     - **EXIT**
4. **Wireless Link Path:**
   - Validates `IsWirelessAdapterConnected`. If disconnected, informs the player to hook up the adapter.
   - If connected, selects Pokémon, saves game, and enters group selection (`LINK_LEADER` / `LINK_MEMBER`), identically to vanilla multiplayer.
5. **Solo Play Path:**
   - Prompts for difficulty: *"Please select a difficulty level."* (`MossdeepCity_GameCorner_1F_Text_ChooseDifficulty`)
   - `MULTI_MINIGAME_DIFFICULTY`:
     - **NORMAL** (value 0)
     - **HARD** (value 1)
     - **EXIT**
   - Stores chosen difficulty into `VAR_0x8006`.
   - Player selects their entering Pokémon via `special ChooseMonForWirelessMinigame`.
   - The selected slot (`VAR_0x8004`) is protected in temporary variable `VAR_0x8008` across `Common_EventScript_SaveGame`.
   - Attendant opens the barrier (`EventScript_OpenMossdeepGameCornerBarrier`), player walks into the minigame room, and the respective solo special is triggered (`special StartPokemonJumpSolo` or `special StartDodrioBerryPickingSolo`).

---

## 3. Pokémon Jump (`src/pokemon_jump.c`)

### 3.1. Initialization & Memory Fixes
- **Uninitialized Memory & Assert Prevention:**
  - `sPokemonJump` is allocated via `AllocZeroed(sizeof(*sPokemonJump))` instead of `Alloc`.
  - In solo mode, `InitSoloPokeJumpPlayers()` is executed immediately upon allocation *before* calling `InitGame(sPokemonJump)`. This ensures `monInfo[1..4]` are assigned valid species IDs (`SPECIES_PIKACHU`, `SPECIES_EEVEE`, `SPECIES_TORCHIC`, `SPECIES_SKITTY`) rather than random garbage heap memory. This prevents `assertf(species <= NUM_SPECIES)` inside `SanitizeSpeciesId()` from throwing a blue screen error.
- **Player Count & Sprite Rendering:**
  - `GetNumPokeJumpPlayers()` returns `sIsSoloMinigame ? MAX_RFU_PLAYERS : GetLinkPlayerCount()`.
  - In vanilla, `GetNumPokeJumpPlayers()` returned `GetLinkPlayerCount()` which is 0 or 1 in offline play, causing `sMonXCoords[playersCount - 2]` to access invalid memory and skipping the sprite creation loop entirely (rendering Pokémon invisible). Returning `MAX_RFU_PLAYERS = 5` creates all 5 Pokémon sprites at positions `{56, 88, 120, 152, 184}` alongside star particles and player name windows.

### 3.2. CPU AI Logic (`UpdateCpuJumpStates`)
- Each CPU Pokémon (`sPokemonJump->players[1..4]`) monitors the Venusaur rope swing state (`sPokemonJump->vineState`):
  - When the rope reaches `VINE_LOWEST` or `VINE_UPSWING_LOWER`, a jump is initiated.
  - In **Normal Mode**, bots jump with a minor realistic reaction margin.
  - In **Hard Mode**, bots jump immediately on frame at optimal velocity.
  - When landing (`jumpOffset == 0`), CPU mon states reset to `MONSTATE_NORMAL` and successfully clear the rope, allowing the team to build streaks and bonus multipliers.

---

## 4. Dodrio Berry Picking (`src/dodrio_berry_picking.c`)

### 4.1. Sprite Synchronization Fix
- **Falling Berry Visibility:**
  - The leader updates berries in `sGame->player.berries` while `UpdateBerrySprites()` reads `sGame->players[sGame->multiplayerId].berries`.
  - In wireless mode, `sGame->players[0].berries` was populated exclusively by incoming wireless network packets.
  - In solo mode without network packets, `sGame->players[0].berries` remained zeroed, causing `UpdateBerrySprites()` to treat all berries as invisible (`SetBerryInvisibility(i, TRUE)`).
  - Explicit synchronization `sGame->players[0].berries = sGame->player.berries;` was added inside `UpdateBerrySprites()`, `InitFirstWaveOfBerries()`, `RecvLinkData_Gameplay()`, and `RecvLinkData_ReadyToEnd()`, restoring full visibility, falling animations, and collision sounds.

### 4.2. CPU AI Logic (`UpdateCpuDodrioPickStates`)
- Dodrios 1 through 4 have 3 heads mapped to falling berry columns:
  - Dodrio 0 (Player): Left 4, Mid 5, Right 6
  - Dodrio 1 (CPU 1): Left 6, Mid 7, Right 8
  - Dodrio 2 (CPU 2): Left 8, Mid 9, Right 0
  - Dodrio 3 (CPU 3): Left 0, Mid 1, Right 2
  - Dodrio 4 (CPU 4): Left 2, Mid 3, Right 4
- **Decision Hierarchy:**
  1. **Middle Column (Exclusive):** Highest priority. When a falling berry is within reach (`fallDist == 6 || fallDist == 7`), the middle head strikes.
  2. **Shared Columns with Player 0 (Cols 4 and 6):**
     - Col 6 is shared between Player 0 (Right) and CPU 1 (Left).
     - Col 4 is shared between Player 0 (Left) and CPU 4 (Right).
     - **Player-First Courtesy:** CPU bots wait until `fallDist == 7` before attempting to catch berries in cols 4 and 6. This gives human Player 0 the opportunity to catch them first at `fallDist == 6`. If the player misses or is busy, the CPU saves the berry at `fallDist == 7` to avoid status bar penalty.
  3. **Shared Columns between Bots (Cols 8, 0, 2):** Caught cleanly at `fallDist == 6 || 7`.

### 4.3. Difficulty Effects
- **Normal:** Standard initial difficulty stage (stage 0). Berries fall at base speed and difficulty increments naturally as berries are eaten.
- **Hard:** Starts at difficulty stage 14 (advances by two full cycles of 7 difficulty stages), triggering faster fall delay stages and higher proportion of fast/special berries from the first second.

---

## 5. Key Source Files Modified

| File | Changes |
|---|---|
| `include/constants/script_menu.h` | Added `MULTI_MINIGAME_MODE` and `MULTI_MINIGAME_DIFFICULTY`. |
| `src/data/script_menu.h` | Registered string options for solo/wireless mode and normal/hard difficulty multichoices. |
| `data/text/cable_club.inc` | Added `MossdeepCity_GameCorner_1F_Text_PlaySoloOrLink` and `MossdeepCity_GameCorner_1F_Text_ChooseDifficulty`. |
| `data/scripts/cable_club.inc` | Updated Old Man script to offer mode selection, difficulty selection, Pokémon selection, barrier animation, and solo entry points. |
| `data/specials.inc` | Registered `StartPokemonJumpSolo` and `StartDodrioBerryPickingSolo` with `waitstate=1`. |
| `include/pokemon_jump.h` | Declared `StartPokemonJumpSolo(void)`. |
| `src/pokemon_jump.c` | Implemented solo startup, `AllocZeroed` memory safety, bot initialization before `InitGame`, sprite count override in `GetNumPokeJumpPlayers()`, and CPU jump AI. |
| `include/dodrio_berry_picking.h` | Declared `StartDodrioBerryPickingSolo(void)`. |
| `src/dodrio_berry_picking.c` | Implemented solo startup, CPU Dodrio setup, berry sprite sync in `UpdateBerrySprites()`, and column-aware cooperative AI. |

---

## 6. Build Instructions

To build the ROM:
```bash
make -j4
```
Outputs `pokeemerald.gba` cleanly.
