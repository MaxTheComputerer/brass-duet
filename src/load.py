import sys

from music21 import clef, converter, corpus, stream

from instruments import BaritoneHorn, TenorHorn


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

    part_2 = stream.base.Part([BaritoneHorn()])
    part_2.append(list(score.parts[1].getElementsNotOfClass('Instrument')))
    convert_clef(part_2)

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
