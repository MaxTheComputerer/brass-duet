import argparse
from pathlib import Path

import load
from difficulty import *
from passage import *
from util import *

EXAMPLES_DIR = Path('examples')
TEST_DIR = EXAMPLES_DIR / 'test'
OUT_DIR = Path('out')

class BrassDuet:

    def __init__(self, path: Path):
        self.in_path = path
        self.out_path = OUT_DIR / path.name
        self.original_score = load.load_xml(self.in_path)
        self.arrangements = []

    def arrange(self, printDifficulties=True):
        original_key = getKey(self.original_score)
        for sharps in range(-5,2):
            transposed_score = transpose_to_key_sig(self.original_score, sharps).toWrittenPitch()

            if printDifficulties:
                print('\n=========================')
                print('Key: ', sharps, 'sharps\n')

            out_of_playable_range = False        
            for part in transposed_score.parts:
                passages = get_segments(part)
                for passage in passages:
                    out_of_range_first = ensure_passage_in_playable_range(passage)
                    out_of_range_second = optimise_passage_register(passage)
                    if out_of_range_first and out_of_range_second:
                        out_of_playable_range = True
                        break
            if out_of_playable_range:
                if printDifficulties:
                    print('Error: Contains notes out of range. Add more phrase marks or reduce range',file=sys.stderr)
                continue
            
            score_for_analysis = transposed_score.stripTies()
            difficulties = overall_difficulty(score_for_analysis, original_key, sharps, printDifficulties=printDifficulties)
            arrangement = Arrangement(transposed_score, sharps, difficulties)
            self.arrangements.append(arrangement)

        if printDifficulties:
            best = self.get_arrangement()
            print('\n=========================')
            print('Best arrangement: ', best.sharps, 'sharps')
            print('Total difficulty: ', best.total_difficulty, '\n')

    def get_arrangement(self):
        if not self.arrangements:
            self.arrange()
        return min(self.arrangements, key=lambda a: a.total_difficulty)

    def get_difficulties(self):
        a = self.get_arrangement()
        return (
            a.interval,
            a.embouchure,
            a.breathing,
            a.out_of_breath,
            a.fingering,
            a.register,
            a.avg_sharps_per_instrument,
            a.distance_to_original_key,
            a.total_difficulty
        )

    def save(self):
        if not self.arrangements:
            print('Error: No arrangement generated. Call arrange() or get_arrangement() first', file=sys.stderr)
            return
        OUT_DIR.mkdir(exist_ok=True)
        self.get_arrangement().score.write('musicxml', self.out_path)
        print('Arrangement saved to', self.out_path)

    def show(self, transposable=False):
        if not self.arrangements:
            print('Error: No arrangement generated. Call arrange() or get_arrangement() first', file=sys.stderr)
            return
        if transposable:
            show(self.get_arrangement().score)
        else:
            self.get_arrangement().score.show()

# Class to store an arrangement and its difficulty metrics
class Arrangement:
    def __init__(self, score, sharps, difficulties):
        self.score = score
        self.sharps = sharps
        (self.interval,
        self.embouchure,
        self.breathing,
        self.out_of_breath,
        self.fingering,
        self.register,
        self.avg_sharps_per_instrument,
        self.distance_to_original_key,
        self.total_difficulty) = difficulties

# Generate and print metrics for a list of paths to .mxl files
def generate_data(pieces):
    print('Title@Sharps,Interval,Embouchure,Breathing,Out-of-breath,Fingering,Register,Avg sharps,Key distance,Overall')
    for piece in pieces:
        duet = BrassDuet(piece)
        duet.arrange(printDifficulties=False)
        title = duet.original_score.metadata.title
        for a in duet.arrangements:
            print(
                title+'@'+str(a.sharps),
                a.interval,
                a.embouchure,
                a.breathing,
                a.out_of_breath,
                a.fingering,
                a.register,
                a.avg_sharps_per_instrument,
                a.distance_to_original_key,
                a.total_difficulty,
                sep=','
            )

def arrange_mode(args):
    duet = BrassDuet(Path(args.path))
    duet.arrange()
    if args.save:
        duet.save()
    else:
        duet.show()

def data_mode(args):
    pieces = list(EXAMPLES_DIR.glob('*.mxl'))
    if args.tests:
        pieces += list(TEST_DIR.glob('*.mxl'))
    generate_data(pieces)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.set_defaults(func=lambda args: parser.print_help())
    subparsers = parser.add_subparsers(title="mode")

    arrange_parser = subparsers.add_parser('arrange', help="Arrange a two-part score for brass duet")
    arrange_parser.add_argument('path', help="Path to .mxl file to be arranged")
    arrange_parser.add_argument(
        '-s',
        '--save',
        dest='save',
        action="store_true",
        help="Save arrangement to output file")
    arrange_parser.set_defaults(func=arrange_mode)

    data_parser = subparsers.add_parser('generate-data', help="Generate difficulty metrics for all files in \"examples\" directory")
    data_parser.add_argument(
        "-t",
        "--include-tests",
        dest="tests",
        action="store_true",
        help="Include test cases files found in \"examples/test/\""
    )
    data_parser.set_defaults(func=data_mode)

    args = parser.parse_args(['arrange', 'examples\\51.mxl'])
    args.func(args)
