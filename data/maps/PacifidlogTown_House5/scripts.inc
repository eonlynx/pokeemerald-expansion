PacifidlogTown_House5_MapScripts::
	map_script MAP_SCRIPT_ON_TRANSITION, PacifidlogTown_House5_OnTransition
	map_script MAP_SCRIPT_ON_RESUME, PacifidlogTown_House5_OnResume
	.byte 0

@ Briney and Peeko only appear during the Wish Charm scene.
@ Tinko (Corsola) only stands next to Mr. Reef while the Wish Charm event is pending.
PacifidlogTown_House5_OnTransition:
	setflag FLAG_TEMP_5
	setflag FLAG_TEMP_6
	setflag FLAG_TEMP_7
	goto_if_set FLAG_MIRAGE_ISLAND_REEF_EVENT_DONE, PacifidlogTown_House5_OnTransition_End
	checkitem ITEM_WISH_CHARM
	goto_if_eq VAR_RESULT, FALSE, PacifidlogTown_House5_OnTransition_End
	clearflag FLAG_TEMP_5
	setobjectmovementtype LOCALID_PACIFIDLOG_HOUSE5_TINKO, MOVEMENT_TYPE_FACE_RIGHT
PacifidlogTown_House5_OnTransition_End:
	end

PacifidlogTown_House5_OnResume:
	goto_if_set FLAG_TEMP_5, PacifidlogTown_House5_OnResume_End
	turnobject LOCALID_PACIFIDLOG_HOUSE5_TINKO, DIR_EAST
PacifidlogTown_House5_OnResume_End:
	end

@ Mr. Reef
PacifidlogTown_House5_EventScript_MirageIslandWatcher::
	lock
	faceplayer
	checkitem ITEM_WISH_CHARM
	goto_if_eq VAR_RESULT, TRUE, PacifidlogTown_House5_EventScript_WishCharmEvent
	specialvar VAR_RESULT, IsMirageIslandPresent
	goto_if_eq VAR_RESULT, TRUE, PacifidlogTown_House5_EventScript_MirageIslandPresent
	msgbox PacifidlogTown_House5_Text_CantSeeMirageIslandToday, MSGBOX_DEFAULT
	release
	end

PacifidlogTown_House5_EventScript_MirageIslandPresent::
	msgbox PacifidlogTown_House5_Text_CanSeeMirageIslandToday, MSGBOX_DEFAULT
	release
	end

PacifidlogTown_House5_EventScript_WishCharmEvent::
	specialvar VAR_0x8004, GetPlayerFacingDirection
	msgbox PacifidlogTown_House5_Text_ReefSeesMirageIsland, MSGBOX_DEFAULT
	closemessage
	delay 30
	playse SE_DOOR
	clearflag FLAG_TEMP_6
	clearflag FLAG_TEMP_7
	addobject LOCALID_PACIFIDLOG_HOUSE5_BRINEY
	addobject LOCALID_PACIFIDLOG_HOUSE5_PEEKO
	applymovement LOCALID_PACIFIDLOG_HOUSE5_BRINEY, PacifidlogTown_House5_Movement_BrineyEnter
	applymovement LOCALID_PACIFIDLOG_HOUSE5_PEEKO, PacifidlogTown_House5_Movement_PeekoEnter
	waitmovement LOCALID_PACIFIDLOG_HOUSE5_BRINEY
	waitmovement LOCALID_PACIFIDLOG_HOUSE5_PEEKO
	applymovement LOCALID_PACIFIDLOG_HOUSE5_REEF, PacifidlogTown_House5_Movement_ReefApproachBriney
	applymovement LOCALID_PACIFIDLOG_HOUSE5_TINKO, PacifidlogTown_House5_Movement_TinkoFollowReef
	waitmovement LOCALID_PACIFIDLOG_HOUSE5_REEF
	waitmovement LOCALID_PACIFIDLOG_HOUSE5_TINKO
	call_if_eq VAR_0x8004, DIR_EAST, PacifidlogTown_House5_EventScript_TurnPlayerSouth
	msgbox PacifidlogTown_House5_Text_ReefAvastBriney, MSGBOX_DEFAULT
	msgbox PacifidlogTown_House5_Text_BrineyAnsweredYourCall, MSGBOX_DEFAULT
	playmoncry SPECIES_PELIPPER, CRY_MODE_NORMAL
	msgbox PacifidlogTown_House5_Text_PeekoCry, MSGBOX_DEFAULT
	waitmoncry
	closemessage
	call_if_eq VAR_0x8004, DIR_SOUTH, PacifidlogTown_House5_EventScript_PlayerApproachFromAboveReef
	call_if_eq VAR_0x8004, DIR_EAST, PacifidlogTown_House5_EventScript_PlayerApproachFromLeftOfReef
	turnobject LOCALID_PACIFIDLOG_HOUSE5_BRINEY, DIR_NORTH
	msgbox PacifidlogTown_House5_Text_BrineySeeYouThere, MSGBOX_DEFAULT
	closemessage
	delay 30
	playfanfare MUS_REGISTER_MATCH_CALL
	msgbox PacifidlogTown_House5_Text_RegisteredBriney, MSGBOX_DEFAULT
	waitfanfare
	closemessage
	setflag FLAG_ENABLE_BRINEY_MATCH_CALL
	delay 30
	turnobject LOCALID_PACIFIDLOG_HOUSE5_BRINEY, DIR_EAST
	turnobject OBJ_EVENT_ID_PLAYER, DIR_EAST
	msgbox PacifidlogTown_House5_Text_ReefAvastLetsGo, MSGBOX_DEFAULT
	closemessage
	turnobject OBJ_EVENT_ID_PLAYER, DIR_SOUTH
	applymovement LOCALID_PACIFIDLOG_HOUSE5_BRINEY, PacifidlogTown_House5_Movement_BrineyExit
	applymovement LOCALID_PACIFIDLOG_HOUSE5_PEEKO, PacifidlogTown_House5_Movement_PeekoExit
	applymovement LOCALID_PACIFIDLOG_HOUSE5_REEF, PacifidlogTown_House5_Movement_ReefExit
	applymovement LOCALID_PACIFIDLOG_HOUSE5_TINKO, PacifidlogTown_House5_Movement_TinkoExit
	waitmovement LOCALID_PACIFIDLOG_HOUSE5_BRINEY
	playse SE_EXIT
	removeobject LOCALID_PACIFIDLOG_HOUSE5_BRINEY
	waitmovement LOCALID_PACIFIDLOG_HOUSE5_PEEKO
	removeobject LOCALID_PACIFIDLOG_HOUSE5_PEEKO
	waitmovement LOCALID_PACIFIDLOG_HOUSE5_REEF
	playse SE_EXIT
	removeobject LOCALID_PACIFIDLOG_HOUSE5_REEF
	waitmovement LOCALID_PACIFIDLOG_HOUSE5_TINKO
	removeobject LOCALID_PACIFIDLOG_HOUSE5_TINKO
	setflag FLAG_TEMP_5
	setflag FLAG_TEMP_6
	setflag FLAG_TEMP_7
	setflag FLAG_MIRAGE_ISLAND_REEF_EVENT_DONE
	releaseall
	end

PacifidlogTown_House5_EventScript_TurnPlayerSouth::
	turnobject OBJ_EVENT_ID_PLAYER, DIR_SOUTH
	return

PacifidlogTown_House5_EventScript_PlayerApproachFromAboveReef::
	applymovement OBJ_EVENT_ID_PLAYER, PacifidlogTown_House5_Movement_PlayerToBrineyFromAboveReef
	waitmovement OBJ_EVENT_ID_PLAYER
	return

PacifidlogTown_House5_EventScript_PlayerApproachFromLeftOfReef::
	applymovement OBJ_EVENT_ID_PLAYER, PacifidlogTown_House5_Movement_PlayerToBrineyFromLeftOfReef
	waitmovement OBJ_EVENT_ID_PLAYER
	return

@ Tinko (Corsola)
PacifidlogTown_House5_EventScript_Tinko::
	lock
	faceplayer
	playmoncry SPECIES_CORSOLA, CRY_MODE_NORMAL
	msgbox PacifidlogTown_House5_Text_Tinko, MSGBOX_DEFAULT
	waitmoncry
	release
	end

PacifidlogTown_House5_EventScript_Gentleman::
	lock
	faceplayer
	goto_if_set FLAG_MIRAGE_ISLAND_REEF_EVENT_DONE, PacifidlogTown_House5_EventScript_GentlemanCaptains
	msgbox PacifidlogTown_House5_Text_MirageIslandAppearDependingOnWeather, MSGBOX_DEFAULT
	release
	end

PacifidlogTown_House5_EventScript_GentlemanCaptains::
	msgbox PacifidlogTown_House5_Text_GentlemanCaptains, MSGBOX_DEFAULT
	release
	end

@ Briney spawns at (5, 8) -> walks up to (5, 7) and right to (6, 7) facing right.
@ Peeko spawns at (4, 8) -> walks right to (5, 8) and up to (5, 7) right behind Briney, facing right.
PacifidlogTown_House5_Movement_BrineyEnter:
	walk_up
	walk_right
	step_end

PacifidlogTown_House5_Movement_PeekoEnter:
	walk_right
	walk_up
	face_right
	step_end

@ Reef starts at (9, 4) -> walks down to (9, 7) and left to (7, 7) facing Briney at (6, 7).
@ Tinko starts at (9, 5) -> swaps up to (9, 4) on step 1, then follows Reef closely to (8, 7) facing left.
PacifidlogTown_House5_Movement_ReefApproachBriney:
	walk_down
	walk_down
	walk_down
	walk_left
	walk_left
	step_end

PacifidlogTown_House5_Movement_TinkoFollowReef:
	walk_up
	walk_down
	walk_down
	walk_down
	walk_left
	step_end

@ From above Reef (9, 3) -> walks down to row 6 and left to (6, 6) right above Briney, facing down.
PacifidlogTown_House5_Movement_PlayerToBrineyFromAboveReef:
	walk_down
	walk_down
	walk_down
	walk_left
	walk_left
	walk_left
	face_down
	step_end

@ From left of Reef (8, 4) -> walks down to row 6 and left to (6, 6) right above Briney, facing down.
PacifidlogTown_House5_Movement_PlayerToBrineyFromLeftOfReef:
	walk_down
	walk_down
	walk_left
	walk_left
	face_down
	step_end

@ Single-file exit down to the door at (5, 8):
@ Step 1: Briney (6,7)->(5,7) while Peeko swaps (5,7)->(6,7); Reef and Tinko wait 1 step (delay_16).
@ Step 2+: Everyone walks out in order: Briney -> Peeko -> Reef -> Tinko.
PacifidlogTown_House5_Movement_BrineyExit:
	walk_left
	walk_down
	step_end

PacifidlogTown_House5_Movement_PeekoExit:
	walk_right
	walk_left
	walk_down
	step_end

PacifidlogTown_House5_Movement_ReefExit:
	delay_16
	walk_left
	walk_left
	walk_down
	step_end

PacifidlogTown_House5_Movement_TinkoExit:
	delay_16
	walk_left
	walk_left
	walk_left
	walk_down
	step_end

PacifidlogTown_House5_Text_CantSeeMirageIslandToday:
	.string "I can't see MIRAGE ISLAND today…$"

PacifidlogTown_House5_Text_CanSeeMirageIslandToday:
	.string "Oh! Oh my!\n"
	.string "I can see MIRAGE ISLAND today!$"

PacifidlogTown_House5_Text_ReefSeesMirageIsland:
	.string "Oh! Oh my!\n"
	.string "I can see MIRAGE ISLAND today!\p"
	.string "Clear as the day I first laid eyes\n"
	.string "on it, all those years ago…\p"
	.string "And it seems you're the one who\n"
	.string "brought it into view, youngster.\p"
	.string "Allow me to introduce myself.\n"
	.string "The name's MR. REEF!\p"
	.string "MR. REEF: Even TINKO here has been\n"
	.string "restless since the first light of dawn.\p"
	.string "I sent for an old friend the very\n"
	.string "moment I spotted it.\p"
	.string "He should be here any minute now…$"

PacifidlogTown_House5_Text_ReefAvastBriney:
	.string "MR. REEF: Avast!\n"
	.string "Right on time, old friend!$"

PacifidlogTown_House5_Text_BrineyAnsweredYourCall:
	.string "MR. BRINEY: Ahoy, my friend!\n"
	.string "I came as soon as I got your call!\p"
	.string "Now, let's go see that MIRAGE\n"
	.string "ISLAND with our own eyes!$"

PacifidlogTown_House5_Text_PeekoCry:
	.string "PEEKO: Pii piihyoro!$"

PacifidlogTown_House5_Text_BrineySeeYouThere:
	.string "MR. BRINEY: Ahoy, {PLAYER}{KUN}!\n"
	.string "It's been too long! It does my\l"
	.string "heart good to see you again!\p"
	.string "Look how much my darling PEEKO's\n"
	.string "grown since we last set sail!\p"
	.string "So you're the one who brought\n"
	.string "MIRAGE ISLAND into view! We'll be\l"
	.string "waiting for you there!\p"
	.string "Here, let's register each other\n"
	.string "in our POKéNAVS, in case you\l"
	.string "need anything at all!$"

PacifidlogTown_House5_Text_RegisteredBriney:
	.string "Registered MR. BRINEY\n"
	.string "in the POKéNAV.$"

PacifidlogTown_House5_Text_ReefAvastLetsGo:
	.string "MR. REEF: Avast! Don't dawdle,\n"
	.string "youngster. The sea waits for no one!$"

PacifidlogTown_House5_Text_Tinko:
	.string "TINKO: Koro kororoo!$"

PacifidlogTown_House5_Text_MirageIslandAppearDependingOnWeather:
	.string "MIRAGE ISLAND…\p"
	.string "It must become visible and invisible\n"
	.string "depending on the weather conditions\l"
	.string "that make mirages appear.\p"
	.string "Or is it really appearing and\n"
	.string "disappearing?$"

PacifidlogTown_House5_Text_GentlemanCaptains:
	.string "REEF and BRINEY were captains,\n"
	.string "and the best of friends.\p"
	.string "Every captain keeps one ritual:\n"
	.string "before a voyage, they read the\l"
	.string "tides aloud, and after it, they\l"
	.string "raise a toast to all who return.\p"
	.string "It warms my heart to see the two\n"
	.string "of them together again.$"
