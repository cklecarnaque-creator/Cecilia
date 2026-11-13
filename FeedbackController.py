"""
# FeedbackController.py
# Controller for the Satisfaction Kiosk. Follows the state model we built in
# class (Welcome, Selection, happy, unhappy, Alarm) using the PicoLibrary
# StateModel. The buttons, the ultrasonic sensor and the timer are added to
# the model, and this class performs the entry / exit / do actions.
# Author: Cecilia Karina Lecarnaque Mendoza (PantherID 6685036)
"""

import time
from Log import *
from StateModel import StateModel
from Counters import SoftwareTimer
from Button import Button
from Sensors_advanced import UltrasonicSensor
from machine import time_pulse_us
from KioskViews import SMILE, SAD, KioskDisplay

# ---- States (state 0 is always the start state in StateModel) ----
WELCOME = 0     # nobody near: "Welcome to Ikea", rainbow lights
SELECTION = 1   # someone is near: "How was your visit?"
HAPPY = 2       # green pressed: thank you + happy music
UNHAPPY = 3     # red pressed: sorry + sad tone
ALARM = 4       # feedback below threshold: alarm in the manager's office

STATE_NAMES = ("Welcome", "Selection", "Happy", "Unhappy", "Alarm")


class DebouncedButton(Button):
    """
    **DebouncedButton** - a PicoLibrary Button that ignores "bounce".

    A real push button does not make one clean contact: for a few
    milliseconds it bounces on/off many times. The original Button can
    then read a press as a release. This subclass waits 20 ms for the
    contact to settle, reads the button once, and only reports a press or
    a release when the state really changed.
    """

    def __init__(self, pin, name):
        super().__init__(pin, name, handler=None)
        self._wasPressed = False

    def _callback(self, pin):
        time.sleep_ms(20)                 # let the contact settle
        pressed = self.isPressed()
        if pressed == self._wasPressed:   # just bounce, nothing changed
            return
        self._wasPressed = pressed
        if self._handler is not None:
            if pressed:
                self._handler.buttonPressed(self._name)
            else:
                self._handler.buttonReleased(self._name)


class SteadyUltrasonicSensor(UltrasonicSensor):
    """
    **SteadyUltrasonicSensor** - a PicoLibrary UltrasonicSensor that is
    reliable with a real hand in front of it.

    - Sends the 10 us trigger pulse the HC-SR04 datasheet asks for.
    - Ignores failed readings (no echo) instead of treating them as "near".
    - Changes state only after 2 readings in a row agree, and uses a small
      margin (trip under threshold, untrip over threshold + 5 cm), so a
      shaky hand does not make it flicker between near and far.
    """

    def __init__(self, *, trigger, echo, name, threshold=10.0):
        super().__init__(trigger=trigger, echo=echo, name=name, threshold=threshold)
        self._near = False
        self._agree = 0

    def distance(self) -> float:
        """ Distance in cm, or -1 if there was no echo """
        self._trigger.off()
        time.sleep_us(2)
        self._trigger.on()
        time.sleep_us(10)                 # datasheet: at least 10 us
        self._trigger.off()
        us = time_pulse_us(self._echo, 1, 30000)
        if us < 0:
            return -1
        return round(us * 0.0343 / 2, 1)

    def tripped(self) -> bool:
        d = self.distance()
        if d <= 0:                        # bad reading: keep what we had
            return self._near
        limit = self._threshold + 5 if self._near else self._threshold
        nowNear = d < limit
        if nowNear != self._near:
            self._agree += 1
            if self._agree >= 2:          # two readings in a row agree
                self._near = nowNear
                self._agree = 0
        else:
            self._agree = 0
        return self._near


class FeedbackController:
    """
    **FeedbackController** - the controller of the Satisfaction Kiosk.

    Events (names are created by PicoLibrary):
    - uss_trip / uss_untrip      : UltrasonicSensor "uss" (< 10 cm / walked away)
    - green_press / red_press    : customer buttons
    - manager_press              : button in the manager's office
    - timer_timeout              : SoftwareTimer "timer"
    - feedback_below_threshold   : custom event, raised when FeedbackStats.is_low()

    Parameters:
    ----------
    display : KioskDisplay
    lights : KioskLights
    sounds : KioskSounds
    alarm : ManagerAlarm
    stats : FeedbackStats
    sensor : UltrasonicSensor   (must be named "uss")
    greenPin, redPin, managerPin : int
        GPIO pins of the three buttons

    Examples:
    ---------
    1. kiosk = FeedbackController(display, lights, sounds, alarm, stats, sensor, 10, 11, 12)
    2. kiosk.run()
    """

    SELECTION_SECONDS = 5   # time to vote before going back to Welcome
    MESSAGE_SECONDS = 5     # time the happy / unhappy message stays on

    def __init__(self, display, lights, sounds, alarm, stats, sensor,
                 greenPin, redPin, managerPin):
        self._display = display
        self._lights = lights
        self._sounds = sounds
        self._alarm = alarm
        self._stats = stats

        # The State Model: 5 states, this controller handles the actions
        self._model = StateModel(5, self, debug=True)

        # Buttons - the model becomes their handler (events: name_press / name_release)
        self._model.addButton(DebouncedButton(greenPin, "green"))
        self._model.addButton(DebouncedButton(redPin, "red"))
        self._model.addButton(DebouncedButton(managerPin, "manager"))

        # Ultrasonic sensor - polled by the model (events: uss_trip / uss_untrip)
        self._model.addSensor(sensor)

        # One software timer for every state that needs one (event: timer_timeout)
        self._timer = SoftwareTimer(name="timer", handler=None)
        self._model.addTimer(self._timer)

        # Custom event: the controller checks the condition and raises it
        self._model.addCustomEvent("feedback_below_threshold")

        # ---- Transitions (same as the class diagram) ----
        self._model.addTransition(WELCOME, ["uss_trip"], SELECTION)
        self._model.addTransition(SELECTION, ["green_press"], HAPPY)
        self._model.addTransition(SELECTION, ["red_press"], UNHAPPY)
        self._model.addTransition(SELECTION, ["timer_timeout", "uss_untrip"], WELCOME)
        self._model.addTransition(HAPPY, ["timer_timeout"], WELCOME)
        self._model.addTransition(UNHAPPY, ["timer_timeout"], WELCOME)
        self._model.addTransition(UNHAPPY, ["feedback_below_threshold"], ALARM)
        self._model.addTransition(ALARM, ["manager_press", "green_press"], WELCOME)

    # ------------------------------------------------------------------
    # Entry actions
    # ------------------------------------------------------------------
    def stateEntered(self, state, event):
        Log.d(f"Entered {STATE_NAMES[state]} on {event}")

        if state == WELCOME:
            self._display.show("Welcome to Ikea!", "Rate us " + SMILE)

        elif state == SELECTION:
            self._sounds.playWelcome()
            self._lights.showGauge(self._stats)
            seconds = FeedbackController.SELECTION_SECONDS
            deadline = time.ticks_add(time.ticks_ms(), seconds * 1000)
            # the {} is filled with the seconds left by KioskDisplay.refresh()
            self._display.show("How was your", "visit? " + SMILE + "/" + SAD + "   {}s", deadline)
            self._timer.start(seconds)

        elif state == HAPPY:
            self._stats.add_happy()
            self._sounds.playHappy()
            self._showVoteResult("Thank you! " + SMILE)

        elif state == UNHAPPY:
            self._stats.add_unhappy()
            self._sounds.playSad()
            self._showVoteResult("Sorry to hear " + SAD)

        elif state == ALARM:
            pct = self._stats.calculate_percentage()
            self._display.show("Calling manager", f"Score: {pct}%  !!")
            self._alarm.start()

    # ------------------------------------------------------------------
    # Exit actions
    # ------------------------------------------------------------------
    def stateLeft(self, state, event):
        Log.d(f"Left {STATE_NAMES[state]} on {event}")

        if state in (SELECTION, HAPPY, UNHAPPY):
            self._timer.cancel()

        elif state == ALARM:
            # exit / reset stats (as in the class diagram)
            self._stats.reset()
            self._alarm.clear()
            self._sounds.playReset()

    # ------------------------------------------------------------------
    # In-state events (none needed - every event is a transition)
    # ------------------------------------------------------------------
    def stateEvent(self, state, event) -> bool:
        return False

    # ------------------------------------------------------------------
    # Do activities - called by the model on every loop (~0.1 s)
    # ------------------------------------------------------------------
    def stateDo(self, state):
        if state == WELCOME:
            self._lights.rainbowStep()

        elif state == UNHAPPY:
            # Guard of the UNHAPPY -> ALARM transition
            if self._stats.is_low():
                self._model.processEvent("feedback_below_threshold")

        elif state == ALARM:
            self._alarm.sirenStep()      # do / play the alarm beeps
            self._lights.flashRed()

        # The LCD is only written here, from the main loop (also runs the countdown)
        self._display.refresh()

    # ------------------------------------------------------------------
    def _showVoteResult(self, top):
        """ Shared entry actions of HAPPY and UNHAPPY """
        pct = self._stats.calculate_percentage()
        self._display.show(top, f"{pct:3d}% " + KioskDisplay.bar(pct))
        self._lights.showGauge(self._stats)
        self._timer.start(FeedbackController.MESSAGE_SECONDS)

    def run(self):
        """ Starts the state model (begins in WELCOME) """
        self._display.show("Satisfaction", "Kiosk starting")
        self._display.refresh()
        time.sleep(1)
        self._model.run()

    def stop(self):
        self._model.stop()
        self._lights.off()
        self._alarm.clear()


if __name__ == "__main__":
    Log.i("Run main.py to start the Satisfaction Kiosk")
