.set LOCALID_OWNER, 1
.set LOCALID_WALLY, 2
.set LOCALID_SPEC_1, 3
.set LOCALID_SPEC_2, 4
.set LOCALID_SPEC_3, 5
.set LOCALID_SPEC_4, 6
.set LOCALID_SPEC_5, 7
.set LOCALID_SPEC_6, 8
.set LOCALID_SPEC_7, 9
.set LOCALID_SPEC_8, 10

TrainerHill_Roof_MapScripts::
	map_script MAP_SCRIPT_ON_RESUME, TrainerHill_Roof_OnResume
	map_script MAP_SCRIPT_ON_TRANSITION, TrainerHill_Roof_OnTransition
	map_script MAP_SCRIPT_ON_FRAME_TABLE, TrainerHill_OnFrame
	.byte 0

TrainerHill_Roof_OnResume:
	trainerhill_resumetimer
	end

TrainerHill_Roof_OnTransition:
	trainerhill_setspectatorgfx
	trainerhill_getspoketoowner
	copyvar VAR_TEMP_4, VAR_RESULT
	end

TrainerHill_Roof_EventScript_TriggerTile8::
	lockall
	setvar VAR_TEMP_4, 1
	applymovement LOCALID_PLAYER, Common_Movement_WalkInPlaceFasterUp
	waitmovement 0
	goto TrainerHill_Roof_EventScript_OwnerProcess

TrainerHill_Roof_EventScript_TriggerTile9::
	lockall
	setvar VAR_TEMP_4, 1
	applymovement LOCALID_PLAYER, TrainerHill_Roof_Movement_PlayerApproachOwner1
	waitmovement 0
	goto TrainerHill_Roof_EventScript_OwnerProcess

TrainerHill_Roof_EventScript_TriggerTile10::
	lockall
	setvar VAR_TEMP_4, 1
	applymovement LOCALID_PLAYER, TrainerHill_Roof_Movement_PlayerApproachOwner2
	waitmovement 0
	goto TrainerHill_Roof_EventScript_OwnerProcess

TrainerHill_Roof_Movement_PlayerApproachOwner1:
	walk_up
	step_end

TrainerHill_Roof_Movement_PlayerApproachOwner2:
	walk_up
	walk_up
	step_end

TrainerHill_Roof_EventScript_Owner::
	setvar VAR_TEMP_4, 1
	lock
	faceplayer
	goto TrainerHill_Roof_EventScript_OwnerProcessNoFace

TrainerHill_Roof_EventScript_OwnerProcess::
	applymovement LOCALID_OWNER, Common_Movement_WalkInPlaceFasterDown
	waitmovement 0
TrainerHill_Roof_EventScript_OwnerProcessNoFace::
	trainerhill_getownerstate
	switch VAR_RESULT
	case 0, TrainerHill_Roof_EventScript_Arrived
	case 1, TrainerHill_Roof_EventScript_GivePrize
	case 2, TrainerHill_Roof_EventScript_AlreadyReceivedPrize
TrainerHill_Roof_EventScript_Arrived::
	msgbox TrainerHill_Roof_Text_YouFinallyCameBravo, MSGBOX_DEFAULT
TrainerHill_Roof_EventScript_GivePrize::
	trainerhill_checkbrain
	switch VAR_RESULT
	case TRAINER_HILL_BRAIN_SILVER, TrainerHill_Roof_EventScript_BattleWallySilver
	case TRAINER_HILL_BRAIN_GOLD, TrainerHill_Roof_EventScript_BattleWallyGold
	case TRAINER_HILL_BRAIN_STREAK, TrainerHill_Roof_EventScript_BattleWallySilverStreak
	case TRAINER_HILL_BRAIN_STREAK_LONG, TrainerHill_Roof_EventScript_BattleWallyGoldStreak
	trainerhill_giveprize
	switch VAR_RESULT
	case 0, TrainerHill_Roof_EventScript_ReceivePrize
	case 2, TrainerHill_Roof_EventScript_CheckFinalTime
TrainerHill_Roof_EventScript_ReceivePrize::
	msgbox TrainerHill_Roof_Text_HaveTheMostMarvelousGift, MSGBOX_DEFAULT
	msgbox BattleFrontier_Text_ObtainedXBattlePoints, MSGBOX_GETPOINTS
	goto TrainerHill_Roof_EventScript_CheckFinalTime

TrainerHill_Roof_EventScript_SpectatorsEnter::
	clearflag FLAG_HIDE_TRAINER_HILL_ROOF_SPECTATORS
	@ Wave 1: Floor 1 trainers (Upper flanks: Left and Right)
	addobject LOCALID_SPEC_1
	playse SE_EXIT
	applymovement LOCALID_SPEC_1, TrainerHill_Roof_Movement_Spec1Enter
	delay 16
	addobject LOCALID_SPEC_2
	applymovement LOCALID_SPEC_2, TrainerHill_Roof_Movement_Spec2Enter
	waitmovement LOCALID_SPEC_1
	waitmovement LOCALID_SPEC_2
	@ Wave 2: Floor 2 trainers (Lower flanks: Left and Right)
	addobject LOCALID_SPEC_3
	playse SE_EXIT
	applymovement LOCALID_SPEC_3, TrainerHill_Roof_Movement_Spec3Enter
	delay 16
	addobject LOCALID_SPEC_4
	applymovement LOCALID_SPEC_4, TrainerHill_Roof_Movement_Spec4Enter
	waitmovement LOCALID_SPEC_3
	waitmovement LOCALID_SPEC_4
	@ Wave 3: Floor 3 trainers (South barrier: Inner Left and Inner Right)
	addobject LOCALID_SPEC_5
	playse SE_EXIT
	applymovement LOCALID_SPEC_5, TrainerHill_Roof_Movement_Spec5Enter
	delay 16
	addobject LOCALID_SPEC_6
	applymovement LOCALID_SPEC_6, TrainerHill_Roof_Movement_Spec6Enter
	waitmovement LOCALID_SPEC_5
	waitmovement LOCALID_SPEC_6
	@ Wave 4: Floor 4 trainers (South barrier: Outer Left and Outer Right)
	addobject LOCALID_SPEC_7
	playse SE_EXIT
	applymovement LOCALID_SPEC_7, TrainerHill_Roof_Movement_Spec7Enter
	delay 16
	addobject LOCALID_SPEC_8
	applymovement LOCALID_SPEC_8, TrainerHill_Roof_Movement_Spec8Enter
	waitmovement LOCALID_SPEC_7
	waitmovement LOCALID_SPEC_8
	playse SE_M_ENCORE2
	delay 30
	return

TrainerHill_Roof_EventScript_SpectatorsReactVictory::
	playse SE_M_ENCORE2
	applymovement LOCALID_SPEC_1, TrainerHill_Roof_Movement_SpecJumpRight
	applymovement LOCALID_SPEC_2, TrainerHill_Roof_Movement_SpecJumpLeft
	applymovement LOCALID_SPEC_3, TrainerHill_Roof_Movement_SpecLookAroundLeft
	applymovement LOCALID_SPEC_4, TrainerHill_Roof_Movement_SpecLookAroundRight
	applymovement LOCALID_SPEC_5, TrainerHill_Roof_Movement_SpecJumpUp
	applymovement LOCALID_SPEC_6, TrainerHill_Roof_Movement_SpecJumpUp
	applymovement LOCALID_SPEC_7, TrainerHill_Roof_Movement_SpecLookAroundUp
	applymovement LOCALID_SPEC_8, TrainerHill_Roof_Movement_SpecLookAroundUp
	waitmovement 0
	delay 30
	playse SE_M_ENCORE2
	return

TrainerHill_Roof_EventScript_PrepareArenaAndWally::
	call TrainerHill_Roof_EventScript_SpectatorsEnter
	msgbox TrainerHill_Roof_Text_OwnerTakeBattlePosition, MSGBOX_DEFAULT
	closemessage
	applymovement LOCALID_PLAYER, TrainerHill_Roof_Movement_PlayerTakePosition
	waitmovement 0
	applymovement LOCALID_OWNER, Common_Movement_WalkInPlaceFasterDown
	waitmovement 0
	msgbox TrainerHill_Roof_Text_OwnerIntroduceWally, MSGBOX_DEFAULT
	closemessage
	playse SE_M_ENCORE2
	playse SE_ELEVATOR
	delay 30
	opendoor 15, 5
	waitdooranim
	clearflag FLAG_HIDE_TRAINER_HILL_ROOF_WALLY
	addobject LOCALID_WALLY
	applymovement LOCALID_WALLY, TrainerHill_Roof_Movement_WallyExitElevator
	waitmovement 0
	closedoor 15, 5
	waitdooranim
	applymovement LOCALID_OWNER, Common_Movement_WalkInPlaceFasterDown
	waitmovement 0
	return

TrainerHill_Roof_EventScript_BattleWallySilver::
	msgbox TrainerHill_Roof_Text_OwnerAnnounceWallySilver, MSGBOX_DEFAULT
	closemessage
	call TrainerHill_Roof_EventScript_PrepareArenaAndWally
	msgbox TrainerHill_Roof_Text_WallySilverIntro, MSGBOX_DEFAULT
	special HealPlayerParty
	trainerbattle_no_intro_double TRAINER_WALLY_HILL_SILVER, TrainerHill_Roof_Text_WallySilverDefeat
	specialvar VAR_RESULT, GetBattleOutcome
	goto_if_ne VAR_RESULT, B_OUTCOME_WON, TrainerHill_Roof_EventScript_LostToWally
	call TrainerHill_Roof_EventScript_SpectatorsReactVictory
	msgbox TrainerHill_Roof_Text_WallySilverAwardSymbol, MSGBOX_DEFAULT
	playfanfare MUS_OBTAIN_SYMBOL
	message TrainerHill_Roof_Text_ReceivedAgilitySymbol
	waitmessage
	waitfanfare
	msgbox TrainerHill_Roof_Text_WallySilverFarewell, MSGBOX_DEFAULT
	closemessage
	goto TrainerHill_Roof_EventScript_WallyDepartsAndOwnerAwards

TrainerHill_Roof_EventScript_BattleWallySilverStreak::
	msgbox TrainerHill_Roof_Text_OwnerAnnounceWallySilver, MSGBOX_DEFAULT
	closemessage
	call TrainerHill_Roof_EventScript_PrepareArenaAndWally
	msgbox TrainerHill_Roof_Text_WallySilverStreakIntro, MSGBOX_DEFAULT
	special HealPlayerParty
	trainerbattle_no_intro_double TRAINER_WALLY_HILL_SILVER, TrainerHill_Roof_Text_WallySilverDefeat
	specialvar VAR_RESULT, GetBattleOutcome
	goto_if_ne VAR_RESULT, B_OUTCOME_WON, TrainerHill_Roof_EventScript_LostToWally
	call TrainerHill_Roof_EventScript_SpectatorsReactVictory
	msgbox TrainerHill_Roof_Text_WallySilverStreakFarewell, MSGBOX_DEFAULT
	closemessage
	goto TrainerHill_Roof_EventScript_WallyDepartsAndOwnerAwards

TrainerHill_Roof_EventScript_BattleWallyGold::
	msgbox TrainerHill_Roof_Text_OwnerAnnounceWallyGold, MSGBOX_DEFAULT
	closemessage
	call TrainerHill_Roof_EventScript_PrepareArenaAndWally
	msgbox TrainerHill_Roof_Text_WallyGoldIntro, MSGBOX_DEFAULT
	special HealPlayerParty
	trainerbattle_no_intro_double TRAINER_WALLY_HILL_GOLD, TrainerHill_Roof_Text_WallyGoldDefeat
	specialvar VAR_RESULT, GetBattleOutcome
	goto_if_ne VAR_RESULT, B_OUTCOME_WON, TrainerHill_Roof_EventScript_LostToWally
	call TrainerHill_Roof_EventScript_SpectatorsReactVictory
	msgbox TrainerHill_Roof_Text_WallyGoldAwardSymbol, MSGBOX_DEFAULT
	playfanfare MUS_OBTAIN_SYMBOL
	message TrainerHill_Roof_Text_AgilitySymbolTookGoldenShine
	waitmessage
	waitfanfare
	msgbox TrainerHill_Roof_Text_WallyGoldFarewell, MSGBOX_DEFAULT
	closemessage
	goto TrainerHill_Roof_EventScript_WallyDepartsAndOwnerAwards

TrainerHill_Roof_EventScript_BattleWallyGoldStreak::
	msgbox TrainerHill_Roof_Text_OwnerAnnounceWallyGold, MSGBOX_DEFAULT
	closemessage
	call TrainerHill_Roof_EventScript_PrepareArenaAndWally
	msgbox TrainerHill_Roof_Text_WallyGoldStreakIntro, MSGBOX_DEFAULT
	special HealPlayerParty
	trainerbattle_no_intro_double TRAINER_WALLY_HILL_GOLD, TrainerHill_Roof_Text_WallyGoldDefeat
	specialvar VAR_RESULT, GetBattleOutcome
	goto_if_ne VAR_RESULT, B_OUTCOME_WON, TrainerHill_Roof_EventScript_LostToWally
	call TrainerHill_Roof_EventScript_SpectatorsReactVictory
	msgbox TrainerHill_Roof_Text_WallyGoldStreakFarewell, MSGBOX_DEFAULT
	closemessage
	goto TrainerHill_Roof_EventScript_WallyDepartsAndOwnerAwards

TrainerHill_Roof_EventScript_WallyDepartsAndOwnerAwards::
	opendoor 15, 5
	waitdooranim
	applymovement LOCALID_WALLY, TrainerHill_Roof_Movement_WallyExitToElevator
	waitmovement 0
	removeobject LOCALID_WALLY
	setflag FLAG_HIDE_TRAINER_HILL_ROOF_WALLY
	closedoor 15, 5
	waitdooranim
	playse SE_ELEVATOR
	playse SE_M_ENCORE2
	applymovement LOCALID_OWNER, TrainerHill_Roof_Movement_OwnerApproachPlayer
	waitmovement 0
	trainerhill_buffermodename
	special DoDomeConfetti
	playse SE_M_ENCORE2
	msgbox TrainerHill_Roof_Text_OwnerProclaimChampion, MSGBOX_DEFAULT
	msgbox TrainerHill_Roof_Text_OwnerPostVictory, MSGBOX_DEFAULT
	trainerhill_givebrainprize
	msgbox BattleFrontier_Text_ObtainedXBattlePoints, MSGBOX_GETPOINTS
	msgbox TrainerHill_Roof_Text_OwnerReturnToReception, MSGBOX_DEFAULT
	closemessage
	setvar VAR_TEMP_5, 0
	warp MAP_TRAINER_HILL_ENTRANCE, 9, 6
	waitstate
	end

TrainerHill_Roof_EventScript_LostToWally::
	goto TrainerHill_1F_EventScript_Lost

TrainerHill_Roof_Movement_PlayerTakePosition:
	walk_left
	walk_left
	walk_in_place_faster_right
	step_end

TrainerHill_Roof_Movement_OwnerApproachPlayer:
	walk_down
	walk_left
	walk_in_place_faster_left
	step_end

TrainerHill_Roof_Movement_WallyExitElevator:
	walk_down
	walk_down
	walk_down
	walk_left
	walk_in_place_faster_left
	step_end

TrainerHill_Roof_Movement_WallyExitToElevator:
	walk_right
	walk_up
	walk_up
	walk_up
	set_invisible
	step_end

TrainerHill_Roof_Movement_Spec1Enter:
	walk_down
	walk_left
	walk_down
	walk_down
	walk_left
	walk_in_place_faster_right
	step_end

TrainerHill_Roof_Movement_Spec2Enter:
	walk_down
	walk_down
	walk_down
	walk_down
	walk_right
	walk_right
	walk_right
	walk_right
	walk_right
	walk_right
	walk_right
	walk_up
	walk_right
	walk_in_place_faster_left
	step_end

TrainerHill_Roof_Movement_Spec3Enter:
	walk_down
	walk_left
	walk_down
	walk_down
	walk_down
	walk_left
	walk_in_place_faster_right
	step_end

TrainerHill_Roof_Movement_Spec4Enter:
	walk_down
	walk_down
	walk_down
	walk_down
	walk_right
	walk_right
	walk_right
	walk_right
	walk_right
	walk_right
	walk_right
	walk_right
	walk_in_place_faster_left
	step_end

TrainerHill_Roof_Movement_Spec5Enter:
	walk_down
	walk_left
	walk_down
	walk_down
	walk_down
	walk_down
	walk_right
	walk_right
	walk_right
	walk_in_place_faster_up
	step_end

TrainerHill_Roof_Movement_Spec6Enter:
	walk_down
	walk_down
	walk_down
	walk_down
	walk_right
	walk_right
	walk_right
	walk_right
	walk_down
	walk_in_place_faster_up
	step_end

TrainerHill_Roof_Movement_Spec7Enter:
	walk_down
	walk_left
	walk_down
	walk_down
	walk_down
	walk_down
	walk_right
	walk_right
	walk_in_place_faster_up
	step_end

TrainerHill_Roof_Movement_Spec8Enter:
	walk_down
	walk_down
	walk_down
	walk_down
	walk_right
	walk_right
	walk_right
	walk_right
	walk_right
	walk_down
	walk_in_place_faster_up
	step_end

TrainerHill_Roof_Movement_SpecJumpRight:
	emote_double_exclamation_mark
	jump_in_place_right
	step_end

TrainerHill_Roof_Movement_SpecJumpLeft:
	emote_double_exclamation_mark
	jump_in_place_left
	step_end

TrainerHill_Roof_Movement_SpecLookAroundLeft:
	emote_exclamation_mark
	walk_in_place_fast_right
	walk_in_place_fast_up
	walk_in_place_fast_right
	step_end

TrainerHill_Roof_Movement_SpecLookAroundRight:
	emote_exclamation_mark
	walk_in_place_fast_left
	walk_in_place_fast_down
	walk_in_place_fast_left
	step_end

TrainerHill_Roof_Movement_SpecJumpUp:
	emote_double_exclamation_mark
	jump_in_place_up
	step_end

TrainerHill_Roof_Movement_SpecLookAroundUp:
	emote_exclamation_mark
	walk_in_place_fast_left
	walk_in_place_fast_right
	walk_in_place_fast_up
	step_end

TrainerHill_Roof_EventScript_CheckFinalTime::
	trainerhill_finaltime
	switch VAR_RESULT
	case 0, TrainerHill_Roof_EventScript_NewRecord
	case 1, TrainerHill_Roof_EventScript_NoNewRecord
	case 2, TrainerHill_Roof_EventScript_EndSpeakToOwner
TrainerHill_Roof_EventScript_NewRecord::
	msgbox TrainerHill_Roof_Text_GotHereMarvelouslyQuickly, MSGBOX_DEFAULT
	goto TrainerHill_Roof_EventScript_EndSpeakToOwner
	end

TrainerHill_Roof_EventScript_NoNewRecord::
	msgbox TrainerHill_Roof_Text_YouWerentVeryQuick, MSGBOX_DEFAULT
	goto TrainerHill_Roof_EventScript_EndSpeakToOwner
	end

TrainerHill_Roof_EventScript_EndSpeakToOwner::
	msgbox TrainerHill_Roof_Text_ArriveZippierNextTime, MSGBOX_DEFAULT
	releaseall
	end

TrainerHill_Roof_EventScript_AlreadyReceivedPrize::
	msgbox TrainerHill_Roof_Text_ArriveZippierNextTime, MSGBOX_DEFAULT
	releaseall
	end
