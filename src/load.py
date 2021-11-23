import sys

from music21 import clef, converter, corpus, stream

from instruments import BaritoneHorn, TenorHorn


# Combines multiple voices into one. Use before convert_chords()
def convert_voices(part):
    for measure in part['Measure']:
        if measure.hasVoices():
            part.replace(measure, measure.chordify(toSoundingPitch=False))

# Replaces chords with their top or bottom notes
def convert_chords(part, keepTop=True):
    for chord in part['Chord']:
        sorted_chord = chord.sortAscending()
        container = chord.activeSite
        slurs = chord.getSpannerSites('Slur')
        if keepTop:
            note = sorted_chord[-1]
        else:
            note = sorted_chord[0]
        if slurs:
            slurs[0].replaceSpannedElement(chord, note)
        container.replace(chord, note)

# Converts a part to use treble clef only
def convert_clef(part):
    clefs = list(part['Clef'])
    part.remove(clefs, recurse=True)
    part.measure(0,indicesNotNumbers=True).insert(0, clef.TrebleClef())

# Converts instruments to Tenor Horn and Baritone
def convert_instruments(score):
    score.atSoundingPitch = True
    part_1 = stream.base.Part([TenorHorn()])
    part_1.append(list(score.parts[0].getElementsNotOfClass('Instrument')))
    convert_clef(part_1)
    convert_voices(part_1)
    convert_chords(part_1, keepTop=True)

    part_2 = stream.base.Part([BaritoneHorn()])
    part_2.append(list(score.parts[1].getElementsNotOfClass('Instrument')))
    convert_clef(part_2)
    convert_voices(part_2)
    convert_chords(part_2, keepTop=False)

    score.removeByClass(['Part', 'StaffGroup'])
    score.append([part_1, part_2])

def parse_xml(path, isCorpus=False):
    if isCorpus:
        return corpus.parse(path)
    else:
        return converter.parse(path)

def load_xml(path, isCorpus=False):
    score = parse_xml(path, isCorpus)
    if len(score.parts) != 2:
        print('Error: Score doesn\'t have two parts',file=sys.stderr)
        sys.exit()
    convert_instruments(score)
    return score
