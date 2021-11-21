from instruments import *

t = TenorHorn()
note = t.lowest_written()
while note != t.highest_written():
    print("'"+str(note.midi)+"': 1,")
    note.transpose(interval.Interval(1), inPlace=True)
print("'"+str(note.midi)+"': 1")


