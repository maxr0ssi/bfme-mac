; seq.ahk x1 y1 x2 y2 ... : activate the game window and click the points in order, 600 ms apart
#NoTrayIcon
SetTitleMatchMode, 2
CoordMode, Mouse, Screen
SetMouseDelay, 30
WinActivate, Rise of the Witch-king
WinWaitActive, Rise of the Witch-king,, 5
Sleep, 200
Loop, %0%
{
    i := A_Index
    if (Mod(i, 2) = 0)
        continue
    x := %i%
    j := i + 1
    y := %j%
    MouseMove, %x%, %y%, 0
    Sleep, 150
    Click, %x%, %y%
    Sleep, 600
}
ExitApp
