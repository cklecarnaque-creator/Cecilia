"""
# Employees.py
# Model classes for the Dynamic NamePlate: the Employee base class, its four
# subtypes (Faculty, Staff, StudentWorker, Administrator) and the Calendar
# used by Administrators for automatic availability.
# Author: Cecilia
"""

import time
from Log import *

# The three possible availability states (like Teams)
AVAILABLE = "Available"
AWAY = "Away"
BUSY = "Busy"
STATUSES = (AVAILABLE, AWAY, BUSY)


class Employee:
    """
    **Employee** - base class for everyone who can occupy an office.

    Everyone has a name, phone number and position. Availability is set
    manually by cycling Available -> Away -> Busy -> Available.

    Parameters:
    ----------
    name : str
        Full name of the person
    phone : str
        Office phone number
    position : str
        Job title / position
    department : str, optional
        Department (default: "")
    email : str, optional
        Email address (default: "")

    Examples:
    ---------
    1. e = Employee("Ana Lopez", "305-348-1111", "Advisor")
    2. e.cycleAvailability()   # Available -> Away
    """

    def __init__(self, name, phone, position, department="", email=""):
        self._name = name
        self._phone = phone
        self._position = position
        self._department = department
        self._email = email
        self._availability = AVAILABLE
        Log.i(f"Employee created: {name}")

    def getName(self):
        return self._name

    def getPhone(self):
        return self._phone

    def getPosition(self):
        return self._position

    def getAvailability(self):
        """ Returns the current availability (Available, Away or Busy) """
        return self._availability

    def cycleAvailability(self):
        """ Moves to the next status: Available -> Away -> Busy -> Available """
        i = STATUSES.index(self._availability)
        self._availability = STATUSES[(i + 1) % len(STATUSES)]
        Log.i(f"{self._name} is now {self._availability}")

    def getDisplayLines(self):
        """
        Returns the text to show on the LCD.
        Item 0 is the top row (always the name). The rest are "pages" that
        the NamePlate rotates through on the bottom row.
        Subclasses override this to add their own information.
        """
        return [self._name, self._position, "Tel " + self._phone,
                "Status:" + self.getAvailability()]


class Faculty(Employee):
    """
    **Faculty** - a professor. Also shows the courses taught and office hours.

    Parameters:
    ----------
    courses : list[str]
        Course codes being taught, e.g. ["COP 4521"]
    officeHours : str
        Office hours, e.g. "MW 2-4pm"
    """

    def __init__(self, name, phone, position, courses, officeHours, department="", email=""):
        super().__init__(name, phone, position, department, email)
        self._courses = courses
        self._officeHours = officeHours

    def getCourses(self):
        return self._courses

    def getOfficeHours(self):
        return self._officeHours

    def getDisplayLines(self):
        lines = super().getDisplayLines()
        lines.append("OH " + self._officeHours)
        for c in self._courses:
            lines.append("Teaches " + c)
        return lines


class Staff(Employee):
    """
    **Staff** - a staff member. Also shows the shift they work.

    Parameters:
    ----------
    shift : str
        Working shift, e.g. "8am-5pm"
    """

    def __init__(self, name, phone, position, shift, department="", email=""):
        super().__init__(name, phone, position, department, email)
        self._shift = shift

    def getShift(self):
        return self._shift

    def getDisplayLines(self):
        lines = super().getDisplayLines()
        lines.append("Shift " + self._shift)
        return lines


class StudentWorker(Employee):
    """
    **StudentWorker** - a student who works in the office.
    Also shows their major and supervisor.

    Parameters:
    ----------
    major : str
        Student's major, e.g. "IT"
    supervisor : str
        Name of the supervisor
    """

    def __init__(self, name, phone, position, major, supervisor, department="", email=""):
        super().__init__(name, phone, position, department, email)
        self._major = major
        self._supervisor = supervisor

    def getMajor(self):
        return self._major

    def getSupervisor(self):
        return self._supervisor

    def getDisplayLines(self):
        lines = super().getDisplayLines()
        lines.append("Major " + self._major)
        lines.append("Sup. " + self._supervisor)
        return lines


class Calendar:
    """
    **Calendar** - a very simple daily schedule.
    Each block is (startMinute, endMinute, status), where minutes are counted
    from midnight. Any time not inside a block counts as Available.

    Examples:
    ---------
    1. cal = Calendar()
    2. cal.addBlock(9*60, 11*60, "Busy")      # busy from 9 to 11
    3. cal.getStatusAt(10*60)                 # -> "Busy"
    """

    def __init__(self):
        self._busyBlocks = []

    def addBlock(self, start, end, status):
        """ Adds a block of time (in minutes since midnight) with a status """
        self._busyBlocks.append((start, end, status))

    def getStatusAt(self, minute):
        """ Returns the status for a given minute of the day """
        for start, end, status in self._busyBlocks:
            if start <= minute < end:
                return status
        return AVAILABLE


class Administrator(Employee):
    """
    **Administrator** - availability is automatic, taken from their Calendar.
    The status button does nothing for administrators.

    Parameters:
    ----------
    calendar : Calendar
        The administrator's schedule
    """

    def __init__(self, name, phone, position, calendar, department="", email=""):
        super().__init__(name, phone, position, department, email)
        self._calendar = calendar

    def getAvailability(self):
        """ Override: look up the current time in the calendar """
        t = time.localtime()
        minute = t[3] * 60 + t[4]
        return self._calendar.getStatusAt(minute)

    def cycleAvailability(self):
        """ Override: administrators cannot change their status manually """
        Log.i(f"{self._name} is an Administrator - status comes from calendar")

    def getDisplayLines(self):
        lines = super().getDisplayLines()
        lines.append("(Auto calendar)")
        return lines


if __name__ == "__main__":
    f = Faculty("Dr. Sengupta", "305-348-0001", "Professor", ["COP 4521"], "MW 2-4pm")
    assert f.getAvailability() == AVAILABLE
    f.cycleAvailability()
    assert f.getAvailability() == AWAY
    Log.i(str(f.getDisplayLines()))

    cal = Calendar()
    cal.addBlock(0, 24 * 60, BUSY)
    a = Administrator("Maria Diaz", "305-348-0002", "Director", cal)
    a.cycleAvailability()
    assert a.getAvailability() == BUSY
    Log.i("Testing complete - Employees.py checks passed")
