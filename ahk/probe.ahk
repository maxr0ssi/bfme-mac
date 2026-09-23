; probe.ahk - extra input probes for mouse diagnosis (all coords are screen points)
;   probe.ahk rdrag x1 y1 x2 y2      right-button drag
;   probe.ahk ldrag x1 y1 x2 y2      left-button drag
;   probe.ahk rclick x y             right click
;   probe.ahk wheel up|down n x y    wheel n notches with cursor at x,y
;   probe.ahk hold x y ms            move cursor to x,y and keep it there ms (re-moving every 100 ms)
;   probe.ahk pos                    print current cursor pos + window under it
#NoTrayIcon
#SingleInstance Off
SetTitleMatchMode, 2
SendMode, Event
SetKeyDelay, 50, 50
SetMouseDelay, 50
CoordMode, Mouse, Screen
title := "Rise of the Witch-king"
WinActivate, %title%
WinWaitActive, %title%,, 5
Sleep, 300
cmd = %1%
if (cmd = "rdrag")
{
    MouseMove, %2%, %3%, 0
    Sleep, 200
    MouseClickDrag, Right, %2%, %3%, %4%, %5%, 20
}
else if (cmd = "ldrag")
{
    MouseMove, %2%, %3%, 0
    Sleep, 200
    MouseClickDrag, Left, %2%, %3%, %4%, %5%, 20
}
else if (cmd = "rclick")
{
    MouseMove, %2%, %3%, 0
    Sleep, 200
    Click, %2%, %3%, Right
}
else if (cmd = "wheel")
{
    MouseMove, %4%, %5%, 0
    Sleep, 300
    dir = %2%
    n = %3%
    if (dir = "up")
        Send, {WheelUp %n%}
    else
        Send, {WheelDown %n%}
}
else if (cmd = "hold")
{
    ms = %4%
    x = %2%
    y = %3%
    MouseMove, %x%, %y%, 0
    t := 0
    Loop
    {
        Sleep, 100
        MouseMove, %x%, %y%, 0
        t += 100
        if (t >= ms)
            break
    }
}
else if (cmd = "pos")
{
    MouseGetPos, mx, my, mwin
    WinGetTitle, mt, ahk_id %mwin%
    WinGetPos, wx, wy, ww, wh, %title%
    FileAppend, cursor=%mx%`,%my% under=%mt% gamewin=%wx%`,%wy% %ww%x%wh%`n, *
}
Sleep, 200
ExitApp
