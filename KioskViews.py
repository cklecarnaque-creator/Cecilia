"""
# KioskViews.py
# View classes for the Satisfaction Kiosk. Each view wraps one or more
# pieces of PicoLibrary hardware so the controller never talks to the
# hardware directly:
#   KioskDisplay  -> LCDDisplay   (text, faces and a satisfaction bar)
#   KioskLights   -> LightStrip   (rainbow attract mode, gauge, alert)
#   KioskSounds   -> PassiveBuzzer (short sounds at the kiosk)
#   ManagerAlarm  -> PassiveBuzzer + Light (alarm beeps and LED in the office)
# Author: Cecilia Karina Lecarnaque Mendoza (PantherID 6685036)
"""

import time
from Log import *
from Lights import GREEN, YELLOW, RED, BLUE, BLACK

# Custom LCD characters (made with https://maxpromer.github.io/LCD-Character-Creator/)
SMILE = chr(1)
SAD = chr(2)
BLOCK = chr(3)
SMILE_SHAPE = [0x00, 0x0A, 0x0A, 0x00, 0x11, 0x0E, 0x00, 0x00]
SAD_SHAPE = [0x00, 0x0A, 0x0A, 0x00, 0x0E, 0x11, 0x00, 0x00]
BLOCK_SHAPE = [0x1F, 0x1F, 0x1F, 0x1F, 0x1F, 0x1F, 0x1F, 0x1F]


class KioskDisplay:
    """
    **KioskDisplay** - shows messages on the 16x2 LCD.

    Button events arrive through an interrupt, so writing to the LCD from
    them could collide with the main loop. To avoid that, show() only
    REMEMBERS the two lines, and refresh() (called from the main loop in
    stateDo) actually writes them. Same idea as the pending action in
    Mini-Lab 2.

    Parameters:
    ----------
    lcd : LCDDisplay
        The PicoLibrary LCD display

    Examples:
    ---------
    1. view.show("Rate your visit", "Green or Red")
    2. view.show("How was your", "visit?  {}s", deadline)   # countdown
    3. view.refresh()      # from the main loop
    """

    def __init__(self, lcd):
        self._lcd = lcd
        self._screen = ("", "", None)     # (top, bottom, countdown deadline)
        self._shown = [None, None]
        lcd.addShape(1, SMILE_SHAPE)
        lcd.addShape(2, SAD_SHAPE)
        lcd.addShape(3, BLOCK_SHAPE)

    def show(self, top, bottom="", deadline=None):
        """
        Asks for two lines to be displayed (written on next refresh).
        If deadline (a time.ticks_ms() value) is given, the bottom line is a
        template with {} that refresh() fills with the seconds left.
        The whole screen is replaced in ONE assignment, so a button
        interrupt can never mix an old line with a new one.
        """
        self._screen = (top, bottom, deadline)

    def refresh(self):
        """ Writes any line that changed. Call only from the main loop. """
        top, bottom, deadline = self._screen    # read once: safe from interrupts
        if deadline is not None:
            left = max(0, (time.ticks_diff(deadline, time.ticks_ms()) + 999) // 1000)
            bottom = bottom.format(left)
        lines = (self._fit(top), self._fit(bottom))
        for row in (0, 1):
            if lines[row] != self._shown[row]:
                self._lcd.showText(lines[row], row, 0)
                self._shown[row] = lines[row]

    @staticmethod
    def bar(percentage, cells=10):
        """ Text bar like  '######----'  using the full-block character """
        filled = round(percentage * cells / 100)
        return BLOCK * filled + "-" * (cells - filled)

    def _fit(self, text):
        """ Cuts or pads text so it is exactly 16 characters """
        return (text + " " * 16)[:16]


class KioskLights:
    """
    **KioskLights** - the LightStrip (NeoPixel ring) of the kiosk.

    - Idle: slow rainbow "attract mode" to catch people's attention
    - Voting: a satisfaction gauge (more LEDs = happier customers),
      green >= 60%, yellow >= threshold, red below threshold
    - Alarm: flashing red

    Parameters:
    ----------
    strip : LightStrip
        The PicoLibrary NeoPixel strip
    numleds : int
        Number of LEDs in the strip
    """

    def __init__(self, strip, numleds):
        self._strip = strip
        self._numleds = numleds
        self._offset = 0
        self._flashOn = False

    def rainbowStep(self):
        """ Moves the rainbow one step. Called repeatedly from stateDo """
        self._offset = (self._offset + 8) % 256
        for i in range(self._numleds):
            color = self._strip.wheel((i * 256 // self._numleds + self._offset) & 255)
            self._strip.setPixel(i, color, show=False)
        self._strip.show()

    def showGauge(self, stats):
        """ Lights as many LEDs as the satisfaction level """
        pct = stats.calculate_percentage()
        if stats.get_total_count() == 0:
            self._strip.setColor(BLUE)          # no votes yet: calm blue
            return
        if pct >= 60:
            color = GREEN
        elif pct >= stats.get_threshold():
            color = YELLOW
        else:
            color = RED
        self._strip.setColor(color, max(1, stats.get_light_level(self._numleds)))

    def flashRed(self):
        """ Toggles red / off. Called repeatedly from stateDo """
        self._flashOn = not self._flashOn
        self._strip.setColor(RED if self._flashOn else BLACK)

    def off(self):
        self._strip.setColor(BLACK)


class KioskSounds:
    """
    **KioskSounds** - short sounds played by the buzzer at the kiosk.

    Parameters:
    ----------
    buzzer : PassiveBuzzer
        The PicoLibrary passive buzzer inside the kiosk
    """

    def __init__(self, buzzer):
        self._buzzer = buzzer
        if hasattr(buzzer, "setVolume"):   # PassiveBuzzer only
            buzzer.setVolume(1.0)          # loudest (50% duty cycle)

    def playWelcome(self):
        self._melody([2349, 2794], 0.08)           # "ding-ding" someone arrived

    def playHappy(self):
        self._melody([2093, 2349, 2637, 2794], 0.09)  # going up = happy

    def playSad(self):
        self._melody([2637, 2349, 2093], 0.15)      # slow, going down = sad

    def playReset(self):
        self._melody([2794, 2349, 2794], 0.1)

    def _melody(self, tones, delay):
        for t in tones:
            self._buzzer.play(t)
            time.sleep(delay)
        self._buzzer.stop()


class ManagerAlarm:
    """
    **ManagerAlarm** - the alarm panel in the manager's office: a passive
    buzzer (alarm beeps) and a red LED. The beeps get MORE URGENT the longer
    nobody presses the manager's button.

    Parameters:
    ----------
    buzzer : PassiveBuzzer
        The buzzer in the manager's office
    led : Light
        The red LED in the manager's office

    Examples:
    ---------
    1. alarm.start()
    2. alarm.sirenStep()   # repeatedly, from stateDo
    3. alarm.clear()
    """

    def __init__(self, buzzer, led):
        self._buzzer = buzzer
        self._led = led
        self._startTime = 0
        self._tick = 0
        self._high = False

    def start(self):
        self._startTime = time.ticks_ms()
        self._tick = 0
        Log.d("ManagerAlarm: alarm ON")

    def sirenStep(self):
        """
        One step of the alarm. Called every loop of the model (~0.1 s).
        Beeps at 2.7 kHz, the buzzer's natural frequency, so it is as loud
        as possible. The beeps get faster the longer nobody answers:
        0-5 s: slow, 5-10 s: faster, after 10 s: very fast.
        """
        elapsed = time.ticks_diff(time.ticks_ms(), self._startTime) / 1000
        if elapsed < 5:
            every = 4
        elif elapsed < 10:
            every = 2
        else:
            every = 1
        if self._tick % every == 0:
            self._high = not self._high
            if self._high:
                if hasattr(self._buzzer, "setVolume"):
                    self._buzzer.setVolume(1.0)
                self._buzzer.play(2700)
            else:
                self._buzzer.stop()
            self._led.flip()
        self._tick += 1

    def clear(self):
        """ Everything back to normal """
        self._buzzer.stop()
        self._led.off()


if __name__ == "__main__":
    from Displays import LCDDisplay
    from LightStrip import LightStrip
    from Buzzer import PassiveBuzzer
    view = KioskDisplay(LCDDisplay(sda=0, scl=1))
    view.show("View test " + SMILE + SAD, KioskDisplay.bar(70))
    view.refresh()
    lights = KioskLights(LightStrip(pin=2, numleds=16), 16)
    for _ in range(30):
        lights.rainbowStep()
    KioskSounds(PassiveBuzzer(16)).playHappy()
    Log.i("Testing complete - KioskViews.py")
