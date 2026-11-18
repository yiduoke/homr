"""Which staff of a page continues which staff of the pages before it (part tracking for merge_pages.py).

A merged piece has a fixed list of staff *slots*, ordered from the top of the system to the bottom. Every
page is a stack of k staves, top to bottom (music21 splits a piano part with two staves into 'P1-Staff1',
'P1-Staff2', so how homr paired the staves into parts does not matter here). A page of k staves gives each
of its staves one slot:

* If the page has as many staves as there are slots, the n-th staff from the top continues the n-th slot
  (the stack is the same as before). A slot only counts if at least half of the pages so far gave it a staff;
  the others (a small extra staff, a spurious one) are left out unless the page has more staves than the
  counting slots.
* Otherwise (a piece which moves between two, three and four staves per system) the staves of the page are
  matched to the slots the way a musician follows a part: in vertical order, never crossing, by register
  and clef (the median pitch of the staff against the typical pitch of the slot, plus a penalty for another
  clef). A page with fewer staves than slots leaves the slots it does not fit empty (the caller fills them
  with rests); a page with more staves than slots opens as many new slots as it has surplus staves, at
  the place in the stack where they stand, so a three-staff passage adds a middle slot.

No piece is named anywhere. The three constants are fixed a priori (an octave for another clef, a minor third
for each place a staff moves in the stack, eight notes before a staff's own median is trusted), not fitted to
any score.
"""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field

# Typical median pitch (MIDI) of a staff in each clef, used when a staff has too few notes to show its register.
CLEF_CENTRE = {"G": 72.0, "F": 48.0, "C": 60.0}
MIN_NOTES = 8
CLEF_COST = 12.0      # semitones: matching a staff to a slot of another clef
POSITION_COST = 3.0   # semitones per place a staff is moved from where it stands counted from the top of the stack


def median(histogram: Counter) -> float | None:
    total = sum(histogram.values())
    if total == 0:
        return None
    seen = 0
    for pitch in sorted(histogram):
        seen += histogram[pitch]
        if 2 * seen >= total:
            return float(pitch)
    return None


@dataclass
class StaffProfile:
    """What the tracker needs to know about one staff of one page."""

    clef: str | None  # sign of the first clef: 'G', 'F', 'C' or None
    pitches: Counter = field(default_factory=Counter)  # MIDI pitch -> number of notes on the page

    def register(self) -> float:
        own = median(self.pitches) if sum(self.pitches.values()) >= MIN_NOTES else None
        if own is not None:
            return own
        return CLEF_CENTRE.get(self.clef or "", 60.0)


@dataclass
class Slot:
    key: str
    first_clef: str | None
    pitches: Counter = field(default_factory=Counter)
    clefs: Counter = field(default_factory=Counter)  # clef of the staves the slot got, one per page
    pages: int = 0

    @property
    def clef(self) -> str | None:
        """The clef most of its staves had (the first one on a tie), so one misread page does not decide."""
        if not self.clefs:
            return self.first_clef
        top = max(self.clefs.values())
        return next(c for c in ([self.first_clef] + list(self.clefs)) if self.clefs.get(c, 0) == top)

    def register(self) -> float:
        own = median(self.pitches) if sum(self.pitches.values()) >= MIN_NOTES else None
        if own is not None:
            return own
        return CLEF_CENTRE.get(self.clef or "", 60.0)

    def take(self, staff: StaffProfile) -> None:
        self.pitches.update(staff.pitches)
        if staff.clef:
            self.clefs[staff.clef] += 1
        self.pages += 1


def cost(staff: StaffProfile, slot: Slot, staff_index: int, slot_index: int) -> float:
    """Distance between a staff of a page and a slot: register, clef, and the places it moves in the stack.

    The last term only decides between matches which the registers hardly tell apart (two grand staves of
    similar range): the stack is then read from the top, as for a page with as many staves as slots.
    """
    clef_cost = CLEF_COST if staff.clef and slot.clef and staff.clef != slot.clef else 0.0
    return abs(staff.register() - slot.register()) + clef_cost + POSITION_COST * abs(staff_index - slot_index)


def align(staves, slots):
    return [i if i < len(slots) else None for i in range(len(staves))]


class SlotTracker:
    """The ordered list of slots of a piece, grown page by page."""

    def __init__(self) -> None:
        self.slots: list[Slot] = []
        self.pages = 0  # pages assigned so far

    def established(self) -> list[int]:
        """Indices of the slots which at least half of the pages so far gave a staff (the rest are ossia-like extras)."""
        return [i for i, s in enumerate(self.slots) if 2 * s.pages >= self.pages]

    def assign(self, staves: list[StaffProfile], keys: list[str]) -> list[tuple[Slot, bool]]:
        """The slot of every staff of the next page, and whether this page opened the slot.

        keys: the name a staff would give a new slot (made unique here). self.slots is updated: new slots
        are placed in the stack where the staff stands, among the slots a page leaves out by register
        (a staff of lower register goes below a skipped slot of higher register).
        """
        if self.slots:
            # A page with no more staves than there are established slots is matched to those only, so a staff
            # which a few pages have (a spurious or small extra staff) does not take notes of the piece's staves
            # later; a page with more staves can use every slot and open new ones.
            candidates = list(range(len(self.slots)))
            if len(staves) > len(candidates):
                candidates = list(range(len(self.slots)))
            if len(staves) == len(candidates):
                local: list[int | None] = list(range(len(staves)))
            else:
                local = align(staves, [self.slots[i] for i in candidates])
            chosen = [None if j is None else candidates[j] for j in local]
        else:
            chosen = [None] * len(staves)
        self.pages += 1
        old = list(self.slots)
        order: list[Slot] = []
        result: list[tuple[Slot, bool]] = []
        pointer = 0  # next old slot not yet in `order`
        group: list[tuple[StaffProfile, Slot]] = []  # new slots since the last matched staff

        def flush(upto: int) -> None:
            """Put old slots pointer..upto-1 and the pending new slots into `order` by register."""
            nonlocal pointer, group
            skipped = old[pointer:upto]
            merged = list(skipped)
            for staff, new in group:
                at = next((n for n, s in enumerate(merged) if any(s is o for o in skipped) and s.register() < staff.register()), len(merged))
                merged.insert(at, new)
            order.extend(merged)
            pointer = upto
            group = []

        taken = {s.key for s in old}
        for index, (staff, slot_index) in enumerate(zip(staves, chosen)):
            if slot_index is None:
                key = keys[index]
                suffix = 2
                unique = key
                while unique in taken:
                    unique = f"{key}#{suffix}"
                    suffix += 1
                taken.add(unique)
                slot = Slot(unique, staff.clef)
                group.append((staff, slot))
                result.append((slot, True))
            else:
                flush(slot_index)
                order.append(old[slot_index])
                pointer = slot_index + 1
                result.append((old[slot_index], False))
        flush(len(old))
        self.slots = order
        for slot, staff in zip((r[0] for r in result), staves):
            slot.take(staff)
        return result
