"""
# MysteryGadget.py
# An engine simulation gadget implemented in MicroPython for Raspberry Pi Pico.
# Uses an LCD Display, Passive Buzzer, Neopixel LightStrip, and Potentiometer.
# Author: Generated for Pair Programming Task
"""

import time
from Log import Log
from Lights import BLACK, GREEN, YELLOW, RED, ORANGE

class MysteryGadget:
    """
    MysteryGadget simulates an automotive engine with realistic sounds,
    tachometer light visualizations, and live RPM/Speed telemetry.

    Components:
    -----------
    display: LCDDisplay
        1602 LCD display to output telemetry (RPM, Speed, and status).
    buzzer: PassiveBuzzer
        PWM buzzer to produce engine cranking, idle rumble, and rev sounds.
    light_strip: LightStrip
        Neopixel strip acting as an LED tachometer / RPM gauge.
    potentiometer: AnalogSensor or ADC
        Analog input used as the accelerator pedal / throttle control.
    """

    IDLE_RPM = 800
    MAX_RPM = 7000
    MAX_SPEED = 140  # In mph (or km/h)

    def __init__(self, display, buzzer, light_strip, potentiometer):
        """
        Initialize the Mystery Gadget with the required peripherals.
        """
        self._display = display
        self._buzzer = buzzer
        self._light_strip = light_strip
        self._potentiometer = potentiometer
        self._running = False
        Log.i("MysteryGadget initialized")

    def start(self):
        """
        Simulate starting the engine.
        Produces low-frequency cranking/rumble sounds on the buzzer, sets
        the engine to idle, and displays initial RPM and speed on the LCD.
        """
        Log.i("MysteryGadget: Starting engine...")

        # 1. Cranking animation on display
        self._display.clear()
        self._display.showText("Starting Engine".center(16), row=0, col=0)
        self._display.showText("Cranking...".center(16), row=1, col=0)

        # 2. Low-frequency engine cranking sound sequence
        crank_frequencies = [45, 60, 75, 90]
        for freq in crank_frequencies:
            self._buzzer.play(freq)
            time.sleep(0.12)
            self._buzzer.stop()
            time.sleep(0.06)

        # 3. Engine catches and begins idling
        self._running = True
        self._buzzer.play(70)  # Low-frequency rumble for engine idle (~70 Hz)

        # 4. Display idle speed and RPM
        self._display.clear()
        self._display.showText(f"RPM: {self.IDLE_RPM}".ljust(16), row=0, col=0)
        self._display.showText("Speed: 0 mph".ljust(16), row=1, col=0)

        # 5. Idle indicator on light strip (single dim green pixel)
        num_leds = getattr(self._light_strip, "_numleds", 8)
        for i in range(num_leds):
            self._light_strip.setPixel(i, BLACK, show=False)
        self._light_strip.setPixel(0, (0, 80, 0), show=False)
        self._light_strip.show()

        Log.i("MysteryGadget: Engine is now idling.")

    def stop(self):
        """
        Stop the engine.
        Shows 'Engine Stopped' on the display, stops all buzzer sound,
        and turns off the Neopixel strip.
        """
        Log.i("MysteryGadget: Stopping engine...")
        self._running = False

        # 1. Stop buzzer sound
        self._buzzer.stop()

        # 2. Turn off light strip
        self._light_strip.off()

        # 3. Update display
        self._display.clear()
        self._display.showText("Engine Stopped".center(16), row=0, col=0)
        self._display.showText("".ljust(16), row=1, col=0)

        Log.i("MysteryGadget: Engine stopped.")

    def control(self, continuous=True, interval_ms=100):
        """
        Monitor the potentiometer and use its raw value to simulate increasing
        and decreasing engine RPM and speed. Visualizes RPM on the light strip
        and shows live numbers on the LCD display.

        Parameters:
        -----------
        continuous: bool
            If True, runs a continuous monitoring loop until stopped or interrupted.
            If False, executes a single monitoring and update step.
        interval_ms: int
            Polling interval in milliseconds when running in continuous mode.
        """
        if not self._running:
            Log.w("MysteryGadget: Engine is stopped. Call start() before control().")
            return

        if not continuous:
            self._update_engine_state()
            return

        Log.i("MysteryGadget: Entering continuous control mode...")
        try:
            while self._running:
                self._update_engine_state()
                time.sleep(interval_ms / 1000.0)
        except KeyboardInterrupt:
            Log.i("MysteryGadget: Control loop interrupted by user.")
            self.stop()

    def _get_pot_value(self):
        """
        Helper to read raw 16-bit value from potentiometer (range: 0 to 65535).
        Supports AnalogSensor (rawValue), machine.ADC (read_u16), or callables.
        """
        if hasattr(self._potentiometer, "rawValue"):
            return self._potentiometer.rawValue()
        elif hasattr(self._potentiometer, "read_u16"):
            return self._potentiometer.read_u16()
        elif callable(self._potentiometer):
            return self._potentiometer()
        return 0

    def _update_engine_state(self):
        """
        Reads the potentiometer, calculates RPM and speed, and updates
        the buzzer sound frequency, light strip tachometer, and LCD display.
        """
        raw_val = self._get_pot_value()
        # Normalize raw value (0 to 65535) to ratio [0.0, 1.0]
        ratio = max(0.0, min(1.0, raw_val / 65535.0))

        # 1. Calculate RPM and Speed
        rpm = int(self.IDLE_RPM + ratio * (self.MAX_RPM - self.IDLE_RPM))
        speed = int(ratio * self.MAX_SPEED)

        # 2. Update LCD Display with RPM and Speed
        self._display.showText(f"RPM: {rpm}".ljust(16), row=0, col=0)
        self._display.showText(f"Speed: {speed} mph".ljust(16), row=1, col=0)

        # 3. Update Buzzer pitch based on RPM (engine rev sound: 60Hz - 360Hz)
        sound_freq = int(60 + ratio * 300)
        self._buzzer.play(sound_freq)

        # 4. Update LightStrip Tachometer visualization
        self._update_tachometer(ratio)

    def _update_tachometer(self, ratio):
        """
        Visualizes the engine RPM as a tachometer bar graph on the Neopixel strip.
        - Low RPM: Green
        - Mid RPM: Amber/Yellow
        - Redline / High RPM: Red
        """
        num_leds = getattr(self._light_strip, "_numleds", 8)
        lit_leds = int(round(ratio * num_leds))

        for i in range(num_leds):
            if i < lit_leds:
                # Color based on gauge position
                pos = i / max(1, num_leds - 1)
                if pos < 0.6:
                    color = GREEN
                elif pos < 0.85:
                    color = ORANGE
                else:
                    color = RED
                self._light_strip.setPixel(i, color, show=False)
            else:
                self._light_strip.setPixel(i, BLACK, show=False)

        # If idling (0 LEDs lit by throttle), keep first LED dimly lit green
        if lit_leds == 0:
            self._light_strip.setPixel(0, (0, 60, 0), show=False)

        self._light_strip.show()


# Example usage when running MysteryGadget directly
if __name__ == "__main__":
    from Displays import LCDDisplay
    from Buzzer import PassiveBuzzer
    from LightStrip import LightStrip
    from Sensors import AnalogSensor

    print("Initializing MysteryGadget components...")
    # Adjust GPIO pins according to your Raspberry Pi Pico wiring:
    # LCD on I2C pins (sda=0, scl=1)
    lcd = LCDDisplay(sda=0, scl=1)

    # Passive Buzzer on GPIO 15
    buzzer = PassiveBuzzer(pin=15, name="EngineBuzzer")

    # LightStrip on GPIO 2 with 8 LEDs
    strip = LightStrip(pin=2, name="Tachometer", numleds=8, brightness=0.5)

    # Potentiometer on ADC pin 26 (ADC0)
    pot = AnalogSensor(pin=26, name="ThrottlePot")

    # Create the MysteryGadget instance
    gadget = MysteryGadget(
        display=lcd,
        buzzer=buzzer,
        light_strip=strip,
        potentiometer=pot
    )

    # Demonstration sequence:
    print("1. Starting engine...")
    gadget.start()
    time.sleep(2)

    print("2. Running control for 10 seconds (adjust potentiometer)...")
    start_time = time.time()
    while time.time() - start_time < 10:
        gadget.control(continuous=False)
        time.sleep(0.1)

    print("3. Stopping engine...")
    gadget.stop()
    print("Demonstration finished.")
