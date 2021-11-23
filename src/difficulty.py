import enum
import sys

from music21 import dynamics, note, pitch
from music21.interval import Direction, Interval


class Fatigue(enum.IntEnum):
    LOW = 4.25
    MID = 5.0
    HIGH = 9.5

# Gives a fatigue score for each pitch register for a given note
# Returns 10.0 if above playable range, and -10.0 if below playable range
def note_pitch_register_difficulty(note):
    instrument = note.getInstrument()
    if note.pitch > instrument.highest_written():
        return 10.0
    elif note.pitch >= pitch.Pitch('G5'):
        return Fatigue.HIGH
    elif note.pitch >= pitch.Pitch('G4'):
        return Fatigue.MID
    elif note.pitch >= instrument.lowest_written():
        return Fatigue.LOW
    else:
        return -10.0

# Tests if a passage contains any out-of-range notes
# Returns 0 if all notes are in range
# Returns 10.0 if there is a note above the maximum
# Returns -10.0 if there is a note below the minimum
def passage_out_of_range(passage):
    for note in passage.get_notes():
        diff = note_pitch_register_difficulty(note)
        if abs(diff) == 10.0:
            return diff
    return 0

# Transposes a passage up or down an octave if it contains any notes outside of the instrument's playable range
def ensure_passage_in_playable_range(passage):
    out_of_range = passage_out_of_range(passage)
    if out_of_range:
        if out_of_range > 0:
            # Too high
            passage.transpose(Interval('P-8'))
        else:
            # Too low
            passage.transpose(Interval('P8'))
    return bool(passage_out_of_range(passage))


############## DIFFICULTY METRICS ##############


# Measure of how many notes are in high registers
def pitch_register_difficulty(part):
    total_register_difficulty = 0
    notes = part.flatten().notes
    for note in notes:
        total_register_difficulty += note_pitch_register_difficulty(note)
    # Avg register difficulty = total register difficulty / number of notes
    return total_register_difficulty / len(notes)

def fingering_difficulty(part):
    FINGERING_DIFF = {
        0:   {0: 0.0, 1: 1.0, 2: 1.0, 3: 1.9, 12: 1.5, 13: 3.0, 23: 3.0, 123: 3.5},
        1:   {0: 1.0, 1: 0.0, 2: 2.0, 3: 3.0, 12: 2.0, 13: 1.5, 23: 7.5, 123: 6.0},
        2:   {0: 1.0, 1: 1.5, 2: 0.0, 3: 5.3, 12: 3.0, 13: 9.5, 23: 6.0, 123: 9.0},
        3:   {0: 2.5, 1: 4.0, 2: 4.5, 3: 0.0, 12: 7.0, 13: 4.0, 23: 4.0, 123: 5.5},
        12:  {0: 1.5, 1: 1.5, 2: 2.3, 3: 7.5, 12: 0.0, 13: 6.0, 23: 6.0, 123: 5.0},
        13:  {0: 3.5, 1: 4.0, 2: 9.5, 3: 1.5, 12: 5.5, 13: 0.0, 23: 6.0, 123: 4.0},
        23:  {0: 2.5, 1: 6.0, 2: 5.5, 3: 4.0, 12: 5.0, 13: 5.5, 23: 0.0, 123: 3.8},
        123: {0: 3.0, 1: 4.0, 2: 8.5, 3: 3.5, 12: 6.0, 13: 5.0, 23: 5.0, 123: 0.0}
    }

    notes = part.flatten().notesAndRests
    num_of_notes = len(notes)
    num_of_rests = 0 if not isinstance(notes[0], note.Rest) else 1
    total_fingering_difficulty = 0

    for i in range(1, num_of_notes):
        prev_note = notes[i-1]
        curr_note = notes[i]
        # If this is a rest then don't count the transition from the previous note
        if isinstance(curr_note, note.Rest) or isinstance(prev_note, note.Rest):
            if isinstance(curr_note, note.Rest):
                num_of_rests += 1
            continue
        instrument = curr_note.getInstrument()
        prev_fingering = instrument.fingering[prev_note.pitch.midi]
        curr_fingering = instrument.fingering[curr_note.pitch.midi]
        total_fingering_difficulty += FINGERING_DIFF[prev_fingering][curr_fingering]

    num_of_notes -= num_of_rests
    # Avg fingering difficulty = total fingering difficulty / number of sounding-note transitions
    return total_fingering_difficulty / (num_of_notes - 1)

# Models depletion of lung air contents over the course of the piece
# Returns (average breathing difficulty, num. of out of breath instances)
def breathing_difficulty(part):
    LOW = {'pp': 35.5, 'p': 29.1, 'mp': 23.5, 'mf': 18.4, 'f': 14.0, 'ff': 10.5}
    MID = {'pp': 40.0, 'p': 35.8, 'mp': 31.0, 'mf': 26.2, 'f': 21.0, 'ff': 14.5}
    HIGH = {'pp': 11.0, 'p': 13.4, 'mp': 15.0, 'mf': 13.6, 'f': 10.5, 'ff': 9.0}

    total_duration = 0
    out_of_breath_instances = 0
    lung_contents = 1.0
    difficulty_sum = 0

    for element in part.flatten().notesAndRests:
        duration = element.seconds
        if isinstance(element, note.Note):
            dynamic = element.volume.getDynamicContext()
            if not dynamic:
                # Default to mf if no dynamics are present
                dynamic = dynamics.Dynamic('mf')

            note_diff = note_pitch_register_difficulty(element)
            if note_diff >= Fatigue.HIGH:
                air_depleted = duration / HIGH[dynamic.value]
            elif note_diff >= Fatigue.MID:
                air_depleted = duration / MID[dynamic.value]
            else:
                air_depleted = duration / LOW[dynamic.value]

            lung_contents = max(lung_contents - air_depleted, 0)

            # If at the end of a phrase, allow a quick breath without out-of-breath penalty
            slurs = element.getSpannerSites('Slur')
            if slurs and slurs[0].isLast(element):
                lung_contents = max(lung_contents, 0.25)

            if lung_contents == 0:
                # Out-of-breath instance
                out_of_breath_instances += 1
                lung_contents = 2/3
        else:
            # Rests over 0.25s allow for breaths to be taken
            if duration > 0.25:
                air_replenished = duration - 0.25
                lung_contents = min(lung_contents + air_replenished, 1)
        difficulty = 100 - (lung_contents * 100)
        difficulty_sum += difficulty
        total_duration += duration
    
    # Avg breathing difficulty = total breathing difficulty / duration of piece
    avg_breathing_difficulty = difficulty_sum / total_duration
    return (avg_breathing_difficulty, out_of_breath_instances)

# Measure of how tired your lips get
def embouchure_endurance_difficulty(part):
    total_duration = 0
    total_embouchure_endurance_difficulty = 0

    for element in part.flatten().notesAndRests:
        duration = element.seconds
        total_duration += duration
        if isinstance(element, note.Note):
            note_diff = note_pitch_register_difficulty(element)
            if abs(note_diff) != 10.0:
                total_embouchure_endurance_difficulty += duration * note_diff
        else:
            # Rests recover at 3 units per second
            total_embouchure_endurance_difficulty -= duration * 3.0

    # Avg embouchure endurance difficulty = total embouchure endurance difficulty / duration of piece
    return total_embouchure_endurance_difficulty / total_duration


# Difficulty of each interval transition
def melodic_interval_difficulty(part):
    LOW_ASC =   [1.0,1.5,1.5,1.5,2.5,2.0,3.5,3.0,4.0,4.0,5.5,5.5,7.0]
    LOW_DESC =  [1.0,1.5,1.5,2.0,2.0,2.5,5.0,6.0,6.5,6.5,8.5,8.5,11.5]
    MID_ASC =   [1.0,1.0,1.3,2.0,2.0,4.5,5.5,5.0,7.5,8.0,9.0,9.5,12.0]
    MID_DESC =  [1.0,3.5,3.5,4.5,4.5,6.5,7.5,7.0,9.0,9.0,10.0,10.5,12.0]
    HIGH_ASC =  [5.8,5.8,6.3,7.8,8.0,8.3,9.5,9.5,11.0,11.0,11.8,11.0,2.5]
    HIGH_DESC = [5.8,6.5,7.0,8.0,8.3,8.5,10.0,9.0,10.0,10.0,12.0,12.0,12.0]

    notes = part.flatten().notesAndRests
    num_of_notes = len(notes)
    num_of_rests = 0 if not isinstance(notes[0], note.Rest) else 1
    total_interval_difficulty = 0

    for i in range(1, num_of_notes):
        prev_note = notes[i-1]
        curr_note = notes[i]

        # If this is a rest then don't count the interval from the previous note
        if isinstance(curr_note, note.Rest) or isinstance(prev_note, note.Rest):
            if isinstance(curr_note, note.Rest):
                num_of_rests += 1
            continue

        interval = Interval(prev_note, curr_note)
        # Reduce intervals greater than an octave to be within an octave
        interval_semitones = abs(interval.semitones)
        interval_semitones = interval_semitones if interval_semitones <= 12 else interval_semitones % 12

        if note_pitch_register_difficulty(curr_note) >= Fatigue.HIGH:
            if interval.direction == Direction.ASCENDING:
                total_interval_difficulty += HIGH_ASC[interval_semitones]
            else:
                total_interval_difficulty += HIGH_DESC[interval_semitones]
        elif note_pitch_register_difficulty(curr_note) >= Fatigue.MID:
            if interval.direction == Direction.ASCENDING:
                total_interval_difficulty += MID_ASC[interval_semitones]
            else:
                total_interval_difficulty += MID_DESC[interval_semitones]
        else:
            if interval.direction == Direction.ASCENDING:
                total_interval_difficulty += LOW_ASC[interval_semitones]
            else:
                total_interval_difficulty += LOW_DESC[interval_semitones]

    num_of_notes -= num_of_rests
    # Avg interval difficulty = total interval difficulty / number of intervallic transitions
    return total_interval_difficulty / (num_of_notes - 1)

# Calculate and return each difficulty metric
def calculate_difficulties(score):
    melodic = embouchure = breathing = out_of_breath = fingering = register = 0
    for part in score.parts:
        melodic += melodic_interval_difficulty(part)
        embouchure += embouchure_endurance_difficulty(part)
        (breathing_, out_of_breath_) = breathing_difficulty(part)
        breathing += breathing_
        out_of_breath += out_of_breath_
        fingering += fingering_difficulty(part)
        register += pitch_register_difficulty(part)
    return (melodic, embouchure, breathing, out_of_breath, fingering, register)

# Calculate overall difficulty score as weighted sum of each difficulty metric
def overall_difficulty(score):
    (melodic, embouchure, breathing, out_of_breath, fingering, register) = calculate_difficulties(score)
    return 0.25 * melodic + 0.15 * embouchure + 0.15 * breathing + 0.1 * out_of_breath + 0.1 * fingering + 0.1 * register
