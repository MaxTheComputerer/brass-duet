from music21 import interval, key
from instruments import *


# Trick to display output with transposing instruments working correctly
def show(score, format=None):
    if format:
        score.show(format, makeNotation=False)
    else:
        score.show(makeNotation=False)

# Transpose a score to the key with the given number of sharps, preserving key mode
def transpose_to_key_sig(score, sharps):
    original_key = score.analyze('key')
    ks = key.KeySignature(sharps)
    new_key = ks.asKey(original_key.mode)
    i = interval.Interval(original_key.tonic, new_key.tonic)
    return score.transpose(i)

# Returns a dictionary of number of sharps written for each instrument for a given concert pitch key
def get_sharps_per_instrument(sharps):
    ks = key.KeySignature(sharps)
    sharps_per_instrument = {}
    for instr in [TenorHorn(), BaritoneHorn()]:
        sharps_per_instrument[instr] = ks.transpose(instr.transposeToWritten).sharps
    return sharps_per_instrument
