; NOTE: the play scripts no longer run this; they run edgescroll.ahk, which does exactly this
; and then stays resident for emulated screen-edge scrolling. Kept for one-shot/diagnostic use.
; Make the BFME window borderless and pin it to the top-left of the screen so that, at the
; screen's native point size, it behaves like fullscreen without exclusive mode.
; Run inside the prefix: wine AutoHotkeyU32.exe borderless.ahk  (after the game window exists)
#NoTrayIcon
#SingleInstance Force
SetTitleMatchMode, 2
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
ExitApp
