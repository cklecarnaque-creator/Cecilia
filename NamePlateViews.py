"""
# NamePlateViews.py
# View classes for the Dynamic NamePlate. Each view wraps one piece of
# hardware from PicoLibrary: NamePlateView (LCD), StatusLight (LightStrip)
# and SoundEffects (PassiveBuzzer).
# Author: Cecilia
"""

import time
from Log import *
from Lights import GREEN, YELLOW, RED, BLACK


class NamePlateView:
    """
    **NamePlateView** - shows text on the 16x2 LCD.

    Parameters:
    ----------
    lcd : LCDDisplay
        The PicoLibrary LCD display

    Examples:
    ---------
    1. view.showEmployee("Dr. Sengupta", "Professor")
    """

    def __init__(self, lcd):
        self._lcd = lcd

    def showEmployee(self, top, bottom):
        """ Shows the name on row 0 and one info page on row 1 """
        self._lcd.showText(self._fit(top), 0, 0)
        self._lcd.showText(self._fit(bottom), 1, 0)

    def showMessage(self, text):
        """ Shows a centered message on row 0 and clears row 1 """
        self._lcd.showText(self._fit(text.center(16)), 0, 0)
        self._lcd.showText(" " * 16, 1, 0)

    def clear(self):
        self._lcd.clear()

    def _fit(self, text):
        """ Cuts or pads text so it is exactly 16 characters """
        return (text + " " * 16)[:16]


class StatusLight:
    """
    **StatusLight** - colors the LightStrip like Teams:
    green = Available, yellow = Away, red = Busy.

    Parameters:
    ----------
    strip : LightStrip
        The PicoLibrary NeoPixel strip
    """

    COLORS = {"Available": GREEN, "Away": YELLOW, "Busy": RED}

    def __init__(self, strip):
        self._strip = strip

    def showStatus(self, status):
        """ Lights the whole strip with the color of the status """
        self._strip.setColor(StatusLight.COLORS.get(status, BLACK))


class SoundEffects:
    """
    **SoundEffects** - short sounds for the nameplate.
    Rising tones for "next", falling tones for "previous".

    Parameters:
    ----------
    buzzer : PassiveBuzzer
        The PicoLibrary passive buzzer
    """

    def __init__(self, buzzer):
        self._buzzer = buzzer

    def playNext(self):
        self._melody([523, 784])         # C5 -> G5 (going up)

    def playPrevious(self):
        self._melody([784, 523])         # G5 -> C5 (going down)

    def playStatusChange(self):
        self._melody([659, 659, 880])    # little "ding-ding-ding"

    def _melody(self, tones):
        for t in tones:
            self._buzzer.play(t)
            time.sleep(0.07)
        self._buzzer.stop()


if __name__ == "__main__":
    from Displays import LCDDisplay
    from LightStrip import LightStrip
    from Buzzer import PassiveBuzzer
    view = NamePlateView(LCDDisplay(sda=0, scl=1))
    view.showEmployee("View test", "Line 2")
    StatusLight(LightStrip(pin=2, numleds=8)).showStatus("Busy")
    SoundEffects(PassiveBuzzer(16)).playNext()
    Log.i("Testing complete - NamePlateViews.py")
