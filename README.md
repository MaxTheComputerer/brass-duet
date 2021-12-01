# Automatic Brass Duet Arranger

A tool for automatically arranging a two-part score (such as a piano score) into a duet for two brass instruments that minimises the difficulty according to Huron and Berec's trumpet difficulty metrics.

- The instruments currently implemented are the Tenor Horn and Baritone Horn but these could be easily swapped out.
- Any chords or multiple voices are combined and removed.
- Musical passages are segmented based on phrase marks (slurs) and rests so use these to mark the phrases in the score.

See [here](https://drive.google.com/file/d/1-EUFlmMSiBdPQf2tMpX8Py7Deej4U1iz/view?usp=sharing) for more details on the implementation.

## Requirements
- Python 3 (tested on 3.8.5)
- [`music21` library](https://web.mit.edu/music21/) (tested with v7.1.0)
  - Install with `pip install music21`
  - Run `python -m music21.configure` to set up music21

## Usage
### Arrange mode
The standard usage mode. Generates and shows an arrangement from an input score given in `.mxl` format.

`python duet.py arrange [-s] [-t] <path>`
- `<path>` is the path to the input `.mxl` file. The path can be absolute or relative to the current directory
- `-s` will save the output to `out/<filename>.mxl` instead of opening in your default score editor
- `-t` will open without calling music21's `makeNotation()` function. This helps MuseScore correctly detect the transposing instruments but it'll look a bit ugly

### Data generation mode
Creates arrangements for each `.mxl` file in `examples/` and prints the difficulty values for each piece in a `.csv`-like format.

`python duet.py generate-data [-t]`
- `-t` will also include all the test cases in the `examples/test/` directory

## References

- D. Huron and J. Berec, “Characterizing Idiomatic Organization in Music: A Theory and Case Study of Musical Affordances,” *Empirical Musicology Review*, vol. 4, no. 3, pp. 103-122, 2009.
- M. Johnson, "Automatic Musical Arrangement For Brass Duet," unpublished.
