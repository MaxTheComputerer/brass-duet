import enum
import sys
from statistics import mean

from music21 import dynamics, note, pitch
from music21.interval import Direction, Interval

from util import *


class Fatigue(enum.IntEnum):
    LOW = 4.25
    MID = 5.0
    HIGH = 9.5

class RegisterPreference(enum.IntEnum):
    # LOW and MID scores have been swapped to make optimise_passage_register() produce
    # results in a more appropriate register (lower =/= better)
    LOW = 5.0
    MID = 4.25
    HIGH = 9.5

# Gives a difficulty score for a given note's pitch register
# Returns 10.0 if above playable range, and -10.0 if below playable range
def note_pitch_register_difficulty(note, registerDifficulty=Fatigue):
    instrument = note.getInstrument()
    if note.pitch > instrument.highest_written():
        return 10.0
    elif note.pitch >= pitch.Pitch('G5'):
        return registerDifficulty.HIGH
    elif note.pitch >= pitch.Pitch('G4'):
        return registerDifficulty.MID
    elif note.pitch >= instrument.lowest_written():
        return registerDifficulty.LOW
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

# Calculates the average register difficulty of all the notes in a passage
def passage_pitch_register_difficulty(passage):
    notes = passage.get_notes()
    total_difficulty = 0
    for note in notes:
        total_difficulty += note_pitch_register_difficulty(note, RegisterPreference)
    return total_difficulty / len(notes)

# Transposes a passage up and down octaves to find its easiest register
def optimise_passage_register(passage):
    optimal_octave_transposition = 0
    current_octave_transposition = 0
    min_difficulty = passage_pitch_register_difficulty(passage)

    # Transpose up 8ves until it's out of range
    while not passage_out_of_range(passage):
        diff = passage_pitch_register_difficulty(passage)
        if diff < min_difficulty:
            min_difficulty = diff
            optimal_octave_transposition = current_octave_transposition
        passage.transpose(Interval('P8'))
        current_octave_transposition += 1

    # Reset to 0 transposition
    while current_octave_transposition > 0:
        passage.transpose(Interval('P-8'))
        current_octave_transposition -= 1

    # Transpose down 8ves until it's out of range
    while not passage_out_of_range(passage):
        diff = passage_pitch_register_difficulty(passage)
        if diff < min_difficulty:
            min_difficulty = diff
            optimal_octave_transposition = current_octave_transposition
        passage.transpose(Interval('P-8'))
        current_octave_transposition -= 1

    # Transpose back up 8ves until we find the optimal again
    while current_octave_transposition < optimal_octave_transposition:
        passage.transpose(Interval('P8'))
        current_octave_transposition += 1
    return bool(passage_out_of_range(passage))


############## DIFFICULTY METRICS ##############


# Measure of the proportion of notes that are in high registers
# Ranges from 4.25 to 9.5
def pitch_register_difficulty(part):
    total_register_difficulty = 0
    notes = part.flatten().notes
    for note in notes:
        total_register_difficulty += note_pitch_register_difficulty(note)
    # Avg register difficulty = total register difficulty / number of notes
    return total_register_difficulty / len(notes)

# Measure of how difficult the change in fingering is for each note transition
# Ranges from 0 to 9.5
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
    if num_of_notes <= 1:
        return 0.0
    # Avg fingering difficulty = total fingering difficulty / number of sounding-note transitions
    return total_fingering_difficulty / (num_of_notes - 1)

# Models depletion of lung air contents over the course of the piece
# Returns (average breathing difficulty, num. of out of breath instances)
# Ranges from 0 to 100
def breathing_difficulty(part):
    LOW = {'pp': 35.5, 'p': 29.1, 'mp': 23.5, 'mf': 18.4, 'f': 14.0, 'ff': 10.5}
    MID = {'pp': 40.0, 'p': 35.8, 'mp': 31.0, 'mf': 26.2, 'f': 21.0, 'ff': 14.5}
    HIGH = {'pp': 11.0, 'p': 13.4, 'mp': 15.0, 'mf': 13.6, 'f': 10.5, 'ff': 9.0}

    total_duration = 0
    out_of_breath_instances = 0
    lung_contents = 1.0
    contents_sum = 0
    notes = part.flatten().notesAndRests

    for element in notes:
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
        contents_sum += lung_contents
        total_duration += duration
    
    avg_lung_contents = contents_sum / len(notes)
    avg_breathing_difficulty = 100 - (avg_lung_contents * 100)
    return (avg_breathing_difficulty, out_of_breath_instances)

# Measure of how tired your lips get
# Ranges from 0 to 9.5
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
            total_embouchure_endurance_difficulty = max(total_embouchure_endurance_difficulty - (duration * 3.0), 0)

    # Avg embouchure endurance difficulty = total embouchure endurance difficulty / duration of piece
    return total_embouchure_endurance_difficulty / total_duration


# Difficulty of each interval transition
# Ranges from 1 to 12
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
    if num_of_notes <= 1:
        return 0.0
    # Avg interval difficulty = total interval difficulty / number of intervallic transitions
    return total_interval_difficulty / (num_of_notes - 1)


# Calculate and return each difficulty metric combined for all parts
# Contribution of each part to the scores is determined by part_weights
def part_difficulties(score, part_weights=[0.5,0.5]):
    if len(part_weights) != len(score.parts) or sum(part_weights) != 1.0:
        print('Error: Invalid part weights entered', file=sys.stderr)
        return None
    interval = embouchure = breathing = out_of_breath = fingering = register = 0
    for i in range(len(score.parts)):
        part = score.parts[i]
        interval += part_weights[i] * melodic_interval_difficulty(part)
        embouchure += part_weights[i] * embouchure_endurance_difficulty(part)
        (breathing_, out_of_breath_) = breathing_difficulty(part)
        breathing += part_weights[i] * breathing_
        out_of_breath += part_weights[i] * out_of_breath_
        fingering += part_weights[i] * fingering_difficulty(part)
        register += part_weights[i] * pitch_register_difficulty(part)
    return (interval, embouchure, breathing, out_of_breath, fingering, register)

def normalise_difficulties(difficulties):
    (interval, embouchure, breathing, out_of_breath, fingering, register) = difficulties
    return (
        interval / 12.0,
        embouchure / 9.5,
        breathing / 100,
        out_of_breath,
        fingering / 9.5,
        register / 9.5
    )

# Calculate overall difficulty score as weighted sum of each difficulty metric
def overall_difficulty(score, original_key, sharps, printDifficulties=True):
    distance_to_original_key = abs(sharps - original_key.sharps)
    sharps_per_instrument = get_sharps_per_instrument(sharps)
    avg_sharps_per_instrument = mean([abs(v) for v in sharps_per_instrument.values()])

    difficulties = normalise_difficulties(part_difficulties(score))
    (interval, embouchure, breathing, out_of_breath, fingering, register) = difficulties

    total_difficulty = 0.25 * interval \
        + 0.15 * embouchure \
        + 0.1 * breathing \
        + 0.1 * out_of_breath \
        + 0.1 * fingering \
        + 0.15 * register \
        + 0.1 * avg_sharps_per_instrument \
        + 0.05 * distance_to_original_key

    if printDifficulties:
        print('Interval:         ', interval)
        print('Embouchure:       ', embouchure)
        print('Breathing:        ', breathing)
        print('Out-of-breath:    ', out_of_breath)
        print('Fingering:        ', fingering)
        print('Register:         ', register)
        print('Avg sharps/flats: ', avg_sharps_per_instrument)
        print('Key distance:     ', distance_to_original_key)
        print('\nTotal difficulty: ', total_difficulty)

    return (
        interval,
        embouchure,
        breathing,
        out_of_breath,
        fingering,
        register,
        avg_sharps_per_instrument,
        distance_to_original_key,
        total_difficulty
    )
