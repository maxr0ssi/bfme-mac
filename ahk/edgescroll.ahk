; edgescroll.ahk - borderless window + emulated screen-edge camera scrolling for BFME2/RotWK.
; AutoHotkey 1.1.37.02 (ahk/AutoHotkeyU32.exe, 32-bit Unicode) running inside the Wine prefix:
;     cd ahk && wine AutoHotkeyU32.exe edgescroll.ahk [margin]
;
; This is a superset of borderless.ahk: it does the same borderless/pin-to-(0,0) setup and then
; STAYS RESIDENT. The play scripts launch this one script instead of borderless.ahk, because
; starting a second Wine process during the game's first seconds has crashed the game
; (see the note in scripts/test-skirmish.sh); one AutoHotkey process does both jobs.
; borderless.ahk is kept for one-shot/diagnostic use.
;
; Why: the SAGE engine disables edge scrolling in windowed mode (-win), the only mode usable
; under Wine's Mac driver. The camera still responds to the arrow keys, so while the cursor sits
; within `margin` points of the game window's edge we simply hold the matching arrow key(s) down;
; a corner holds two. The engine reads the mouse through Win32 messages and the keyboard through
; DirectInput, and both SendInput and keybd_event feed Wine's input queue, so held keys arrive.
;
; Toggle: Ctrl+Alt+E (Control+Option+E on a Mac keyboard), or Scroll Lock on a PC keyboard.
;   Neither is bound by BFME2/RotWK (the game uses bare letters, Ctrl+digit for control groups,
;   and the F-keys; it has no Ctrl+Alt combinations). Mac keyboards have no Scroll Lock, which is
;   why the primary binding is Ctrl+Alt+E. The hotkeys only fire while the game window is active.
; Rescue: Ctrl+Alt+R forces the game window back to the foreground - the manual half of the
;   Cmd-Tab mouse-death workaround (Sikarugir #237, see README "Mouse after Cmd-Tab").

#NoTrayIcon
#SingleInstance Force
SetTitleMatchMode, 2
SetBatchLines, -1          ; no artificial throttle; the Sleep below is what keeps CPU near zero
SetKeyDelay, -1, -1        ; no delay between key events (ignored by SendInput, used if Event)
SendMode, Input            ; SendInput. If keys ever stop reaching the game under Wine, try Event.
CoordMode, Mouse, Screen
CoordMode, ToolTip, Screen
SetWinDelay, -1

; Super-globals [v1.1.05+]: a bare `global` outside any function makes these visible in every
; function below. Declared bare and assigned separately, which is valid in every 1.1 build.
global margin, poll, enabled, held, hwnd, recaptureOnActivate
margin  := 4               ; how close to the edge (in window points) counts as "at the edge"
poll    := 30              ; ms between cursor samples
enabled := true            ; edge scrolling on/off, flipped by the hotkey
held    := {"Up": false, "Down": false, "Left": false, "Right": false}
hwnd    := 0

; Problem B (Sikarugir #237): after Cmd-Tab the 3D view can stop taking mouse input, because
; wine-10.0's macdrv_app_deactivated() drops the cursor clip and hands the foreground to the
; desktop window, while macdrv_app_activated() restores neither - recovery depends on a
; WINDOW_GOT_FOCUS / WM_MOUSEACTIVATE round-trip that the busy 3D window can miss. Set this to
; true to run Recapture() automatically whenever the window regains focus. Off by default: it is
; a guess, and Ctrl+Alt+R does the same thing on demand. See README "Mouse after Cmd-Tab".
recaptureOnActivate := false

; Command line: [on|off] [margin] [input|event|play]. "off" starts with edge scrolling disabled (the
; skirmish harness passes it, because a parked cursor at a screen edge would hold arrow keys down
; while it drives the menus); Ctrl+Alt+E still toggles. The third argument picks how keys are
; injected: SendInput (default), SendEvent, or SendPlay - if the game ignores one, try the next.
; Legacy %1% syntax, as in the other scripts here. Everything is logged to edgescroll.log next to
; this script (cursor/window geometry every 5 s, every key change), so a failed session is
; diagnosable afterwards.
arg1 = %1%
arg2 = %2%
arg3 = %3%
if (arg1 = "off")
    enabled := false
if (arg2 != "")
    margin := arg2 + 0
if (arg3 = "event")
    SendMode, Event
else if (arg3 = "play")
    SendMode, Play
global sendmode
sendmode := (arg3 != "") ? arg3 : "input"

; --- borderless: same as borderless.ahk ----------------------------------------------------
WinWait, The Lord of the Rings,, 120
if ErrorLevel
    ExitApp
Sleep, 500
WinGet, hwnd, ID, The Lord of the Rings
; strip WS_CAPTION (0xC00000), WS_THICKFRAME (0x40000), WS_SYSMENU (0x80000); drop WS_EX_DLGMODALFRAME etc.
WinSet, Style, -0xCC0000, ahk_id %hwnd%
WinSet, ExStyle, -0x201, ahk_id %hwnd%
WinMove, ahk_id %hwnd%,, 0, 0, %A_ScreenWidth%, %A_ScreenHeight%
WinActivate, ahk_id %hwnd%
OnExit("ReleaseAllOnExit")
WinGetPos, wx0, wy0, ww0, wh0, ahk_id %hwnd%
Log("resident, edge scrolling " . (enabled ? "on" : "off") . ", margin=" . margin . "px, sendmode=" . sendmode
    . ", hwnd=" . hwnd . ", window " . wx0 . "," . wy0 . " " . ww0 . "x" . wh0 . ", screen " . A_ScreenWidth . "x" . A_ScreenHeight
    . ", toggle Ctrl+Alt+E, rescue Ctrl+Alt+R")
SetTimer, Heartbeat, 5000

; --- edge scrolling loop -------------------------------------------------------------------
wasActive := false
Loop
{
    if (!WinActive("ahk_id " hwnd))
    {
        ReleaseAll()
        wasActive := false
        Sleep, 150                       ; idle slowly while another app has focus
        if (!WinExist("ahk_id " hwnd))   ; game gone -> so are we
            ExitApp
        continue
    }
    if (!wasActive)
    {
        wasActive := true
        if (recaptureOnActivate)
            Recapture()
    }
    ; Never fight the camera: right-drag rotates/pans, left-drag box-selects.
    if (!enabled or GetKeyState("LButton", "P") or GetKeyState("RButton", "P") or GetKeyState("MButton", "P"))
    {
        ReleaseAll()
        Sleep, %poll%
        continue
    }
    ; Use the window's own rectangle, not the screen, so the offsets are right on any monitor.
    WinGetPos, wx, wy, ww, wh, ahk_id %hwnd%
    MouseGetPos, mx, my
    if (mx < wx or mx >= wx + ww or my < wy or my >= wy + wh)   ; cursor left the window
    {
        ReleaseAll()
        Sleep, %poll%
        continue
    }
    Hold("Left",  mx - wx < margin)
    Hold("Right", (wx + ww - 1) - mx < margin)
    Hold("Up",    my - wy < margin)
    Hold("Down",  (wy + wh - 1) - my < margin)
    Sleep, %poll%
}

; --- hotkeys (only while the game window is focused) ----------------------------------------
#If WinActive("ahk_id " hwnd)
^!e::
ScrollLock::
    enabled := !enabled
    if (!enabled)
        ReleaseAll()
    Notify("edge scrolling " . (enabled ? "ON" : "OFF"))
return
#If
; Deliberately NOT guarded by #If: when #237 bites, Wine's foreground window is the desktop, so
; WinActive() on the game is false and a guarded hotkey could never fire.
^!r::
    Recapture()
    Notify("forced focus back to the game window")
return

; --- helpers --------------------------------------------------------------------------------
Hold(key, want) {
    global held
    if (held[key] = want)                ; only send on a change, never every poll
        return
    ; {Blind}: do not let AHK lift a modifier the player is physically holding (Ctrl+click etc.)
    Send, % "{Blind}{" . key . (want ? " down}" : " up}")
    held[key] := want
    Log("key " . key . (want ? " down" : " up"))
}

ReleaseAll() {
    global held
    for key, isDown in held
        if (isDown)
        {
            Send, % "{Blind}{" . key . " up}"
            held[key] := false
        }
}

ReleaseAllOnExit(ExitReason := "", ExitCode := "") {   ; OnExit passes two args; accept them
    ReleaseAll()                          ; never leave an arrow key stuck down
}

; Sikarugir #237 rescue. Three steps, in the order the driver skipped them:
;   1. drop any stale cursor clip (macdrv_app_deactivated already called NtUserClipCursor(NULL),
;      but the Cocoa side can have re-engaged confinement on its own);
;   2. do the NtUserSetForegroundWindow that macdrv_app_activated() never does - we are a separate
;      Wine process in the same prefix, so our SetForegroundWindow reaches the game's thread;
;   3. nudge the cursor through the driver so it re-syncs its warp state and the game gets a move.
Recapture() {
    global hwnd
    DllCall("ClipCursor", "Ptr", 0)
    WinActivate, ahk_id %hwnd%
    DllCall("SetForegroundWindow", "Ptr", hwnd)
    MouseGetPos, cx, cy
    DllCall("SetCursorPos", "Int", cx + 1, "Int", cy)
    DllCall("SetCursorPos", "Int", cx, "Int", cy)
    Log("re-capture: cleared clip, forced foreground, nudged cursor")
}

Notify(msg) {
    ToolTip, %msg%, 20, 20
    SetTimer, ClearTip, -1200
    Log(msg)
}

Log(msg) {
    FileAppend, % A_Hour ":" A_Min ":" A_Sec " edgescroll: " msg "`n", *
    FileAppend, % A_Hour ":" A_Min ":" A_Sec " " msg "`n", %A_ScriptDir%\edgescroll.log
}

Heartbeat:
    WinGetPos, hx, hy, hw, hh, ahk_id %hwnd%
    MouseGetPos, hmx, hmy
    Log("hb active=" . (WinActive("ahk_id " hwnd) ? 1 : 0) . " enabled=" . (enabled ? 1 : 0)
        . " mouse=" . hmx . "," . hmy . " win=" . hx . "," . hy . " " . hw . "x" . hh
        . " held=" . (held["Left"] ? "L" : "") . (held["Right"] ? "R" : "") . (held["Up"] ? "U" : "") . (held["Down"] ? "D" : "")
        . " lb=" . (GetKeyState("LButton", "P") ? 1 : 0) . " rb=" . (GetKeyState("RButton", "P") ? 1 : 0))
return

ClearTip:
    ToolTip
return
