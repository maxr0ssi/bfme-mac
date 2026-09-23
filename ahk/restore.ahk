#NoTrayIcon
SetTitleMatchMode, 2
WinGet, hwnd, ID, Rise of the Witch-king
WinGet, st, MinMax, ahk_id %hwnd%
FileAppend, minmax=%st%`n, *
WinRestore, ahk_id %hwnd%
WinShow, ahk_id %hwnd%
WinMove, ahk_id %hwnd%,, 0, 0, %A_ScreenWidth%, %A_ScreenHeight%
WinActivate, ahk_id %hwnd%
ExitApp
