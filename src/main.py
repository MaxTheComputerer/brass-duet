from pathlib import Path

from music21 import analysis

import load
from difficulty import *
from passage import *
from util import *


def arrange(s):
    key_difficulties = {}
    for sharps in range(-5,2):
        score = transpose_to_key_sig(s, sharps).toWrittenPitch()
        
        for part in score.parts:
            passages = get_segments(part)
            for passage in passages:
                ensure_passage_in_playable_range(passage)

        print('\n=========================')
        print('Key: ', sharps, 'sharps\n')

        (melodic, embouchure, breathing, out_of_breath, fingering, register) = calculate_difficulties(score)

        print('Melodic:       ', melodic)
        print('Embouchure:    ', embouchure)
        print('Breathing:     ', breathing)
        print('Out-of-breath: ', out_of_breath)
        print('Fingering:     ', fingering)
        print('Register:      ', register)
        difficulty = 0.25 * melodic + 0.15 * embouchure + 0.15 * breathing + 0.1 * out_of_breath + 0.1 * fingering + 0.1 * register
        print('\nTotal difficulty: ', difficulty)
        key_difficulties[score] = difficulty
        
    return min(key_difficulties, key=key_difficulties.get).toWrittenPitch()



OUT_DIR = Path('out')

s = load.load_xml(OUT_DIR / '78.mxl')

show(arrange(s))
