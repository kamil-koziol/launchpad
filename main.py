from time import sleep
from launchpad_mini import LaunchpadMini

lp = LaunchpadMini()
lp.setup()

buttonPressed = 0
offset = 0
while True:
    lp.Reset()
    buttonPressed = lp.ButtonStateRaw()
    for x in range(3):
        for y in range(3):
            lp.LedCtrlXY(x + offset, y + offset, x, y)
    if buttonPressed:
        if buttonPressed[0] == 0 and buttonPressed[1]:
            # Green, Yellow, Orange, Red
            print(buttonPressed)
            pass
    offset += 1
    offset %= 8
    sleep(0.05)


lp.Reset()
lp.Close()
print(lp)
