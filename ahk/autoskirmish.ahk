; autoskirmish.ahk - hands-free: wait for the RotWK window, skip the intro movie, and click
; Solo Play -> Skirmish -> Play so the last-used skirmish (Argonath 2p, Isengard vs Easy Goblins)
; starts loading. Run inside the prefix:  cd ahk && wine AutoHotkeyU32.exe autoskirmish.ahk [mode]
;   mode = full   (default) wait for window, skip movie, wait for the main menu, click through
;   mode = clicks           the main menu is already showing: only do the three clicks
;   mode = skip             only press Esc twice (skip movie)
;
; Coordinates are screen points for the borderless 1512x982 window at (0,0) (see borderless.ahk),
; measured from screenshots (3024x1964 px capture / 2). The two games do NOT share a main menu:
; RotWK stacks its buttons vertically at the bottom left, BFME2 has one horizontal bar of six
; (Tutorials / Solo Play / Multiplayer / Options / My Heroes / Quit), so Solo Play sits further
; right. Both fly-outs open upwards, and both Play buttons are bottom-right.
;   RotWK  Solo Play (162, 907)   Skirmish (162, 630)   Play (1291, 940)
;   BFME2  Solo Play (410, 889)   Skirmish (410, 634)   Play (1333, 940)
; BFME2 also needs a player profile to exist: with none, Skirmish opens a modal "Add New Profile"
; dialog and nothing below it can be clicked. One was created by hand in prefixes/w10 ("Player").
; Timings seen: window appears ~8 s after launch, intro movie ~15 s after launch; after Esc the
; rune-ring splash shows for ~15 s, then the main menu. Nothing here reads pixels (the D3D window
; can't be sampled reliably from inside Wine); test-skirmish.sh verifies each stage with
; screencapture + classify-capture.py and re-runs "clicks" mode if a click did not land.
#NoTrayIcon
#SingleInstance Force
SetTitleMatchMode, 2
CoordMode, Mouse, Screen
SendMode, Event
SetKeyDelay, 60, 60
SetMouseDelay, 30

mode = %1%
if (mode = "")
    mode := "full"
game = %2%
if (game = "")
    game := "rotwk"
; optional timing overrides (ms): %3% = wait before the first Esc, %4% = wait for the main menu
; after Esc. Wine 11 stable: movie at ~+15 s, menu ~15 s after Esc. Wine 10 (w10 engine): the
; movie starts ~+35 s and the splash lasts ~50 s, so the harness passes 48000 / 55000 there.
preEsc = %3%
if (preEsc = "")
    preEsc := 6000
menuWait = %4%
if (menuWait = "")
    menuWait := 20000
; per-game window title substring and button coordinates (screen points)
if (game = "bfme2")
{
    title := "Battle for Middle-earth(tm) II"   ; BFME2 title has no "Witch-king" suffix
    soloX := 410,  soloY := 889                 ; 2nd button of the horizontal bar, not the corner
    skirX := 410,  skirY := 634                 ; top entry of the fly-out above it
    playX := 1333, playY := 940
}
else
{
    title := "Rise of the Witch-king"
    soloX := 162,  soloY := 907
    skirX := 162,  skirY := 630
    playX := 1291, playY := 940
}

; --- helpers -----------------------------------------------------------------------------
Activate(title) {
    WinActivate, %title%
    WinWaitActive, %title%,, 5
    Sleep, 200
}
ClickAt(x, y) {
    MouseMove, %x%, %y%, 0
    Sleep, 150
    Click, %x%, %y%
}
Log(msg) {
    FileAppend, % A_Hour ":" A_Min ":" A_Sec " autoskirmish: " msg "`n", *
}

; --- wait for the window -------------------------------------------------------------------
WinWait, %title%,, 120
if ErrorLevel
{
    Log("game window did not appear")
    ExitApp, 2
}
Log("window found, mode=" mode " game=" game " preEsc=" preEsc " menuWait=" menuWait)

if (mode = "full" or mode = "skip")
{
    ; Let the movie start (black frames first), then Esc twice. Esc is harmless on the splash
    ; and on the main menu, so this is tolerant of the movie already being gone.
    if (mode = "full")
        Sleep, %preEsc%  ; the harness starts us ~12 s after launch
    Activate(title)
    Send, {Esc}
    Sleep, 2500
    Activate(title)
    Send, {Esc}
    Log("sent Esc x2")
    if (mode = "skip")
        ExitApp, 0
    ; splash -> main menu. The intro does not reliably start by preEsc (BFME2 on the w10 engine
    ; was still playing it 2 min in, so the burst above landed before the movie), so keep tapping
    ; Esc through the first half of the wait instead of relying on that one burst. Esc is harmless
    ; on the splash and on the main menu, and the total elapsed time is unchanged.
    half := Floor(menuWait / 2)
    waited := 0
    while (waited < half)
    {
        Sleep, 6000
        waited += 6000
        Activate(title)
        Send, {Esc}
    }
    rest := menuWait - waited
    if (rest > 0)
        Sleep, %rest%
}

; --- main menu: Solo Play -> Skirmish -> Play ----------------------------------------------
Activate(title)
ClickAt(soloX, soloY)      ; Solo Play (fly-out opens above it)
Sleep, 700
ClickAt(skirX, skirY)      ; Skirmish
Log("clicked Solo Play + Skirmish")
Sleep, 3000                ; skirmish setup screen appears
Activate(title)
ClickAt(playX, playY)      ; Play
Log("clicked Play")
Sleep, 500
; park the cursor away from the buttons so hover state can't change anything
MouseMove, 756, 400, 0
ExitApp, 0
