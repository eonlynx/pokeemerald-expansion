PacifidlogTown_House5_MapScripts::
	map_script MAP_SCRIPT_ON_TRANSITION, PacifidlogTown_House5_OnTransition
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
PacifidlogTown_House5_OnTransition_End:
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
	applymovement LOCALID_PACIFIDLOG_HOUSE5_REEF, PacifidlogTown_House5_Movement_ReefFaceLeft
	applymovement LOCALID_PACIFIDLOG_HOUSE5_TINKO, PacifidlogTown_House5_Movement_ReefFaceLeft
	waitmovement LOCALID_PACIFIDLOG_HOUSE5_REEF
	waitmovement LOCALID_PACIFIDLOG_HOUSE5_TINKO
	msgbox PacifidlogTown_House5_Text_ReefAvastBriney, MSGBOX_DEFAULT
	msgbox PacifidlogTown_House5_Text_BrineyAnsweredYourCall, MSGBOX_DEFAULT
	playmoncry SPECIES_PELIPPER, CRY_MODE_NORMAL
	msgbox PacifidlogTown_House5_Text_PeekoCry, MSGBOX_DEFAULT
	waitmoncry
	msgbox PacifidlogTown_House5_Text_BrineySeeYouThere, MSGBOX_DEFAULT
	closemessage
	delay 30
	playfanfare MUS_REGISTER_MATCH_CALL
	msgbox PacifidlogTown_House5_Text_RegisteredBriney, MSGBOX_DEFAULT
	waitfanfare
	closemessage
	setflag FLAG_ENABLE_BRINEY_MATCH_CALL
	delay 30
	msgbox PacifidlogTown_House5_Text_ReefAvastLetsGo, MSGBOX_DEFAULT
	closemessage
	playse SE_EXIT
	applymovement LOCALID_PACIFIDLOG_HOUSE5_BRINEY, PacifidlogTown_House5_Movement_BrineyExit
	applymovement LOCALID_PACIFIDLOG_HOUSE5_PEEKO, PacifidlogTown_House5_Movement_PeekoExit
	applymovement LOCALID_PACIFIDLOG_HOUSE5_TINKO, PacifidlogTown_House5_Movement_TinkoExit
	applymovement LOCALID_PACIFIDLOG_HOUSE5_REEF, PacifidlogTown_House5_Movement_ReefExit
	waitmovement LOCALID_PACIFIDLOG_HOUSE5_BRINEY
	removeobject LOCALID_PACIFIDLOG_HOUSE5_BRINEY
	waitmovement LOCALID_PACIFIDLOG_HOUSE5_PEEKO
	removeobject LOCALID_PACIFIDLOG_HOUSE5_PEEKO
	waitmovement LOCALID_PACIFIDLOG_HOUSE5_TINKO
	removeobject LOCALID_PACIFIDLOG_HOUSE5_TINKO
	waitmovement LOCALID_PACIFIDLOG_HOUSE5_REEF
	removeobject LOCALID_PACIFIDLOG_HOUSE5_REEF
	setflag FLAG_TEMP_5
	setflag FLAG_TEMP_6
	setflag FLAG_TEMP_7
	setflag FLAG_MIRAGE_ISLAND_REEF_EVENT_DONE
	releaseall
	end

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

@ Briney spawns at (5, 8), Peeko at (4, 8). Both walk up from the door.
PacifidlogTown_House5_Movement_BrineyEnter:
	walk_up
	walk_up
	walk_right
	walk_right
	walk_up
	face_right
	step_end

PacifidlogTown_House5_Movement_PeekoEnter:
	delay_16
	walk_up
	walk_up
	walk_right
	walk_right
	walk_right
	walk_right
	walk_up
	face_left
	step_end

PacifidlogTown_House5_Movement_ReefFaceLeft:
	face_left
	step_end

@ Exit routes use row 7 as a corridor to the door. Delays keep everyone in single file.
PacifidlogTown_House5_Movement_BrineyExit:
	walk_down
	walk_down
	walk_left
	walk_left
	walk_down
	step_end

PacifidlogTown_House5_Movement_PeekoExit:
	delay_16
	delay_16
	walk_down
	walk_down
	walk_left
	walk_left
	walk_left
	walk_left
	walk_down
	step_end

PacifidlogTown_House5_Movement_TinkoExit:
	delay_16
	delay_16
	delay_16
	delay_16
	walk_down
	walk_down
	walk_left
	walk_left
	walk_left
	walk_left
	walk_down
	step_end

PacifidlogTown_House5_Movement_ReefExit:
	delay_16
	delay_16
	delay_16
	delay_16
	delay_16
	delay_16
	walk_down
	walk_down
	walk_down
	walk_left
	walk_left
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
	.string "Even TINKO here has been restless\n"
	.string "since the first light of dawn.\p"
	.string "I sent for an old friend the very\n"
	.string "moment I spotted it.\p"
	.string "He should be here any minute now…$"

PacifidlogTown_House5_Text_ReefAvastBriney:
	.string "Avast!\n"
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
	.string "Avast! Don't dawdle, youngster.\n"
	.string "The sea waits for no one!$"

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
