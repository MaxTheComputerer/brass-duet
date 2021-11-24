from music21 import interval, pitch
from music21.instrument import BrassInstrument


class CustomBrassInstrument(BrassInstrument):
    
    def __init__(self):
        super().__init__()

        self.midiProgram = 60

        self.fingering = {
            54: 123, # F#3
            55: 13,  # G3
            56: 23,  # G#3
            57: 12,  # A3
            58: 1,   # B-3
            59: 2,   # B3
            60: 0,   # C4
            61: 123, # C#4
            62: 13,  # D4
            63: 23,  # E-4
            64: 12,  # E3
            65: 1,   # F4
            66: 2,   # F#4
            67: 0,   # G4
            68: 23,  # G#4
            69: 12,  # A4
            70: 1,   # B-4
            71: 2,   # B4
            72: 0,   # C5
            73: 12,  # C#5
            74: 1,   # D5
            75: 2,   # E-5
            76: 0,   # E5
            77: 1,   # F5
            78: 2,   # F#5
            79: 0,   # G5
            80: 23,  # G#5
            81: 12,  # A5
            82: 1,   # B-5
            83: 2,   # B5
            84: 0    # C6
        }

    def lowest_written(self):
        return self.lowestNote.transpose(self.transposeToWritten)

    def highest_written(self):
        return self.highestNote.transpose(self.transposeToWritten)

    def lowest_concert(self):
        return self.lowestNote
    
    def highest_concert(self):
        return self.highestNote

class TenorHorn(CustomBrassInstrument):
    def __init__(self):
        super().__init__()

        self.instrumentName = 'Tenor Horn'
        self.instrumentAbbreviation = 'Hrn'
        self.instrumentSound = 'brass.tenor-horn'

        # In concert pitch
        self.lowestNote = pitch.Pitch('A2')
        self.highestNote = pitch.Pitch('E-5')

        # Written -> Concert
        self.transposition = interval.Interval('M-6')
        self.transposeToConcert = self.transposition
        # Concert -> Written
        self.transposeToWritten = interval.Interval('M6')

class BaritoneHorn(CustomBrassInstrument):
    def __init__(self):
        super().__init__()

        self.instrumentName = 'Baritone'
        self.instrumentAbbreviation = 'Bari'
        self.instrumentSound = 'brass.baritone-horn'

        # In concert pitch
        self.lowestNote = pitch.Pitch('E2')
        self.highestNote = pitch.Pitch('B-4')

        # Written -> Concert
        self.transposition = interval.Interval('M-9')
        self.transposeToConcert = self.transposition
        # Concert -> Written
        self.transposeToWritten = interval.Interval('M9')
