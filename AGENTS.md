# AGENTS.md - Mirage Island Wish Charm Expansion

This document summarizes the architecture, mechanics, technical decisions, and full implementation of the **Wish Charm** system for **Mirage Island** within `pokeemerald-expansion`. It serves as a comprehensive reference guide for any developer or AI agent maintaining or customizing this codebase.

---

## 1. Context & Core Objectives

In vanilla Pokémon Emerald, **Mirage Island** is an extremely elusive location on Route 130 (`MAP_ROUTE130`). Its appearance is controlled by a daily 16-bit pseudo-random value (`GetMirageRnd() >> 16`). Every day:
- The game determines whether any Pokémon in the player's current party has a personality ID whose lower 16 bits match the daily Mirage Island random seed (`IsMirageIslandPresent()`).
- If a match is found:
  - Route 130 loads the `LAYOUT_ROUTE130_MIRAGE_ISLAND` layout, revealing the island.
  - The Liechi Berry tree (`FLAG_TEMP_HIDE_MIRAGE_ISLAND_BERRY_TREE`) is made visible.
  - Wild Wynaut encounters become accessible in the grass.
  - The old man in Pacifidlog Town House 5 announces: *"Oh! Oh my! I can see MIRAGE ISLAND today!"*.
- Because the odds are $\approx 1/65536$ per party Pokémon per day, Mirage Island is practically unreachable during normal playthroughs.

This expansion introduces the **Wish Charm**, a Key Item that forces Mirage Island to appear, providing an accessible and lore-friendly way to encounter Mirage Island while honoring its original mechanics.

---

## 2. Requirements & Implementations

### 2.1. The Wish Charm Key Item
- **Item Definition (`include/constants/items.h`, `src/data/items.h`):**
  - Identifier: `ITEM_WISH_CHARM` (874)
  - Pocket: `POCKET_KEY_ITEMS`
  - Importance: `1` (Key Item, cannot be tossed or sold)
  - Type: `ITEM_USE_BAG_MENU`
  - Field Use: `ItemUseOutOfBattle_CannotUse` (passive charm item, similar to Shiny Charm, Oval Charm, and Exp. Charm)
  - Visuals: Uses the Shiny Charm icon and palette (`gItemIcon_ShinyCharm`, `gItemIconPalette_ShinyCharm`).
  - Description:
    ```c
    "A charm that glows\n"
    "faintly. It seems\n"
    "to hold a wish."
    ```
    Intentionally vague (like the Enigma Stone): it does not reveal its purpose so the player discovers it, as it will be tied to Jirachi.

### 2.2. Mirage Island Forcing Logic
- **Central Authority (`IsMirageIslandPresent()` in `src/time_events.c`):**
  - Updated to check `IsWishCharmActive()` before evaluating party personality IDs:
    ```c
    bool8 IsMirageIslandPresent(void)
    {
        if (IsWishCharmActive())
            return TRUE;
        ...
    }
    ```
- **Pacifidlog Town Old Man:**
  - `PacifidlogTown_House5_EventScript_MirageIslandWatcher` queries `specialvar VAR_RESULT, IsMirageIslandPresent`.
  - When the Wish Charm is active, the watcher automatically sees Mirage Island and delivers his iconic announcement: *"Oh! Oh my!\nI can see MIRAGE ISLAND today!"*.
- **Route 130 Layout & Objects:**
  - `Route130_OnTransition` evaluates `IsMirageIslandPresent`.
  - Sets `LAYOUT_ROUTE130_MIRAGE_ISLAND` and leaves `FLAG_TEMP_HIDE_MIRAGE_ISLAND_BERRY_TREE` clear, revealing the island terrain and Liechi Berry tree.
  - Wynaut ambient cries play correctly while on the island.

### 2.3. Single-Use & Daily Expiration Mechanics
- **Single-Day Availability (Vanilla Parity):**
  - When Mirage Island appears normally, the player can visit it, leave Route 130 (e.g. to heal or buy Poké Balls in Pacifidlog Town), and return to Mirage Island as many times as desired during that same day.
  - The Wish Charm honors this mechanic: once the player arrives at Mirage Island for the first time, the charm remains active for the remainder of that day.
  - After that day has passed, the Wish Charm expires and will no longer force Mirage Island to appear.
- **First Arrival Detection (`UpdateMirageIslandWishCharmStep()` in `src/time_events.c`):**
  - Hooked into overworld player movement in `src/field_control_avatar.c` (`input->tookStep`).
  - Checks if the player is on `MAP_ROUTE130`, layout is `LAYOUT_ROUTE130_MIRAGE_ISLAND`, and the player is on foot (`!TestPlayerAvatarFlags(PLAYER_AVATAR_FLAG_SURFING)`).
  - Since Route 130 contains no land other than Mirage Island, stepping foot on land confirms arrival on the island.
  - Sets `FLAG_WISH_CHARM_VISITED` and records the current day into `VAR_WISH_CHARM_VISIT_DAY` (`VarGet(VAR_DAYS) + 1`).
- **Expiration Trigger (`UpdateMirageIslandWishCharmDaily()` in `src/clock.c`):**
  - Integrated into `DoDailyEvents(daysSince)` when a midnight/day transition occurs.
  - If `FLAG_WISH_CHARM_VISITED` is set, `FLAG_WISH_CHARM_EXPIRED` is set.
  - Additionally, `IsWishCharmActive()` checks if `VAR_WISH_CHARM_VISIT_DAY != 0` and `VAR_WISH_CHARM_VISIT_DAY != VarGet(VAR_DAYS) + 1`, providing instant expiration even if time was modified without running `DoDailyEvents`.

### 2.4. Development & Debug Configuration
- **Debug Flag (`OW_FLAG_WISH_CHARM_INFINITE` in `include/config/overworld.h`):**
  - Follows the same pattern as `OW_FLAG_NO_COLLISION` etc.: the config define holds the flag ID (`FLAG_UNUSED_0x022`); set it to `0` to disable the feature (the debug menu then shows the standard "flag not set in config" message).
  - Set on new games in `NewGameInitData` (`src/new_game.c`) when configured, so it is enabled by default for development.
  - When enabled, the Wish Charm never expires, allowing developers to enter and leave Mirage Island repeatedly across multiple days without needing to reset flags or re-acquire the item.
- **Debug Menu Integration (`src/debug.c`):**
  - **Key Items Pocket Fill:** In `DebugAction_PCBag_Fill_PocketKeyItems`, `ITEM_WISH_CHARM` is added first (matching the pattern in `altering_cave`) so players always receive it even if pocket item limit is reached.
  - **Flag Toggle:** Added `Toggle {STR_VAR_1}Wish Charm Inf` under `Debug Menu -> Flags & Vars…`.
    - Pressing A toggles the debug flag on/off with audio feedback (`SE_PC_LOGIN` / `SE_PC_OFF`).
    - Dynamic color status: green when infinite mode is active, red when inactive.

---

## 3. Constants & State Storage

| Constant | Value | Description |
|---|---|---|
| `ITEM_WISH_CHARM` | `874` | Key Item constant |
| `FLAG_WISH_CHARM_VISITED` | `0x20` | Set when player first lands on Mirage Island with Wish Charm |
| `FLAG_WISH_CHARM_EXPIRED` | `0x21` | Set when the day of the first visit has ended |
| `OW_FLAG_WISH_CHARM_INFINITE` | `FLAG_UNUSED_0x022` | Debug flag (config in `include/config/overworld.h`): infinite reusable visits |
| `VAR_WISH_CHARM_VISIT_DAY` | `0x40DB` | Stores `VAR_DAYS + 1` corresponding to the day of the first visit |

---

## 4. Key Source Files Modified

| File | Changes Made |
|---|---|
| `include/constants/items.h` | Registered `ITEM_WISH_CHARM = 874`. |
| `include/constants/vars.h` | Assigned `VAR_WISH_CHARM_VISIT_DAY` (`0x40DB`). |
| `include/time_events.h` | Declared `IsWishCharmActive`, `UpdateMirageIslandWishCharmStep`, and `UpdateMirageIslandWishCharmDaily`. |
| `src/data/items.h` | Defined `[ITEM_WISH_CHARM]` properties, pocket, description, and Shiny Charm icon/palette. |
| `src/time_events.c` | Implemented `IsWishCharmActive`, `UpdateMirageIslandWishCharmStep`, `UpdateMirageIslandWishCharmDaily`, and updated `IsMirageIslandPresent`. |
| `src/field_control_avatar.c` | Called `UpdateMirageIslandWishCharmStep()` in `input->tookStep` movement handler. |
| `src/clock.c` | Hooked `UpdateMirageIslandWishCharmDaily()` into `DoDailyEvents()`. |
| `src/debug.c` | Prioritized `ITEM_WISH_CHARM` in `DebugAction_PCBag_Fill_PocketKeyItems`, added `DEBUG_FLAGVAR_MENU_ITEM_TOGGLE_WISH_CHARM` option and toggle function in `sDebugMenu_Actions_Flags`. |
| `AGENTS.md` | Created this reference document for agents and developers. |

---

## 5. Verification & Testing Guide

1. **Obtaining the Item:**
   - Open the Start Menu -> `Debug Menu` -> `PC/Bag…` -> `Fill…` -> `Fill Pocket Key Items`.
   - Open Bag -> Key Items Pocket: confirm `Wish Charm` is present with the Shiny Charm icon and proper 3-line description.
2. **Pacifidlog Town Dialogue:**
   - Warp to Pacifidlog Town.
   - Enter House 5 (the rightmost house).
   - Talk to the old man looking through the window: confirm he says *"Oh! Oh my! I can see MIRAGE ISLAND today!"*.
3. **Route 130 Exploration:**
   - Surf east from Pacifidlog Town to Route 130.
   - Confirm Mirage Island is visible with its grass, sandy shore, and Liechi Berry tree.
   - Walk onto the island, pick the berry, and encounter wild Wynauts in the grass.
4. **Debug Infinite Mode:**
   - Check `Debug Menu` -> `Flags & Vars…` -> `Toggle {COLOR GREEN}Wish Charm Inf`.
   - Confirm Mirage Island remains accessible across days and multiple visits without expiring.
5. **Normal Expiration Flow (Single-Use):**
   - In `Debug Menu` -> `Flags & Vars…`, toggle `Wish Charm Inf` OFF (turns red).
   - Land on Mirage Island (sets visit flag and day).
   - Leave Route 130 to Route 129 or Pacifidlog Town: on the same day, confirm Mirage Island is still visible.
   - Advance day (via `Debug Menu` -> `Utilities…` -> `Time Functions…` -> `Redo daily events`).
   - Check with the old man: confirm he now says *"I can't see MIRAGE ISLAND today…"*.
   - Re-enter Route 130: confirm Mirage Island has vanished and the area is empty ocean.

---

## 6. Mr. Reef Event (Pacifidlog Town House 5)

The Wish Charm no longer reveals Mirage Island on its own: the player must first talk to the old man (**Mr. Reef**, whose name is not revealed to the player yet) in `PacifidlogTown_House5` while carrying the charm. Naturally appearing Mirage Island (party personality match) is unaffected.

- **Gate:** `IsWishCharmActive()` (`src/time_events.c`) returns `FALSE` until `FLAG_MIRAGE_ISLAND_REEF_EVENT_DONE` is set (checked before the debug infinite flag).
- **Tinko (Corsola, `OBJ_EVENT_GFX_SPECIES(CORSOLA)`):** stands at (9,5) next to Mr. Reef while the player holds the Wish Charm and the event is pending (`FLAG_TEMP_5`, set/cleared in `PacifidlogTown_House5_OnTransition`). Interacting plays Corsola's cry.
- **Scene (`PacifidlogTown_House5_EventScript_WishCharmEvent`):** Reef announces Mirage Island, says he sent for an old friend; Mr. Briney (`OBJ_EVENT_GFX_EXPERT_M`) and Peeko (now `OBJ_EVENT_GFX_SPECIES(PELIPPER)`, Pelipper cry) enter through the door (`FLAG_TEMP_6`/`FLAG_TEMP_7`). Reef says his catchphrase **"Avast!"** for the first time here (Briney's is "Ahoy!"). Briney gives his number (registered in Match Call), then Briney, Peeko, Tinko and Reef walk out and are removed. Reef stays hidden afterwards (`FLAG_MIRAGE_ISLAND_REEF_EVENT_DONE` is his object flag) — the original "can/can't see Mirage Island" watcher is therefore gone for now; to be revisited.
- **Other NPC (Gentleman):** after the event, says Reef and Briney were captains and great friends.
- **Match Call:** `MC_HEADER_BRINEY` (`include/pokenav.h`, `src/pokenav_match_call_data.c`) sits between Scott and Roxanne because the list is built in header order. Enabled by `FLAG_ENABLE_BRINEY_MATCH_CALL`. Text `MatchCall_Text_Briney1` (`data/text/match_call.inc`): "What are you waiting for?..." with Peeko's classic `"PEEKO: Pihyo pihyohyo…"` line.

| Constant | Value | Description |
|---|---|---|
| `FLAG_MIRAGE_ISLAND_REEF_EVENT_DONE` | `0x24` | Scene finished; hides Reef; unlocks Wish Charm |
| `FLAG_ENABLE_BRINEY_MATCH_CALL` | `0x25` | Mr. Briney registered in Match Call |
