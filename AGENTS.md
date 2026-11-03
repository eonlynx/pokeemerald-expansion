# AGENTS.md - Offline Minigames Expansion (Pokémon Jump, Dodrio's Berry Picking & Berry Crush)

This document provides a comprehensive technical overview and architectural guide of the offline/solo implementation for **Pokémon Jump**, **Dodrio's Berry Picking**, and **Berry Crush** in Mossdeep City Game Corner (`pokeemerald-expansion`). It details the design decisions, bug fixes, AI bot mechanics, and file structure for any developer or AI assistant maintaining or extending this codebase.

---

## 1. Overview & Objectives

In vanilla Pokémon Emerald, the Game Corner on 1F of Mossdeep City (`MAP_MOSSDEEP_CITY_GAME_CORNER_1F`) offers two wireless minigames:
1. **Pokémon Jump** (up to 5 players)
2. **Dodrio's Berry Picking** (up to 5 players)

Meanwhile, **Berry Crush** (up to 5 players) was traditionally only accessible in the Direct Corner on 2F of Pokémon Centers (and FireRed/LeafGreen).

In the original game, all three minigames strictly required a Game Boy Advance Wireless Adapter and at least one other connected human player, rendering them inaccessible in single-player or emulators without network link configurations.

### Key Goals:
- **Unified Minigame Hub:** Bring all three wireless minigames—**Pokémon Jump**, **Dodrio's Berry Picking**, and **Berry Crush**—together into the **Mossdeep City Game Corner**.
- **Solo Play with AI Companions:** Allow playing completely offline without a Wireless Adapter or link partners.
- **Maximum Participant Support:** Run all minigames with the full 5-player maximum (`MAX_RFU_PLAYERS = 5`), populating positions 1 through 4 with intelligent CPU-controlled Pokémon / Dodrios / Trainers (`LADDIE`, `LASSIE`, `DUDE`, `MISS`).
- **Authentic Atmosphere & Dialogue:** Welcoming greeting mentioning **MOSSDEEP CITY GAME CORNER** without awkward artificial delays or connection-checking text.
- **Difficulty Selection:** Offer *Normal* and *Hard* difficulty settings prior to launching Pokémon Jump and Dodrio's Berry Picking. (Berry Crush is purely cooperative and runs at a balanced, natural cadence without a redundant difficulty prompt).
- **Graceful Save and Exit:** Integrate offline saving (`Task_LinkFullSave`) and proper overworld map warp return triggers (`USING_MINIGAME` at coordinates `5, 1`) when exiting the minigames.
- **Wireless Multiplayer Intact:** Keep the original Wireless Link flow fully functional for when players choose to play via Wireless Adapter.

---

## 2. Architecture & Flow

### 2.1. Dialogue & Menu Flow (`data/scripts/cable_club.inc`)
When speaking with the Old Man attendant at Mossdeep City Game Corner 1F:
1. Attendant greets the player:
   > *"Hi, welcome to the MOSSDEEP CITY GAME CORNER!\pWhich game would you like to play?"* (`MossdeepCity_GameCorner_1F_Text_Welcome`)
2. Displays 4-option menu `MULTI_MOSSDEEP_MINIGAME`:
   - **POKéMON JUMP**
   - **DODRIO BERRY-PICKING**
   - **BERRY CRUSH**
   - **EXIT**
3. Eligibility checks:
   - **Pokémon Jump:** `special IsPokemonJumpSpeciesInParty` verifies eligible species $\le$ 28 inches without ungrounded movement.
   - **Dodrio Berry Picking:** `special IsDodrioInParty` checks if Dodrio is in the party.
   - **Berry Crush:** `checkitem ITEM_POWDER_JAR` checks if player owns a Powder Jar, and `special HasAtLeastOneBerry` ensures at least one Berry is in the Bag. If Powder Jar is missing, the attendant explains what is required (`MossdeepCity_GameCorner_1F_Text_PowderJarInfo`) without spoiling secret item locations.
4. If requirements are met, attendant asks:
   > *"Which mode would you like to play?"* (`MossdeepCity_GameCorner_1F_Text_PlaySoloOrLink`)
   - `MULTI_MINIGAME_MODE`:
     - **SOLO PLAY**
     - **WIRELESS LINK**
     - **EXIT**
5. **Wireless Link Path:**
   - Validates `IsWirelessAdapterConnected`. If disconnected, informs player to hook up the adapter.
   - If connected, selects Pokémon (for Jump/Dodrio), saves game, and enters group selection (`LINK_LEADER` / `LINK_MEMBER`), identically to vanilla multiplayer.
   - In `src/union_room.c`, `ACTIVITY_BERRY_CRUSH` detects if launched from Mossdeep City Game Corner and warps back to `(USING_MINIGAME, 5, 1)` rather than Pokémon Center 2F.
6. **Solo Play Path:**
   - For **Pokémon Jump** and **Dodrio Berry Picking**: Prompts for difficulty:
     - `MULTI_MINIGAME_DIFFICULTY`: **NORMAL** (0) or **HARD** (1).
     - Player selects their entering Pokémon via `special ChooseMonForWirelessMinigame`.
     - Party slot `VAR_0x8004` is preserved in `VAR_0x8008` across `Common_EventScript_SaveGame`.
   - For **Berry Crush**: Jumps straight into Solo Play (setting difficulty to 0) and saves the game without redundant difficulty or Pokémon selection menus.
   - Attendant opens the barrier (`EventScript_OpenMossdeepGameCornerBarrier`), player walks into the minigame room, and the respective solo special is triggered (`special StartPokemonJumpSolo`, `special StartDodrioBerryPickingSolo`, or `special StartBerryCrushSolo`).

### 2.2. Info Desk (`MossdeepCity_GameCorner_1F_EventScript_InfoMan2`)
The Info Man provides rule explanations for all 3 games:
- Pokémon Jump (`MossdeepCity_GameCorner_1F_Text_PokemonJumpInfo`)
- Dodrio Berry Picking (`MossdeepCity_GameCorner_1F_Text_DodrioBerryPickingInfo`)
- Berry Crush (`MossdeepCity_GameCorner_1F_Text_BerryCrushInfo`): Explains pressing A rhythmically to crush berries into Berry Powder, requiring a Powder Jar and berries.

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

## 5. Berry Crush (`src/berry_crush.c`)

### 5.1. Solo Startup & RFU Decoupling
- **`StartBerryCrushSolo(void)`:** Sets `sIsSoloMinigame = TRUE`, configures `VAR_CABLE_CLUB_STATE` to `USING_MINIGAME`, warps to coordinates `(5, 1)`, sets wireless comm type 0, and starts the game with `CB2_LoadMap`.
- **Decoupled Link Hooks:** In solo mode, RFU handshake waits (`Rfu_SetLinkStandbyCallback`, `IsLinkTaskFinished`, `SendBlock`) are cleanly bypassed during palette fade, berry dropping, crusher lid fall, countdown, results tabulation, saving, and exiting.
- **Simulated Teammates:** 4 CPU companions (`LADDIE`, `LASSIE`, `DUDE`, `MISS`) join the game. In `Cmd_WaitForOthersToPickBerries`, each contributes a berry (`BERRY_CHERI`, `BERRY_CHESTO`, `BERRY_PECHA`, `BERRY_RAWST`), calculating total target A presses and powder amount.

### 5.2. CPU AI & Button Mashing Logic (`HandleSoloGameLeader`)
- Berry Crush is a purely cooperative minigame where players push down the crusher before the timer runs out.
- Each CPU companion has its own cadence timer (`sCpuPressTimers[i - 1]`):
  - Every 7 to 12 frames (averaging ~9.5 frames, or ~6.3 presses/sec per bot), the bot presses A.
  - Bots simulate realistic button holds (`sCpuHoldTimers[i - 1] = 2`) to accumulate natural "pressing power" time.
  - This results in a healthy team pace of ~30-38 presses/sec, scoring neat streaks and synchronous hits while leaving ample room for player skill to shine and beat high scores.
- `localState` is directly copied to `recvCmd` so impact sprites, vibrations, big sparkles, and sound effects trigger dynamically on frame.
- **Results & Powder Reward:** Results pages (Presses, Neatness/Coop/Power, Powder amount) are tabulated and sorted normally. `SaveResults()` awards the player their earned Berry Powder via `GiveBerryPowder()` and saves 5-player speed records to save block 2.

---

## 6. Key Source Files Modified

| File | Changes |
|---|---|
| `include/constants/script_menu.h` | Added `MULTI_MINIGAME_MODE`, `MULTI_MINIGAME_DIFFICULTY`, and `MULTI_MOSSDEEP_MINIGAME`. |
| `src/data/script_menu.h` | Registered `sMultichoiceList_MossdeepMinigame` (4 options: Pokémon Jump, Dodrio Berry-Picking, Berry Crush, Exit) and registered in `sMultichoiceLists`. |
| `data/text/cable_club.inc` | Added `MossdeepCity_GameCorner_1F_Text_Welcome` (welcoming to MOSSDEEP CITY GAME CORNER), `MossdeepCity_GameCorner_1F_Text_BerryCrushInfo`, `MossdeepCity_GameCorner_1F_Text_ExplainPowderJar`, and `MossdeepCity_GameCorner_1F_Text_PowderJarInfo`. |
| `data/scripts/cable_club.inc` | Updated Old Man and Info Man to use `MULTI_MOSSDEEP_MINIGAME`; added Powder Jar and berry checks for Berry Crush; added direct Solo Play start for Berry Crush; added solo barrier and start routines. |
| `data/specials.inc` | Registered `StartPokemonJumpSolo`, `StartDodrioBerryPickingSolo`, and `StartBerryCrushSolo` with `waitstate=1`. |
| `include/pokemon_jump.h` | Declared `StartPokemonJumpSolo(void)`. |
| `src/pokemon_jump.c` | Implemented solo startup, `AllocZeroed` memory safety, bot initialization before `InitGame`, sprite count override in `GetNumPokeJumpPlayers()`, and CPU jump AI. |
| `include/dodrio_berry_picking.h` | Declared `StartDodrioBerryPickingSolo(void)`. |
| `src/dodrio_berry_picking.c` | Implemented solo startup, CPU Dodrio setup, berry sprite sync in `UpdateBerrySprites()`, and column-aware cooperative AI. |
| `include/berry_crush.h` | Declared `StartBerryCrushSolo(void)`. |
| `src/berry_crush.c` | Implemented solo startup, CPU teammate simulation, RFU decoupling, button mashing AI, and results saving. |
| `src/union_room.c` | Configured `ACTIVITY_BERRY_CRUSH` to return to Mossdeep Game Corner barrier `(USING_MINIGAME, 5, 1)` when played in Mossdeep. |

---

## 7. Build Instructions

To build the ROM:
```bash
make -j4
```
Outputs `pokeemerald.gba` cleanly.
