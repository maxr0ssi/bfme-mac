; Helper: send input to the game window. Usage (inside the prefix):
;   wine AutoHotkeyU32.exe send.ahk key {ESC}        ; send a key (AHK Send syntax)
;   wine AutoHotkeyU32.exe send.ahk click 756 900    ; click at screen point (x, y)
;   wine AutoHotkeyU32.exe send.ahk activate         ; just activate the game window
#NoTrayIcon
#SingleInstance Off
SetTitleMatchMode, 2
SendMode, Event
SetKeyDelay, 50, 50
SetMouseDelay, 50
CoordMode, Mouse, Screen
title := "Rise of the Witch-king"
WinWait, %title%,, 30
if ErrorLevel
{
    FileAppend, no window`n, *
    ExitApp, 2
}
WinActivate, %title%
WinWaitActive, %title%,, 5
Sleep, 300
cmd = %1%
if (cmd = "key")
{
    Send, %2%
}
else if (cmd = "click")
{
    MouseMove, %2%, %3%, 0
    Sleep, 200
    Click, %2%, %3%
}
else if (cmd = "move")
{
    MouseMove, %2%, %3%, 0
}
Sleep, 200
ExitApp
