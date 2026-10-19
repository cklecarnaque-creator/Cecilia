"""
main.py
Runs the MysteryGadget engine simulation: starts it, controls it for
approximately ten seconds, and stops it.
"""

import time
from Displays import LCDDisplay
from Buzzer import PassiveBuzzer
from LightStrip import LightStrip
from Sensors import AnalogSensor
from MysteryGadget import MysteryGadget

def main():
    # 1. Initialize hardware components with standard Raspberry Pi Pico pins
    # LCD Display connected via I2C (SDA=GP0, SCL=GP1)
    lcd = LCDDisplay(sda=0, scl=1)

    # Passive Buzzer connected to PWM on GP15
    buzzer = PassiveBuzzer(pin=16, name="EngineBuzzer")

    # Neopixel LightStrip connected to GP2 (8 LEDs)
    strip = LightStrip(pin=2, name="Tachometer", numleds=8, brightness=0.5)

    # Potentiometer connected to ADC0 on GP26
    pot = AnalogSensor(pin=26, name="ThrottlePot")

    # 2. Create an instance of MysteryGadget
    gadget = MysteryGadget(
        display=lcd,
        buzzer=buzzer,
        light_strip=strip,
        potentiometer=pot
    )

    try:
        # 3. Start the gadget (simulates engine start sequence)
        print("Starting MysteryGadget...")
        gadget.start()

        # 4. Control it for about ten seconds (reads potentiometer & updates telemetry)
        print("Controlling MysteryGadget for ~10 seconds (adjust potentiometer)...")
        start_time = time.time()
        while time.time() - start_time < 10:
            gadget.control(continuous=False)
            time.sleep(0.1)

    finally:
        # 5. Stop the gadget (turns off sounds and LEDs, shows 'Engine Stopped')
        print("Stopping MysteryGadget...")
        gadget.stop()
        print("Engine stopped. Demonstration complete.")

if __name__ == "__main__":
    main()
