"""
# FeedbackStats.py
# Model (business) class for the Satisfaction Kiosk. Keeps the count of
# happy and unhappy votes and decides when satisfaction is too low.
# Author: Cecilia Karina Lecarnaque Mendoza (PantherID 6685036)
"""

from Log import *


class FeedbackStats:
    """
    **FeedbackStats** - counts the votes and calculates the satisfaction level.

    Satisfaction is the percentage of happy votes. If it falls below the
    threshold (30% by default) AND there are enough votes to be meaningful,
    the kiosk must alert the manager.

    Parameters:
    ----------
    threshold : int, optional
        Percentage below which satisfaction is "low" (default: 30)
    min_votes : int, optional
        Minimum number of votes before an alarm can go off, so a single
        bad vote does not wake up the manager (default: 3)

    Examples:
    ---------
    1. stats = FeedbackStats()
    2. stats.add_happy()
    3. stats.calculate_percentage()      # -> 100
    4. stats.get_light_level(16)         # -> 16 LEDs lit
    """

    def __init__(self, threshold=30, min_votes=3):
        self._happy_count = 0
        self._unhappy_count = 0
        self._threshold = threshold
        self._min_votes = min_votes
        Log.i(f"FeedbackStats created (threshold {threshold}%)")

    def add_happy(self):
        """ A customer pressed the green button """
        self._happy_count += 1
        Log.i(f"Happy vote -> {self}")

    def add_unhappy(self):
        """ A customer pressed the red button """
        self._unhappy_count += 1
        Log.i(f"Unhappy vote -> {self}")

    def get_happy_count(self):
        return self._happy_count

    def get_unhappy_count(self):
        return self._unhappy_count

    def get_total_count(self):
        """ Total number of votes received """
        return self._happy_count + self._unhappy_count

    def calculate_percentage(self):
        """
        Percentage (0-100) of happy votes. With no votes yet we return 100,
        since nobody has complained.
        """
        total = self.get_total_count()
        if total == 0:
            return 100
        return round(self._happy_count * 100 / total)

    def get_light_level(self, numleds):
        """ How many LEDs of the strip should be lit to show the satisfaction """
        return round(self.calculate_percentage() * numleds / 100)

    def get_threshold(self):
        return self._threshold

    def is_low(self):
        """ True when there are enough votes and satisfaction is under threshold """
        return (self.get_total_count() >= self._min_votes and
                self.calculate_percentage() < self._threshold)

    def reset(self):
        """ Manager resets the statistics """
        self._happy_count = 0
        self._unhappy_count = 0
        Log.i("FeedbackStats reset")

    def __str__(self):
        pct = self.calculate_percentage()
        return f"{self._happy_count} happy / {self._unhappy_count} unhappy ({pct}%)"


if __name__ == "__main__":
    s = FeedbackStats()
    assert s.calculate_percentage() == 100
    s.add_happy()
    s.add_unhappy()
    s.add_unhappy()
    assert s.get_total_count() == 3
    assert s.calculate_percentage() == 33
    assert not s.is_low()
    s.add_unhappy()
    assert s.calculate_percentage() == 25
    assert s.is_low()
    assert s.get_light_level(16) == 4
    s.reset()
    assert s.get_total_count() == 0 and not s.is_low()
    Log.i("Testing complete - FeedbackStats.py checks passed")
