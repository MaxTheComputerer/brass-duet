from pathlib import Path
from statistics import mean

from music21 import analysis

import load
from difficulty import *
from passage import *
from util import *


def arrange(s):
    original_key = getKey(s)
    key_difficulties = {}

    for sharps in range(-5,2):
        distance_to_original_key = abs(sharps - original_key.sharps)
        sharps_per_instrument = get_sharps_per_instrument(sharps)
        avg_sharps_per_instrument = mean(sharps_per_instrument.values())
        out_of_playable_range = False

        print('\n=========================')
        print('Key: ', sharps, 'sharps\n')

        score = transpose_to_key_sig(s, sharps).toWrittenPitch()
        for part in score.parts:
            passages = get_segments(part)
            for passage in passages:
                if ensure_passage_in_playable_range(passage):
                    out_of_playable_range = True
                    
        if out_of_playable_range:
            print('Error: Contains notes out of range. Add more phrase marks or reduce range',file=sys.stderr)
            continue
         
        score_for_analysis = score.stripTies()
        (melodic, embouchure, breathing, out_of_breath, fingering, register) = calculate_difficulties(score_for_analysis)

        print('Melodic:       ', melodic)
        print('Embouchure:    ', embouchure)
        print('Breathing:     ', breathing)
        print('Out-of-breath: ', out_of_breath)
        print('Fingering:     ', fingering)
        print('Register:      ', register)
        difficulty = 0.25 * melodic \
                + 0.15 * embouchure \
                + 0.1 * breathing \
                + 0.1 * out_of_breath \
                + 0.1 * fingering \
                + 0.15 * register \
                + 0.1 * avg_sharps_per_instrument \
                + 0.05 * distance_to_original_key
        print('\nTotal difficulty: ', difficulty)
        key_difficulties[score] = difficulty
        
    return min(key_difficulties, key=key_difficulties.get)


def generate_data(s):
    print('Title@Sharps,Melodic,Embouchure,Breathing,Out-of-breath,Fingering,Register,Avg sharps,Key distance,Overall')
    original_key = getKey(s)
    for sharps in range(-5,2):
        distance_to_original_key = abs(sharps - original_key.sharps)
        sharps_per_instrument = get_sharps_per_instrument(sharps)
        avg_sharps_per_instrument = mean(sharps_per_instrument.values())
        out_of_playable_range = False

        score = transpose_to_key_sig(s, sharps).toWrittenPitch()
        for part in score.parts:
            passages = get_segments(part)
            for passage in passages:
                if ensure_passage_in_playable_range(passage):
                    out_of_playable_range = True
                    
        if out_of_playable_range:
            continue

        score_for_analysis = score.stripTies()
        (melodic, embouchure, breathing, out_of_breath, fingering, register) = calculate_difficulties(score_for_analysis)
        difficulty = 0.25 * melodic \
                + 0.15 * embouchure \
                + 0.1 * breathing \
                + 0.1 * out_of_breath \
                + 0.1 * fingering \
                + 0.15 * register \
                + 0.1 * avg_sharps_per_instrument \
                + 0.05 * distance_to_original_key

        print(score.metadata.title+'@'+str(sharps),melodic,embouchure,breathing,out_of_breath,fingering,register,avg_sharps_per_instrument,distance_to_original_key,difficulty, sep=',')


OUT_DIR = Path('out')

s = load.load_xml(OUT_DIR / 'stopthecavalry.mxl')
show(arrange(s))
#generate_data(s)
