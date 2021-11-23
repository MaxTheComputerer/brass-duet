from music21 import clef, note


# Extension of music21.analysis.Segmenter.getSegmentsList
# Adds ability to segment on slurs
def get_segments(part):
    segments = []
    first = None
    last = None
    in_slur = False
    partNotes = part.recurse().getElementsByClass(['Note', 'Rest', 'Clef'])
    for i in range(len(partNotes)):
        n = partNotes[i]
        if isinstance(n, note.Note):
            slurs = n.getSpannerSites('Slur')
            if slurs:
                if slurs[0].isFirst(n):
                    segments.append((first, last))
                    first = n
                    last = None
                    in_slur = True
                elif slurs[0].isLast(n):
                    segments.append((first, n))
                    first = last = None
                    in_slur = False
            elif not in_slur:
                if first:
                    last = n
                else:
                    first = n
        elif isinstance(n, (note.Rest, clef.Clef)) and not in_slur:
            segments.append((first, last))
            first = last = None
    # If we end with a one-note phrase
    if first is not None and last is None:
        last = first
    segments.append((first, last))

    # Remove the empty sublists given by rests
    new_segments = []
    for segment in segments:
        if segment != (None, None):
            (first,last) = segment
            new_segments.append(Passage(part, first, last))
    return new_segments

class Passage:
    def __init__(self, part, start_note, end_note):
        self.part = part
        self.start_note = start_note
        self.end_note = end_note
        self.instrument = self.part.getInstrument()

    def get_elements(self):
        start_offset = self.start_note.getOffsetInHierarchy(self.part)
        end_offset = self.end_note.getOffsetInHierarchy(self.part)
        return self.part.flatten().getElementsByOffset(start_offset, end_offset)

    def get_notes(self):
        return self.get_elements().getElementsByClass('Note')

    def transpose(self, interval):
        for note in self.get_notes():
            note.transpose(interval, inPlace=True)
