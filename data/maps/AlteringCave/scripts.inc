.set LOCAL_VAR_LURE_ITEM, VAR_0x8004

AlteringCave_MapScripts::
	map_script MAP_SCRIPT_ON_TRANSITION, AlteringCave_OnTransition
	.byte 0

AlteringCave_OnTransition:
	setflag FLAG_LANDMARK_ALTERING_CAVE
	end

AlteringCave_EventScript_ExitTrigger::
	lockall
	bufferitemname STR_VAR_1, VAR_ALTERING_CAVE_LURE_ITEM
	msgbox AlteringCave_Text_LureStillActiveExitEarly, MSGBOX_YESNO
	goto_if_eq VAR_RESULT, YES, AlteringCave_EventScript_ExitEarlyYes
	closemessage
	applymovement LOCALID_PLAYER, AlteringCave_Movement_StepBackUp
	waitmovement 0
	releaseall
	end

AlteringCave_EventScript_ExitEarlyYes::
	msgbox AlteringCave_Text_LureWoreOff, MSGBOX_DEFAULT
	closemessage
	clearflag FLAG_ALTERING_CAVE_LURE_ACTIVE
	setvar VAR_ALTERING_CAVE_LURE_STEPS, 0
	setvar VAR_ALTERING_CAVE_WILD_SET, 0
	setvar VAR_ALTERING_CAVE_LURE_ITEM, 0
	warp MAP_ROUTE103, 45, 6
	waitstate
	releaseall
	end

AlteringCave_Movement_StepBackUp:
	walk_up
	step_end

EventScript_AlteringCaveLureWoreOff::
	lockall
	copyvar LOCAL_VAR_LURE_ITEM, VAR_ALTERING_CAVE_LURE_ITEM
	bufferitemname STR_VAR_1, LOCAL_VAR_LURE_ITEM
	checkitem LOCAL_VAR_LURE_ITEM, 1
	goto_if_eq VAR_RESULT, TRUE, EventScript_AlteringCaveLureWoreOff_AskUseAnother
	msgbox AlteringCave_Text_LureWoreOff, MSGBOX_SIGN
	setvar VAR_ALTERING_CAVE_LURE_ITEM, 0
	releaseall
	end

EventScript_AlteringCaveLureWoreOff_AskUseAnother::
	msgbox AlteringCave_Text_LureWoreOffAskAnother, MSGBOX_YESNO
	goto_if_eq VAR_RESULT, YES, EventScript_AlteringCaveLureWoreOff_UseAnother
	setvar VAR_ALTERING_CAVE_LURE_ITEM, 0
	closemessage
	releaseall
	end

EventScript_AlteringCaveLureWoreOff_UseAnother::
	playse SE_REPEL
	waitse
	removeitem LOCAL_VAR_LURE_ITEM, 1
	setvar VAR_ALTERING_CAVE_LURE_STEPS, 250
	setflag FLAG_ALTERING_CAVE_LURE_ACTIVE
	call AlteringCave_EventScript_SetWildSetFromItem
	bufferitemname STR_VAR_2, LOCAL_VAR_LURE_ITEM
	msgbox Text_SprayWoreOffUseX, MSGBOX_SIGN
	releaseall
	end

AlteringCave_EventScript_SetWildSetFromItem::
	switch LOCAL_VAR_LURE_ITEM
	case ITEM_NORMAL_LURE, AlteringCave_EventScript_SetTableNormal
	case ITEM_WATER_LURE, AlteringCave_EventScript_SetTableWater
	case ITEM_BUG_LURE, AlteringCave_EventScript_SetTableBug
	case ITEM_ROCK_LURE, AlteringCave_EventScript_SetTableRock
	case ITEM_SPECIAL_LURE, AlteringCave_EventScript_SetTableSpecial
	case ITEM_RARE_LURE, AlteringCave_EventScript_SetTableRare
	return

AlteringCave_EventScript_SetTableNormal:
	setvar VAR_ALTERING_CAVE_WILD_SET, 1
	return

AlteringCave_EventScript_SetTableWater:
	setvar VAR_ALTERING_CAVE_WILD_SET, 2
	return

AlteringCave_EventScript_SetTableBug:
	setvar VAR_ALTERING_CAVE_WILD_SET, 3
	return

AlteringCave_EventScript_SetTableRock:
	setvar VAR_ALTERING_CAVE_WILD_SET, 4
	return

AlteringCave_EventScript_SetTableSpecial:
	setvar VAR_ALTERING_CAVE_WILD_SET, 5
	return

AlteringCave_EventScript_SetTableRare:
	setvar VAR_ALTERING_CAVE_WILD_SET, 6
	return

AlteringCave_Text_LureWoreOff:
	.string "{STR_VAR_1}'s effect wore off…$"

AlteringCave_Text_LureWoreOffAskAnother:
	.string "{STR_VAR_1}'s effect wore off!\n"
	.string "Use another?$"

AlteringCave_Text_LureStillActiveExitEarly:
	.string "The {STR_VAR_1} is still active.\n"
	.string "If you leave, its effect will fade.\p"
	.string "Are you sure you want to exit?$"
