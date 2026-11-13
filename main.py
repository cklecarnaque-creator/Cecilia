"""
# main.py  (same file for Wokwi and the real Pico 2 W)
# Starts the Satisfaction Kiosk: creates the hardware, the views, the
# statistics model and the controller, then runs the state model.
# Author: Cecilia Karina Lecarnaque Mendoza (PantherID 6685036)
"""

from Log import *
from Displays import LCDDisplay
from LightStrip import LightStrip
from Lights import Light
from Buzzer import PassiveBuzzer
from FeedbackController import SteadyUltrasonicSensor
from FeedbackStats import FeedbackStats
from KioskViews import KioskDisplay, KioskLights, KioskSounds, ManagerAlarm
from FeedbackController import FeedbackController

Log.level = DEBUG   # hide the very chatty INFO logs, keep state-model debug output

# ---- Pins (change here if your wiring is different) ----
NUM_LEDS = 8        # Freenove 8 RGB LED module
GREEN_PIN = 10      # HAPPY button
RED_PIN = 11        # UNHAPPY button
MANAGER_PIN = 12    # MANAGER button

# --- Hardware: the kiosk ---
lcd = LCDDisplay(sda=0, scl=1)
strip = LightStrip(pin=2, name="Kiosk ring", numleds=NUM_LEDS, brightness=0.3)
buzzer = PassiveBuzzer(16, "Buzzer")
sensor = SteadyUltrasonicSensor(trigger=15, echo=14, name="uss", threshold=10.0)

# --- Hardware: the manager's office ---
# Only one buzzer: the kiosk sounds and the office siren share it.
# The office LED is the Pico's own on-board LED.
officeLed = Light("LED", "Office LED")

# --- Views and model ---
display = KioskDisplay(lcd)
lights = KioskLights(strip, NUM_LEDS)
sounds = KioskSounds(buzzer)
alarm = ManagerAlarm(buzzer, officeLed)
stats = FeedbackStats(threshold=30, min_votes=3)

# --- Controller ---
kiosk = FeedbackController(display, lights, sounds, alarm, stats, sensor,
                           GREEN_PIN, RED_PIN, MANAGER_PIN)

try:
    kiosk.run()
except KeyboardInterrupt:
    kiosk.stop()
