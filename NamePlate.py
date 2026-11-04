"""
# NamePlate.py
# Controller for the Dynamic NamePlate. Keeps the list of employees, reacts
# to the three buttons (previous, next, status) and updates the views.
# Author: Cecilia
"""

import time
from Log import *
from Button import Button


class NamePlate:
    """
    **NamePlate** - the controller.

    - **prev** button: show previous person (falling sound)
    - **next** button: show next person (rising sound)
    - **status** button: cycle Available/Away/Busy (not for Administrators)

    The bottom row of the LCD rotates through each person's info every
    few seconds.

    Parameters:
    ----------
    view : NamePlateView
        Shows text on the LCD
    statusLight : StatusLight
        Shows availability on the LightStrip
    sound : SoundEffects
        Plays sounds on the buzzer
    prevPin, nextPin, statusPin : int
        GPIO pins of the three buttons

    Examples:
    ---------
    1. plate = NamePlate(view, light, sound, 10, 11, 12)
    2. plate.addEmployee(Faculty(...))
    3. plate.run()
    """

    ROTATE_MS = 2500   # how often the bottom row changes

    def __init__(self, view, statusLight, sound, prevPin, nextPin, statusPin):
        self._employees = []
        self._currentIndex = 0
        self._infoPage = 0
        self._lastRotateTime = time.ticks_ms()
        self._pendingAction = None
        self._view = view
        self._statusLight = statusLight
        self._sound = sound
        # The buttons call buttonPressed / buttonReleased on this object
        self._prevButton = Button(prevPin, "prev", handler=self)
        self._nextButton = Button(nextPin, "next", handler=self)
        self._statusButton = Button(statusPin, "status", handler=self)

    def addEmployee(self, employee):
        self._employees.append(employee)

    def nextEmployee(self):
        self._currentIndex = (self._currentIndex + 1) % len(self._employees)
        self._sound.playNext()
        self._showCurrent()

    def previousEmployee(self):
        self._currentIndex = (self._currentIndex - 1) % len(self._employees)
        self._sound.playPrevious()
        self._showCurrent()

    def cycleCurrentAvailability(self):
        self._employees[self._currentIndex].cycleAvailability()
        self._sound.playStatusChange()
        self._infoPage = 2          # jump to the "Status:" page so you see it
        self._showCurrent(resetPage=False)

    def buttonPressed(self, name):
        """
        Called by Button when pressed. It only remembers which button was
        pressed; the main loop in run() does the real work. This avoids the
        button interrupt and the main loop using the LCD at the same time.
        """
        self._pendingAction = name

    def buttonReleased(self, name):
        pass

    def run(self):
        """ Main loop: handles button presses and rotates the info """
        if not self._employees:
            self._view.showMessage("No employees")
            return
        self._view.showMessage("NamePlate ON")
        time.sleep(1)
        self._showCurrent()
        while True:
            action = self._pendingAction
            self._pendingAction = None
            if action == "next":
                self.nextEmployee()
            elif action == "prev":
                self.previousEmployee()
            elif action == "status":
                self.cycleCurrentAvailability()
            self._rotateInfo()
            time.sleep(0.05)

    def _showCurrent(self, resetPage=True):
        """ Draws the current employee on the LCD and the LightStrip """
        if resetPage:
            self._infoPage = 0
        self._lastRotateTime = time.ticks_ms()
        emp = self._employees[self._currentIndex]
        lines = emp.getDisplayLines()
        pages = lines[1:]
        self._view.showEmployee(lines[0], pages[self._infoPage % len(pages)])
        self._statusLight.showStatus(emp.getAvailability())
        Log.i(f"Showing {emp.getName()} ({type(emp).__name__})")

    def _rotateInfo(self):
        """ Every ROTATE_MS, shows the next info page on the bottom row """
        if time.ticks_diff(time.ticks_ms(), self._lastRotateTime) >= NamePlate.ROTATE_MS:
            self._infoPage += 1
            self._showCurrent(resetPage=False)


if __name__ == "__main__":
    Log.i("Run main.py to test the NamePlate controller")
