TrainerHill_Entrance_MapScripts::
	map_script MAP_SCRIPT_ON_RESUME, TrainerHill_Entrance_OnResume
	map_script MAP_SCRIPT_ON_RETURN_TO_FIELD, TrainerHill_Entrance_OnReturn
	map_script MAP_SCRIPT_ON_TRANSITION, TrainerHill_Entrance_OnTransition
	map_script MAP_SCRIPT_ON_LOAD, TrainerHill_Entrance_OnLoad
	map_script MAP_SCRIPT_ON_FRAME_TABLE, TrainerHill_Entrance_OnFrame
	map_script MAP_SCRIPT_ON_WARP_INTO_MAP_TABLE, TrainerHill_Entrance_OnWarpTable
	.byte 0

TrainerHill_Entrance_OnWarpTable:
	map_script_2 VAR_TEMP_0, 0, TrainerHill_Entrance_EventScript_CheckPlayerOrientation
	.2byte 0

TrainerHill_Entrance_EventScript_CheckPlayerOrientation::
	getplayerxy VAR_TEMP_2, VAR_TEMP_3
	goto_if_le VAR_TEMP_3, 8, TrainerHill_Entrance_EventScript_TurnPlayerSouth
	goto_if_eq VAR_TEMP_3, 11, TrainerHill_Entrance_EventScript_TurnPlayerNorth
	end

TrainerHill_Entrance_EventScript_TurnPlayerSouth::
	turnobject LOCALID_PLAYER, DIR_SOUTH
	end

TrainerHill_Entrance_EventScript_TurnPlayerNorth::
	turnobject LOCALID_PLAYER, DIR_NORTH
	end

TrainerHill_Entrance_OnTransition:
	setflag FLAG_LANDMARK_TRAINER_HILL
	getplayerxy VAR_TEMP_D, VAR_RESULT
	end

TrainerHill_Entrance_OnResume:
	trainerhill_resumetimer
	setvar VAR_TEMP_0, 0
	getplayerxy VAR_TEMP_2, VAR_TEMP_3
	goto_if_le VAR_TEMP_3, 8, TrainerHill_Entrance_EventScript_PlayerDontFaceAttendant
	goto_if_eq VAR_TRAINER_HILL_IS_ACTIVE, 0, TrainerHill_Entrance_EventScript_PlayerDontFaceAttendant
	trainerhill_getusingereader
	goto_if_eq VAR_RESULT, FALSE, TrainerHill_Entrance_EventScript_TryFaceAttendant  @ VAR_RESULT always FALSE here
	setobjectxy LOCALID_PLAYER, 3, 11
	applymovement LOCALID_PLAYER, TrainerHill_Entrance_Movement_PlayerFaceAttendant
	end

TrainerHill_Entrance_EventScript_TryFaceAttendant::
	trainerhill_getwon
	goto_if_eq VAR_RESULT, TRUE, TrainerHill_Entrance_EventScript_PlayerDontFaceAttendant
	applymovement LOCALID_PLAYER, TrainerHill_Entrance_Movement_PlayerFaceAttendant
	end

TrainerHill_Entrance_EventScript_PlayerDontFaceAttendant::
	end

TrainerHill_Entrance_OnReturn:
	addobject LOCALID_TRAINER_HILL_ATTENDANT
	addobject LOCALID_TRAINER_HILL_MAN
	addobject LOCALID_TRAINER_HILL_GIRL
	end

TrainerHill_Entrance_OnLoad:
	call_if_eq VAR_TEMP_D, 19, TrainerHill_Entrance_EventScript_OpenCounterDoor
	end

TrainerHill_Entrance_EventScript_OpenCounterDoor::
	setmetatile 19, 3, METATILE_TrainerHill_GreenFloorTile, FALSE
	return

TrainerHill_Entrance_OnFrame:
	map_script_2 VAR_TEMP_0, 0, TrainerHill_Entrance_EventScript_ExitChallenge
	map_script_2 VAR_TEMP_D, 19, TrainerHill_Entrance_EventScript_ExitElevator
	map_script_2 VAR_TEMP_1, 1, TrainerHill_EventScript_WarpToEntranceCounter
	.2byte 0

TrainerHill_Entrance_EventScript_ExitElevator::
	lockall
	applymovement LOCALID_PLAYER, TrainerHill_Entrance_Movement_PlayerExitElevator
	waitmovement 0
	setmetatile 19, 3, METATILE_TrainerHill_CounterDoor, TRUE
	special DrawWholeMapView
	playse SE_CLICK
	waitse
	setvar VAR_TEMP_D, 0
	releaseall
	end

TrainerHill_Entrance_EventScript_ExitChallenge::
	setvar VAR_TEMP_0, 1
	getplayerxy VAR_TEMP_2, VAR_TEMP_3
	goto_if_le VAR_TEMP_3, 8, TrainerHill_Entrance_EventScript_EndExitChallenge
	trainerhill_getstatus
	switch VAR_RESULT
	case TRAINER_HILL_PLAYER_STATUS_LOST, TrainerHill_Entrance_EventScript_ExitChallengeLost
	case TRAINER_HILL_PLAYER_STATUS_BRAIN_WON, TrainerHill_Entrance_EventScript_ExitChallengeBrainWon
	case TRAINER_HILL_PLAYER_STATUS_ECARD_SCANNED, TrainerHill_Entrance_EventScript_ExitChallengeECard
	case TRAINER_HILL_PLAYER_STATUS_DIDNT_SAVE, TrainerHill_Entrance_EventScript_ExitChallengeDidntSave
	case TRAINER_HILL_PLAYER_STATUS_NORMAL, TrainerHill_Entrance_EventScript_EndExitChallenge

TrainerHill_Entrance_EventScript_ExitChallengeDidntSave::
	lockall
	applymovement LOCALID_PLAYER, TrainerHill_Entrance_Movement_PlayerFaceAttendant
	msgbox TrainerHill_Entrance_Text_FailedToSaveBeforeQuitting, MSGBOX_DEFAULT
	message TrainerHill_Entrance_Text_RecordWillBeSaved
	waitmessage
	setvar VAR_TRAINER_HILL_IS_ACTIVE, 0
	setvar VAR_TEMP_5, 0
	special HealPlayerParty
	callnative UpdateFollowingPokemon
	trainerhill_savechallenge
	playse SE_SAVE
	waitse
	msgbox TrainerHill_Entrance_Text_HopeToSeeYouAgain, MSGBOX_DEFAULT
	closemessage
	releaseall
	end

TrainerHill_Entrance_EventScript_ExitChallengeBrainWon::
	lockall
	applymovement LOCALID_PLAYER, TrainerHill_Entrance_Movement_PlayerFaceAttendant
	msgbox TrainerHill_Entrance_Text_BrainVictoryReception, MSGBOX_DEFAULT
	goto TrainerHill_Entrance_EventScript_AskRecordBattle

TrainerHill_Entrance_EventScript_ExitChallengeLost::
	lockall
	applymovement LOCALID_PLAYER, TrainerHill_Entrance_Movement_PlayerFaceAttendant
	msgbox TrainerHill_Entrance_Text_TooBadTremendousEffort, MSGBOX_DEFAULT
	goto TrainerHill_Entrance_EventScript_AskRecordBattle

TrainerHill_Entrance_EventScript_AskRecordBattle::
	setvar VAR_TRAINER_HILL_IS_ACTIVE, 0
	setvar VAR_TEMP_5, 0
	special HealPlayerParty
	callnative UpdateFollowingPokemon
	message TrainerHill_Entrance_Text_RecordWillBeSaved
	waitmessage
	trainerhill_savechallenge
	playse SE_SAVE
	waitse
	call BattleFrontier_EventScript_GetCantRecordBattle
	goto_if_eq VAR_RESULT, TRUE, TrainerHill_Entrance_EventScript_EndChallenge
	message TrainerHill_Entrance_Text_RecordLastMatch
	waitmessage
	multichoicedefault 20, 8, MULTI_YESNO, 1, FALSE
	switch VAR_RESULT
	case 1, TrainerHill_Entrance_EventScript_EndChallenge
	case 0, TrainerHill_Entrance_EventScript_RecordBattle
	case MULTI_B_PRESSED, TrainerHill_Entrance_EventScript_EndChallenge

TrainerHill_Entrance_EventScript_RecordBattle::
	call BattleFrontier_EventScript_SaveBattle
TrainerHill_Entrance_EventScript_EndChallenge::
	msgbox TrainerHill_Entrance_Text_HopeToSeeYouAgain, MSGBOX_DEFAULT
	goto TrainerHill_Entrance_EventScript_PlayerExitChallenge

TrainerHill_Entrance_EventScript_ExitChallengeECard::
	lockall
	applymovement LOCALID_PLAYER, TrainerHill_Entrance_Movement_PlayerFaceAttendant
	msgbox TrainerHill_Entrance_Text_MovedReceptionHereForSwitch, MSGBOX_DEFAULT
	setvar VAR_TRAINER_HILL_IS_ACTIVE, 0
	setvar VAR_TEMP_5, 0
	special HealPlayerParty
	callnative UpdateFollowingPokemon
TrainerHill_Entrance_EventScript_PlayerExitChallenge::
	closemessage
	releaseall
TrainerHill_Entrance_EventScript_EndExitChallenge::
	end

TrainerHill_Entrance_EventScript_Attendant::
	lock
	faceplayer
	trainerhill_inchallenge
	goto_if_eq VAR_RESULT, TRUE, TrainerHill_Entrance_EventScript_HopeYouGiveItYourBest
	goto_if_unset FLAG_SYS_GAME_CLEAR, TrainerHill_Entrance_EventScript_Closed
	msgbox TrainerHill_Entrance_Text_WelcomeToTrainerHill, MSGBOX_DEFAULT
TrainerHill_Entrance_EventScript_AskChallengeTrainers::
	message TrainerHill_Entrance_Text_LikeToChallengeTrainers
	waitmessage
	multichoice 17, 6, MULTI_CHALLENGEINFO, FALSE
	switch VAR_RESULT
	case 0, TrainerHill_Entrance_EventScript_ChooseChallenge
	case 1, TrainerHill_Entrance_EventScript_Info
	case 2, TrainerHill_Entrance_EventScript_CancelEntry
	case MULTI_B_PRESSED, TrainerHill_Entrance_EventScript_CancelEntry
	end

TrainerHill_Entrance_EventScript_HopeYouGiveItYourBest::
	msgbox TrainerHill_Entrance_Text_HopeYouGiveItYourBest, MSGBOX_DEFAULT
	release
	end

TrainerHill_Entrance_EventScript_Info::
	msgbox TrainerHill_Entrance_Text_ExplainTrainerHill, MSGBOX_DEFAULT
	goto TrainerHill_Entrance_EventScript_AskChallengeTrainers
	end

TrainerHill_Entrance_EventScript_ChooseChallenge::
	multichoice 13, 2, MULTI_TAG_MATCH_TYPE, FALSE
	switch VAR_RESULT
	case 4, TrainerHill_Entrance_EventScript_CancelEntry
	case MULTI_B_PRESSED, TrainerHill_Entrance_EventScript_CancelEntry
	copyvar VAR_0x8006, VAR_RESULT
	message TrainerHill_Entrance_Text_WhichLevelMode
	waitmessage
	multichoice 17, 6, MULTI_LEVEL_MODE, FALSE
	switch VAR_RESULT
	case FRONTIER_LVL_TENT, TrainerHill_Entrance_EventScript_CancelEntry
	case MULTI_B_PRESSED, TrainerHill_Entrance_EventScript_CancelEntry
	case FRONTIER_LVL_50, TrainerHill_Entrance_EventScript_CheckLvl50
	case FRONTIER_LVL_OPEN, TrainerHill_Entrance_EventScript_StartOpenLevel
	goto TrainerHill_Entrance_EventScript_CancelEntry
	end

TrainerHill_Entrance_EventScript_CheckLvl50::
	trainerhill_getpartymaxlevel
	goto_if_gt VAR_RESULT, FRONTIER_MAX_LEVEL_50, TrainerHill_Entrance_EventScript_PartyLevelTooHigh50
	trainerhill_setlvlmode FRONTIER_LVL_50
	goto TrainerHill_Entrance_EventScript_EnterChallenge
	end

TrainerHill_Entrance_EventScript_StartOpenLevel::
	trainerhill_setlvlmode FRONTIER_LVL_OPEN
	goto TrainerHill_Entrance_EventScript_EnterChallenge
	end

TrainerHill_Entrance_EventScript_PartyLevelTooHigh50::
	msgbox TrainerHill_Entrance_Text_PartyLevelTooHigh50, MSGBOX_DEFAULT
	closemessage
	setvar VAR_TEMP_5, 0
	releaseall
	end

TrainerHill_Entrance_EventScript_EnterChallenge::
	msgbox TrainerHill_Entrance_Text_SaveBeforeChallenge, MSGBOX_YESNO
	switch VAR_RESULT
	case NO, TrainerHill_Entrance_EventScript_CancelEntry
	case MULTI_B_PRESSED, TrainerHill_Entrance_EventScript_CancelEntry
	closemessage
	trainerhill_setsaved
	trainerhill_setmode VAR_0x8006
	setvar VAR_TRAINER_HILL_IS_ACTIVE, 1
	call Common_EventScript_SaveGame
	goto_if_eq VAR_RESULT, FALSE, TrainerHill_Entrance_EventScript_CancelChallengeSaveFailed
	setvar VAR_TEMP_5, 0
	special HealPlayerParty
	callnative UpdateFollowingPokemon
	applymovement LOCALID_TRAINER_HILL_ATTENDANT, TrainerHill_Entrance_Movement_AttendantStepAside
	applymovement LOCALID_PLAYER, TrainerHill_Entrance_Movement_PlayerStepInCorridor
	waitmovement 0
	msgbox TrainerHill_Entrance_Text_TimeProgessGetSetGo, MSGBOX_DEFAULT
	closemessage
	applymovement LOCALID_PLAYER, TrainerHill_Entrance_Movement_PlayerWalkUp
	waitmovement 0
	trainerhill_start
	releaseall
	end

TrainerHill_Entrance_EventScript_CancelChallengeSaveFailed::
	trainerhill_clearsaved
	setvar VAR_TRAINER_HILL_IS_ACTIVE, 0
	goto TrainerHill_Entrance_EventScript_CancelEntry

TrainerHill_Entrance_Movement_AttendantStepAside:
	walk_up
	walk_left
	face_right
	step_end

TrainerHill_Entrance_Movement_PlayerStepInCorridor:
	walk_up
	walk_up
	face_left
	step_end

TrainerHill_Entrance_Movement_PlayerWalkUp:
	walk_up
	step_end

TrainerHill_Entrance_EventScript_CancelEntry::
	setvar VAR_TEMP_5, 0
	msgbox TrainerHill_Entrance_Text_PleaseVisitUsAgain, MSGBOX_DEFAULT
	closemessage
	releaseall
	end

TrainerHill_Entrance_EventScript_RetireTrigger::
	lockall
	applymovement LOCALID_PLAYER, Common_Movement_FaceLeft
	applymovement LOCALID_TRAINER_HILL_ATTENDANT, Common_Movement_FaceRight
	waitmovement 0
	msgbox TrainerHill_Entrance_Text_RetireFromChallenge, MSGBOX_YESNO
	switch VAR_RESULT
	case YES, TrainerHill_Entrance_EventScript_Retire
	case NO, TrainerHill_Entrance_EventScript_DontRetire
	case MULTI_B_PRESSED, TrainerHill_Entrance_EventScript_DontRetire
	end

TrainerHill_Entrance_EventScript_Retire::
	message TrainerHill_Entrance_Text_RecordWillBeSaved
	waitmessage
	trainerhill_retire
	setvar VAR_TRAINER_HILL_IS_ACTIVE, 0
	setvar VAR_TEMP_5, 0
	special HealPlayerParty
	callnative UpdateFollowingPokemon
	trainerhill_savechallenge
	playse SE_SAVE
	waitse
	msgbox TrainerHill_Entrance_Text_HopeToSeeYouAgain, MSGBOX_DEFAULT
	closemessage
	applymovement LOCALID_PLAYER, TrainerHill_Entrance_Movement_PlayerExitCorridor
	applymovement LOCALID_TRAINER_HILL_ATTENDANT, TrainerHill_Entrance_Movement_AttendantReturnToPost
	waitmovement 0
	releaseall
	end

TrainerHill_Entrance_EventScript_DontRetire::
	closemessage
	applymovement LOCALID_PLAYER, TrainerHill_Entrance_Movement_PushPlayerBackFromExit
	waitmovement 0
	releaseall
	end

TrainerHill_Entrance_Movement_PlayerExitCorridor:
	walk_down
	walk_down
	step_end

TrainerHill_Entrance_Movement_AttendantReturnToPost:
	walk_right
	walk_down
	face_down
	step_end

TrainerHill_Entrance_Movement_PushPlayerBackFromExit:
	walk_up
	step_end

TrainerHill_Entrance_EventScript_Closed::
	msgbox TrainerHill_Entrance_Text_StillGettingReady, MSGBOX_DEFAULT
	closemessage
	releaseall
	end

TrainerHill_Entrance_Movement_PlayerFaceAttendant:
	face_up
	step_end

TrainerHill_Entrance_Movement_PlayerExitElevator:
	walk_down
	walk_down
	step_end

TrainerHill_Entrance_EventScript_Records::
	lockall
	fadescreen FADE_TO_BLACK
	setvar VAR_0x8004, 0
	special ShowTrainerHillRecords
	releaseall
	end

TrainerHill_Entrance_EventScript_Man::
	goto_if_unset FLAG_SYS_GAME_CLEAR, TrainerHill_Entrance_EventScript_ManTrainerHillClosed
	msgbox TrainerHill_Entrance_Text_WhatSortOfTrainersAreAhead, MSGBOX_NPC
	end

TrainerHill_Entrance_EventScript_ManTrainerHillClosed::
	msgbox TrainerHill_Entrance_Text_CantWaitToTestTheWaters, MSGBOX_NPC
	end

TrainerHill_Entrance_EventScript_Girl::
	goto_if_unset FLAG_SYS_GAME_CLEAR, TrainerHill_Entrance_EventScript_GirlTrainerHillClosed
	msgbox TrainerHill_Entrance_Text_FriendsTryingToReachTimeBoardTop, MSGBOX_NPC
	end

TrainerHill_Entrance_EventScript_GirlTrainerHillClosed::
	msgbox TrainerHill_Entrance_Text_DoYouKnowWhenTheyOpen, MSGBOX_NPC
	end

TrainerHill_Entrance_Text_StillGettingReady:
	.string "Where the speed of TRAINERS\n"
	.string "is put to the test…\p"
	.string "This is the BATTLE HILL.\p"
	.string "Unfortunately, we're still getting\n"
	.string "things ready. Please come back later!$"

TrainerHill_Entrance_Text_WelcomeToTrainerHill:
	.string "Where the speed of TRAINERS\n"
	.string "is put to the test!\p"
	.string "Welcome to the BATTLE HILL!\p"
	.string "I am your guide to the Time Attack\n"
	.string "Tag Battle Challenge.$"

TrainerHill_Entrance_Text_SaveBeforeChallenge:
	.string "Before you begin your BATTLE HILL\n"
	.string "challenge, I must save the game.\l"
	.string "Is that okay?$"

TrainerHill_Entrance_Text_FailedToSaveBeforeQuitting:
	.string "Excuse me!\p"
	.string "You didn't save before you quit\n"
	.string "your challenge last time.\p"
	.string "Because of that, your challenge\n"
	.string "so far has been disqualified.\l"
	.string "Sorry!$"

TrainerHill_Entrance_Text_RetireFromChallenge:
	.string "Would you like to retire from your\n"
	.string "BATTLE HILL challenge?$"

TrainerHill_Entrance_Text_LikeToChallengeTrainers:
	.string "Would you like to take the\n"
	.string "BATTLE HILL challenge?$"

TrainerHill_Entrance_Text_TimeProgessGetSetGo:
	.string "I will time your progress.\n"
	.string "Best of luck!\p"
	.string "On your marks…\p"
	.string "Get set…\p"
	.string "Go!$"

TrainerHill_Entrance_Text_PleaseVisitUsAgain:
	.string "We look forward to seeing you on\n"
	.string "another challenge!$"

TrainerHill_Entrance_Text_TooBadTremendousEffort:
	.string "Thank you for participating!\n"
	.string "I commend your valiant effort.$"

TrainerHill_Entrance_Text_HopeYouGiveItYourBest:
	.string "I hope you give it your best.$"

TrainerHill_Entrance_Text_MovedReceptionHereForSwitch:
	.string "When the TRAINERS switch places,\n"
	.string "the movement can be hectic.\p"
	.string "To avoid the stampede, we moved\n"
	.string "the reception counter here.\p"
	.string "I'm sorry for the inconvenience.$"

TrainerHill_Entrance_Text_ThankYouForPlaying:
	.string "Thank you for playing!$"

TrainerHill_Entrance_Text_ExplainTrainerHill:
	.string "At the BATTLE HILL, we conduct\n"
	.string "the Time Attack Tag Challenge.\p"
	.string "It is an endurance race measuring\n"
	.string "how quickly you can scale all four\l"
	.string "floors to reach the rooftop arena.\p"
	.string "On each floor, you will face two\n"
	.string "TRAINERS in a TAG BATTLE.\p"
	.string "You may enter with a full team of\n"
	.string "six POKéMON, and no species or\l"
	.string "held items are restricted.\p"
	.string "Battle Points are awarded on the\n"
	.string "roof based on your clear time.\p"
	.string "Saving inside is prohibited.\p"
	.string "If you quit without finishing,\n"
	.string "your challenge is disqualified.$"

@ Unused
TrainerHill_Entrance_Text_NeedAtLeastTwoPokemon:
	.string "Oh, I'm sorry, but you appear to have\n"
	.string "only one POKéMON with you.\p"
	.string "You will need at least two POKéMON\n"
	.string "to enter this event.$"

TrainerHill_Roof_Text_YouFinallyCameBravo:
	.string "Hm! Hm!\p"
	.string "You finally came!\n"
	.string "Yes, you have arrived!\p"
	.string "Wait! Don't say it!\n"
	.string "I know why you came all the way\l"
	.string "here by yourself!\p"
	.string "You wanted to see me, the owner\n"
	.string "of the BATTLE HILL, because…\p"
	.string "You want to form a tag team with me!\n"
	.string "Wa-hoo!\p"
	.string "…Uh?\n"
	.string "That's not it?\p"
	.string "Anyway, I watched you on your way up.\n"
	.string "Marvelous battling! Bravo, indeed!$"

TrainerHill_Roof_Text_HaveTheMostMarvelousGift:
	.string "For a marvelous someone like you,\n"
	.string "take these marvelous Battle Points!$"

TrainerHill_Roof_Text_OwnerAnnounceWallySilver:
	.string "Bravo! Welcome to the summit!\p"
	.string "I watched your ascent, and your speed\n"
	.string "across every floor was astonishing!\p"
	.string "A challenge so marvelous warrants\n"
	.string "an exhibition of the highest order!\p"
	.string "Our FRONTIER BRAIN has arrived!$"

TrainerHill_Roof_Text_OwnerAnnounceWallyGold:
	.string "Bravo! Welcome back to the summit!\p"
	.string "Your agility has reached a realm\n"
	.string "few TRAINERS ever attain!\p"
	.string "The crowd eagerly awaits this clash!\n"
	.string "Our FRONTIER BRAIN is here!$"

TrainerHill_Roof_Text_OwnerRestoreParty:
	.string "The TRAINERS you defeated have\n"
	.string "gathered around the arena to watch!\p"
	.string "First, I shall restore your\n"
	.string "POKéMON to full health!$"

TrainerHill_Roof_Text_OwnerTakeBattlePosition:
	.string "Challenger! Step forward to the\n"
	.string "arena and take your battle stance!$"

TrainerHill_Roof_Text_OwnerIntroduceWally:
	.string "Ladies and gentlemen!\p"
	.string "Please welcome our FRONTIER BRAIN,\n"
	.string "WALLY the HILL PRODIGY!$"

TrainerHill_Roof_Text_WallySilverIntro:
	.string "WALLY: Hi, {PLAYER}!\p"
	.string "Remember that RALTS you helped me\n"
	.string "catch back on ROUTE 102?\p"
	.string "Ever since our battle on VICTORY\n"
	.string "ROAD, my team and I kept training!\p"
	.string "When the Owner invited me to be\n"
	.string "the FRONTIER BRAIN here, I dreamed\l"
	.string "of facing you on this rooftop!\p"
	.string "I'm not the frail kid from before…\n"
	.string "Let me show you how strong we are!$"

TrainerHill_Roof_Text_WallySilverDefeat:
	.string "Wow…\n"
	.string "{PLAYER}, you are strong after all!$"

TrainerHill_Roof_Text_WallySilverAwardSymbol:
	.string "WALLY: That was breathtaking!\p"
	.string "Battling you as a FRONTIER BRAIN\n"
	.string "is the greatest honor!\p"
	.string "Your FRONTIER PASS, please!\n"
	.string "I want to present you with this!$"

TrainerHill_Roof_Text_ReceivedAgilitySymbol:
	.string "The Agility Symbol was embossed on\n"
	.string "the FRONTIER PASS!$"

TrainerHill_Roof_Text_WallySilverFarewell:
	.string "WALLY: {PLAYER}, losing to you in\n"
	.string "MAUVILLE made me stronger.\p"
	.string "Today, you showed me once more how\n"
	.string "much higher we can aim!\p"
	.string "I won't give up. One day, I will\n"
	.string "catch up to you, {PLAYER}!\p"
	.string "Until then, take care!$"

TrainerHill_Roof_Text_WallySilverStreakIntro:
	.string "WALLY: Hi again, {PLAYER}!\p"
	.string "Whenever I see you climbing the\n"
	.string "BATTLE HILL, my heart races!\p"
	.string "My team is ready to give it all\n"
	.string "we've got! Here we come!$"

TrainerHill_Roof_Text_WallySilverStreakFarewell:
	.string "WALLY: What a thrilling match!\p"
	.string "Battles with you remind me of\n"
	.string "why I fell in love with POKéMON.\p"
	.string "I won't stop training either!\n"
	.string "Thank you so much, {PLAYER}!$"

TrainerHill_Roof_Text_WallyGoldIntro:
	.string "WALLY: Hi, {PLAYER}!\p"
	.string "Before I met you, I hardly ever\n"
	.string "left my house in PETALBURG…\p"
	.string "Now look at us, standing atop the\n"
	.string "pinnacle of the BATTLE HILL!\p"
	.string "GARDEVOIR and I gave everything we\n"
	.string "had to master this facility!\p"
	.string "Show me the true summit of your\n"
	.string "power, {PLAYER}! Here I come!$"

TrainerHill_Roof_Text_WallyGoldDefeat:
	.string "Incredible…!\n"
	.string "You truly are my hero, {PLAYER}!$"

TrainerHill_Roof_Text_WallyGoldAwardSymbol:
	.string "WALLY: That was magnificent!\p"
	.string "To share this battle with the\n"
	.string "TRAINER who inspired my journey…\p"
	.string "Your FRONTIER PASS, please!\n"
	.string "You've earned the Golden Agility!$"

TrainerHill_Roof_Text_AgilitySymbolTookGoldenShine:
	.string "The Agility Symbol took on\n"
	.string "a golden shine!$"

TrainerHill_Roof_Text_WallyGoldFarewell:
	.string "WALLY: Thank you, {PLAYER}.\p"
	.string "From catching RALTS together to\n"
	.string "facing off as a FRONTIER BRAIN…\p"
	.string "All of my journey happened because\n"
	.string "you believed in me.\p"
	.string "I will keep training so I can\n"
	.string "give you an even greater match!\p"
	.string "Thank you for everything, {PLAYER}!$"

TrainerHill_Roof_Text_WallyGoldStreakIntro:
	.string "WALLY: Hi, {PLAYER}!\p"
	.string "No matter how many times we clash,\n"
	.string "the excitement never fades away!\p"
	.string "We won't hold back a single ounce\n"
	.string "of energy! Let's go, {PLAYER}!$"

TrainerHill_Roof_Text_WallyGoldStreakFarewell:
	.string "WALLY: Incredible battle!\p"
	.string "You keep showing me what a true\n"
	.string "CHAMPION can achieve.\p"
	.string "I'll keep chasing your footsteps!\n"
	.string "Thank you so much, {PLAYER}!$"

TrainerHill_Roof_Text_OwnerProclaimChampion:
	.string "{PLAYER} is the\n"
	.string "{STR_VAR_1} Champion!\p"
	.string "Congratulations!$"

TrainerHill_Roof_Text_OwnerPostVictory:
	.string "As proprietor of this facility,\n"
	.string "I present your Battle Points!$"

TrainerHill_Roof_Text_OwnerReturnToReception:
	.string "Let us return to the reception\n"
	.string "counter below!$"

TrainerHill_Entrance_Text_BrainVictoryReception:
	.string "Splendid!\p"
	.string "You defeated the HILL PRODIGY and\n"
	.string "conquered the summit of BATTLE HILL!$"

TrainerHill_Entrance_Text_RecordWillBeSaved:
	.string "Your record will be saved.\n"
	.string "Please wait.$"

TrainerHill_Entrance_Text_RecordLastMatch:
	.string "Would you like to record your last\n"
	.string "match on your FRONTIER PASS?$"

TrainerHill_Entrance_Text_HopeToSeeYouAgain:
	.string "We look forward to your\n"
	.string "next challenge!$"

TrainerHill_Roof_Text_GotHereMarvelouslyQuickly:
	.string "Oh, hold on here! Did you possibly get\n"
	.string "here marvelously quickly?\p"
	.string "How splendid! You needn't have\n"
	.string "hurried so to see me!\p"
	.string "That is so delightful. I'll have the Time\n"
	.string "Board at the reception updated!$"

TrainerHill_Roof_Text_YouWerentVeryQuick:
	.string "But, oh…\n"
	.string "You weren't very quick getting here.$"

TrainerHill_Roof_Text_ArriveZippierNextTime:
	.string "Perhaps it would please me more if you\n"
	.string "arrived zippier next time.\p"
	.string "Then, I should be pleased to form\n"
	.string "a tag team with you!$"

TrainerHill_Roof_Text_UntilWeMeetAgain:
	.string "Until we meet again, amigo!$"

@ Unused
TrainerHill_Roof_Text_BuiltTrainerHillToFindPartner:
	.string "I had the BATTLE HILL built for but\n"
	.string "one reason and one only!\p"
	.string "To find the most suitable partner\n"
	.string "with whom I may form a tag team!$"

TrainerHill_Entrance_Text_ChallengeTime:
	.string "{STR_VAR_1} min. {STR_VAR_2}.{STR_VAR_3} sec.$"

TrainerHill_Entrance_Text_WhatSortOfTrainersAreAhead:
	.string "Who knows what sort of TRAINERS\n"
	.string "and POKéMON combos are ahead?\p"
	.string "All I know is that I'll knock aside\n"
	.string "anyone that stands in my way!$"

TrainerHill_Entrance_Text_CantWaitToTestTheWaters:
	.string "I heard tough TRAINERS come to this\n"
	.string "BATTLE HILL from all over.\p"
	.string "I can't wait to test the waters!\p"
	.string "I'll knock aside anyone that stands\n"
	.string "in my way!$"

TrainerHill_Entrance_Text_FriendsTryingToReachTimeBoardTop:
	.string "Do you see the Time Board over there?\p"
	.string "My friends and I are trying to see who\n"
	.string "can reach the top in the least time.$"

TrainerHill_Entrance_Text_DoYouKnowWhenTheyOpen:
	.string "Do you know when they're opening\n"
	.string "this place up?\p"
	.string "I'm waiting here to be the first\n"
	.string "challenger ever!$"

TrainerHill_Elevator_Text_ReturnToReception:
	.string "Would you like to return to\n"
	.string "the reception counter?$"

TrainerHill_Entrance_Text_WhichLevelMode:
	.string "The BATTLE HILL offers two levels\n"
	.string "of challenge, Level 50 and Open Level.\l"
	.string "Which is your choice?$"

TrainerHill_Entrance_Text_PartyLevelTooHigh50:
	.string "Excuse me!\p"
	.string "One or more of your POKéMON exceeds\n"
	.string "Level 50.\p"
	.string "All POKéMON in your party must be\n"
	.string "Level 50 or less to enter Level 50.\p"
	.string "Please come see me when you are ready.$"
