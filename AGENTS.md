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
- **Maximum Participant Support:** Run all minigames with the full 5-player maximum (`MAX_RFU_PLAYERS = 5`), populating positions with intelligent CPU-controlled Pokémon / Dodrios / Trainers dynamically chosen from the full authentic Berry Blender cast (`MISTER`, `LADDIE`, `LASSIE`, `DUDE`, `MISS`, and `MASTER`).
- **Authentic Atmosphere & Dialogue:** Welcoming greeting mentioning **MOSSDEEP GAME CORNER** without awkward artificial delays or connection-checking text.
- **Difficulty Selection & Opponents:**
  - **Pokémon Jump:** Purely cooperative jumping rope. If ANY Pokémon touches the rope, `UpdateVineHitStates()` returns `FALSE` and triggers an immediate `FUNC_GAME_OVER` for the entire party. A weaker AI would cause frustrating, unavoidable losses for the human player. Therefore, difficulty selection is completely removed (single unified balanced mode where bots jump in sync with staggered human micro-delays). Player position is randomized across the 5 spots ($0..4$) rather than being stuck on the far left. Opponent Pokémon are dynamically picked from a pool of 21 authentic jumping species. Blend Master (`MASTER`) appears cosmetically with a rare 5% rate with sharp timing.
  - **Berry Crush:** Purely cooperative button mashing with shared Berry Powder reward ($B \times S \times P$). Better bots only help the team, and difficulty selection is eliminated in favor of an authentic 8-tier Daily Berry Lottery system based on player berry anchoring and daily RTC seeds. Blend Master (`MASTER`) appears only on the first game of the day if a berry of Tier 5 or higher is in play, mashing at top human cadence (12 presses/sec).
  - **Dodrio Berry Picking:** Highly competitive for 1st place (only top score wins a berry), yet drops penalize the shared status bar. Player position is preserved at the bottom-center controls position identically to multiplayer. Difficulty selection (**NORMAL** vs **HARD**) is maintained so players can choose their competitive challenge. Blend Master (`MASTER`) appears as an opponent 5% of the time on Normal mode and 10% of the time on Hard mode using advanced competitive AI.
- **Graceful Save and Exit:** Fixed softlock in `Task_LinkFullSave` (`src/save.c`) which previously stalled forever waiting for wireless link standby packets in offline play. Also removed out-of-place link standby and "A member dropped out" messages when exiting solo Berry Crush and Pokémon Jump. Offline games now save sector-by-sector to flash memory and transition smoothly back to the overworld.
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

### 3.2. CPU AI Logic, Dynamic Positions & Species Pool (`UpdateCpuJumpStates`, `InitSoloPokeJumpPlayers`)
- Each CPU Pokémon monitors the Venusaur rope swing state (`sPokemonJump->vineState`):
  - **Human Reaction Staggering:** Rather than jumping on the exact identical frame, each CPU receives a small natural reaction delay (0 to 2 frames) as the vine reaches `VINE_LOWEST`.
  - Sprites take off with organic, believable stagger rather than robotic unison.
  - Jump heights remain well above ground level during the `VINE_UPSWING_LOWER` collision check, guaranteeing that CPUs never trip the rope.
  - Peak jump intervals (`JUMP_PEAK`) overlap dynamically with other CPUs and the player, awarding authentic synchronization combos.
  - **Randomized Player Position:** In multiplayer, clients were placed at positions 1 through 4 depending on join order. In solo play, `sPokemonJump->multiplayerId` is now randomized among positions 0 through 4 (`Random() % MAX_RFU_PLAYERS`), so the human player no longer always stands on the far left. The name window and sprite highlighting adapt automatically.
  - **Failure Handling Across All Positions:** Fixed a softlock where `GameOver_Leader` and `UpdateVineHitStates` previously looped `for (i = 1; i < sPokemonJump->numPlayers; i++)`, which assumed the human was always player 0. If the player was in slots 1 through 4, slot 0 remained in `JUMPSTATE_NONE`, causing `AllPlayersJumpedOrHit()` to hang indefinitely. Both loops now iterate through all CPU slots `i != multiplayerId`.
  - **Expanded Species Variety:** Instead of the same 4 hardcoded Pokémon every match, CPUs are dynamically populated by choosing 4 unique Pokémon from a pool of 21 verified jumping species (Pikachu, Eevee, Torchic, Treecko, Mudkip, Skitty, Plusle, Minun, Clefairy, Jigglypuff, Meowth, Psyduck, Poliwag, Marill, Togepi, Wooper, Bulbasaur, Charmander, Squirtle, Bellossom, Pichu). A safety fallback in `InitPlayerAndJumpTypes` ensures any unforeseen species without jump tables defaults to `PKMN_JUMP_TYPE_NORMAL` so sprites never freeze.
  - **Blender Names & Rare MASTER Appearance:** Opponent names are selected from the 5 regular Berry Blender characters (`MISTER`, `LADDIE`, `LASSIE`, `DUDE`, `MISS`). Blend Master (`MASTER`) appears cosmetically with a rare 5% rate with sharp reaction timing (0-frame reaction delay).
  - **Clean Solo Exit:** In `DoPlayAgainPrompt()`, declining to play again skips `GFXFUNC_MSG_COMM_STANDBY`, avoiding the out-of-place "COMMUNICATION STANDBY..." text.
  - **Single Unified Mode:** The leftover `sSoloDifficulty` variable was completely eliminated; Pokémon Jump operates in a single, balanced mode.

---

## 4. Dodrio Berry Picking (`src/dodrio_berry_picking.c`)

### 4.1. Sprite Synchronization Fix
- **Falling Berry Visibility:**
  - The leader updates berries in `sGame->player.berries` while `UpdateBerrySprites()` reads `sGame->players[sGame->multiplayerId].berries`.
  - In wireless mode, `sGame->players[0].berries` was populated exclusively by incoming wireless network packets.
  - In solo mode without network packets, `sGame->players[0].berries` remained zeroed, causing `UpdateBerrySprites()` to treat all berries as invisible (`SetBerryInvisibility(i, TRUE)`).
  - Explicit synchronization `sGame->players[0].berries = sGame->player.berries;` was added inside `UpdateBerrySprites()`, `InitFirstWaveOfBerries()`, `RecvLinkData_Gameplay()`, and `RecvLinkData_ReadyToEnd()`, restoring full visibility, falling animations, and collision sounds.

### 4.2. CPU AI Logic, Blend Master & Difficulty Calibration (`UpdateCpuDodrioPickStates`)
- Dodrios 1 through 4 have 3 heads mapped to falling berry columns:
  - Dodrio 0 (Player): Left 4, Mid 5, Right 6
  - Dodrio 1 (CPU 1): Left 6, Mid 7, Right 8
  - Dodrio 2 (CPU 2): Left 8, Mid 9, Right 0
  - Dodrio 3 (CPU 3): Left 0, Mid 1, Right 2
  - Dodrio 4 (CPU 4): Left 2, Mid 3, Right 4
- **Difficulty & Reaction Modeling:**
  - **Normal Mode:**
    - Standard opponents: `LADDIE`, `LASSIE`, `DUDE`, `MISS`.
    - In middle exclusive columns, CPUs exhibit human reaction distribution: 65% caught at `fallDist == 6`, 35% caught at `fallDist == 7`. 100% of berries are saved from squishing, but without robotic frame-0 snatching.
    - On shared columns with Player 0 (cols 4 and 6), CPUs hold back at `fallDist == 6` to let the human player score, only catching at `fallDist == 7` if the player missed.
    - Yields a balanced, winnable match where the human player can win 1st place.
  - **Hard Mode:**
    - CPU 1 is assigned as the **Blend Master** (`MASTER`).
    - Berries fall at accelerated velocity (difficulty stage 14).
    - CPUs are sharp and competitive: they catch decisively at `fallDist == 6` and contest shared columns with 40% aggression, putting up a genuine challenge for 1st place using the pre-existing advanced AI.

### 4.3. Replay Persistence & Multi-Round Fix (`ResetGame`)
- In solo play, selecting "Yes" to "Play again?" previously reset `sGame->numPlayers = 1` because `gReceivedRemoteLinkPlayers` was FALSE, causing all 4 companion Dodrios to vanish in round 2.
- `ResetGame()` was patched to guard against solo play (`if (!gReceivedRemoteLinkPlayers && !sIsSoloMinigame)`) and recalculate active berry columns with `GetActiveBerryColumns(...)`, allowing endless replay rounds with all 5 Dodrios active.
- To ensure consistent behavior matching Pokémon Jump and Berry Crush, opponent roster initialization (`InitSoloDodrioPlayers()`) is run only once on game start. Replay rounds maintain the exact same opponent Dodrios and names; players only change when exiting and re-entering the minigame.

---

## 5. Berry Crush (`src/berry_crush.c`)

### 5.1. Solo Startup, RFU Decoupling & Replay Persistence
- **`StartBerryCrushSolo(void)`:** Sets `sIsSoloMinigame = TRUE`, configures `VAR_CABLE_CLUB_STATE` to `USING_MINIGAME`, warps to coordinates `(5, 1)`, sets wireless comm type 0, and starts the game with `CB2_LoadMap`.
- **Decoupled Link Hooks & Clean Exit:**
  - In solo mode, RFU handshake waits (`Rfu_SetLinkStandbyCallback`, `IsLinkTaskFinished`, `SendBlock`) are cleanly bypassed during palette fade, berry dropping, crusher lid fall, countdown, results tabulation, saving, and exiting.
  - When the player selects "NO" on the "Play again?" prompt, offline solo play bypasses `MSG_COMM_STANDBY` ("COMMUNICATION STANDBY...") and `MSG_DROPPED` ("A member dropped out"), transitioning immediately to link cleanup and fading back to the overworld.
- **Persistent Player Names Across Rounds & Berry Selection:**
  - In the original implementation, CPU names were re-randomized after exiting the Berry Pouch (`ChooseCpuBerries`), causing the opponent nameplates to change mid-game.
  - CPU names are now set once during initial startup in `SetNamesAndTextSpeed()` and remain strictly consistent throughout the entire session.
  - If Blend Master (`MASTER`) was assigned for the daily first play, in subsequent replay rounds `ResetGame()` reverts that slot back to `MISTER` so `MASTER` only plays on the daily lucky run.
- **Replay Freeze Fix in Round 2:**
  - In `HandleSoloGameLeader`, `memcpy(game->recvCmd, &game->localState, sizeof(game->recvCmd))` previously wrote at offset 0 of `recvCmd`. Because `struct BerryCrushGame_LinkState` has `u16 rfuCmd` at offset 0 while `struct BerryCrushGame_LocalState` does not, this shifted all fields by 2 bytes and copied 2 bytes past `localState` into `sparkleAmount`.
  - In round 2, this read the previous match's powder (>1000) into `sparkleAmount`, causing `UpdateInputEffects()` to iterate hundreds of times over `gfx->sparkleSprites[11]` and dereference invalid memory, instantly locking up the GBA on the first A press of round 2.
  - Fixed by populating `game->recvCmd[0] = RFUCMD_SEND_PACKET;` and copying `sizeof(game->localState)` to `&game->recvCmd[1]`, clamping `maxSparkles = min(ARRAY_COUNT(gfx->sparkleSprites), ...)`, guarding against division by zero in sparkle x-coords, and fully zeroing `results`, `localState`, and `recvCmd` in `ResetGame()`.
- **Simulated Teammates, Authentic Names & 8-Tier Berry Selection (`ChooseCpuBerries`):**
  - 4 CPU companions join the game using authentic Berry Blender names (`LADDIE`, `LASSIE`, `DUDE`, `MISS`).
  - **Blend Master Condition:** The Blend Master (`MASTER`) appears **only** on the first game of the day (`!FlagGet(FLAG_DAILY_BERRY_CRUSH_RECEIVED_BONUS)`) if any berry in play (either chosen by the player or rolled by a CPU) is Tier 5 or higher (`highestCpuTier >= 5 || playerTier >= 5`).
  - The CPU with the highest tier is designated as `MASTER` and receives the fastest human mashing cadence (`cadence = 5`, ~12 presses/sec).
  - Subsequent games or games with lower tiers retain standard Berry Blender names.
  - **Player Berry Anchoring:** The base berry tier of all CPUs is anchored to the player's chosen berry tier (Tier 0 to Tier 7).
  - **General Sub-Roll (Every Game):** Each CPU independently has an 18.8% chance to elevate tiers above the player's berry tier:
    - +7 Tiers: 0.1%
    - +6 Tiers: 0.2%
    - +5 Tiers: 0.5%
    - +4 Tiers: 1.0%
    - +3 Tiers: 2.0%
    - +2 Tiers: 5.0%
    - +1 Tier: 10.0%
    - +0 Tier (Player's Tier): 81.2% (clamped at Tier 7).
  - **First Game of the Day (Daily Guaranteed High Tier):**
    - Uses `gSaveBlock1Ptr->dailySeed` for a deterministic lottery roll per CPU (anti-reroll across soft resets):
      - Tier 7: 5% (Lansat, Starf)
      - Tier 6: 5% (Liechi, Ganlon, Salac, Petaya, Apicot)
      - Tier 5: 10% (Spelon, Pamtre, Watmel, Durin, Belue)
      - Tier 4: 30% (Tamato, Cornn, Magost, Rabuta, Nomel)
      - Tier 3: 50% (Pomeg, Kelpsy, Qualot, Hondew, Grepa)
    - **Most Favorable Outcome Rule:** `max(normalTier, dailyTier)` ensures that if the player invests in a higher-tier berry (e.g. Tier 6), the daily roll will never downgrade the CPUs below what the standard roll produces.
    - Consuming the daily roll sets `FLAG_DAILY_BERRY_CRUSH_RECEIVED_BONUS`.
  - (Enigma Berry is excluded from CPU selection).

### 5.2. Human Button Mashing & Cadence Scaling (`HandleSoloGameLeader`, `InitCpuPressCadence`)
- **Berry Difficulty & Target Press Scaling:**
  - Base cadence scales dynamically with total target presses:
    - $\le 350$ presses (Tier 0-1): 9 frames (~6.7 presses/sec).
    - $351-550$ presses (Tier 2-3): 8 frames (~7.5 presses/sec).
    - $551-800$ presses (Tier 4-5): 7 frames (~8.6 presses/sec).
    - $> 800$ presses (Tier 6-7): 6 frames (~10.0 presses/sec).
- **Lucky Daily Roll Reward:**
  - If a CPU was awarded a rare berry from the daily roll (Tier 4+ or 6+), it receives a motivation boost (reducing cadence by 1-2 frames), rewarding the player with faster times and massive powder!
- **Human Rhythm & Streak Modeling:**
  - Rather than randomized intervals on every press, CPUs maintain steady cadence for streaks of 5 to 10 presses within $\pm 1$ frame, generating authentic human "Neatness" scores (40%–70%).
  - Periodic micro-drifts simulate natural human fatigue.
  - Button holds are modeled at 2 frames per press.
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
