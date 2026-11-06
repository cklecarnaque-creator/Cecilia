"""
# main.py
# Starts the Dynamic NamePlate: creates the hardware, the views, the
# employees and the controller, then runs it.
# Author: Cecilia
"""

from Displays import LCDDisplay
from LightStrip import LightStrip
from Buzzer import PassiveBuzzer
from Employees import Faculty, Staff, StudentWorker, Administrator, Calendar
from NamePlateViews import NamePlateView, StatusLight, SoundEffects
from NamePlate import NamePlate

# --- Hardware (same pins as Lab 1) ---
lcd = LCDDisplay(sda=0, scl=1)
strip = LightStrip(pin=2, name="Status", numleds=8, brightness=0.3)
buzzer = PassiveBuzzer(16)
buzzer.setVolume(1.0)                    # max volume

# --- Views ---
view = NamePlateView(lcd)
light = StatusLight(strip)
sound = SoundEffects(buzzer)

# --- Controller (buttons: prev=GP10, next=GP11, status=GP12) ---
plate = NamePlate(view, light, sound, 10, 11, 12)

# --- People ---
cal = Calendar()
cal.addBlock(9 * 60, 12 * 60, "Busy")     # meetings 9am-12pm
cal.addBlock(12 * 60, 13 * 60, "Away")    # lunch 12-1pm
cal.addBlock(15 * 60, 17 * 60, "Busy")    # meetings 3-5pm

plate.addEmployee(Faculty("Ms. Cecilia L", "305-348-0001", "Professor",
                          ["COP 4521", "CEN 4010"], "MW 2-4pm"))
plate.addEmployee(Administrator("Ms. Valerie W", "305-348-0002", "Director", cal))
plate.addEmployee(Staff("Mr. Louis T", "305-348-0003", "IT Support", "8am-5pm"))
plate.addEmployee(StudentWorker("Ms. Martina L", "305-348-0004", "Front Desk",
                                "IT", "V Winehouse"))

plate.run()
