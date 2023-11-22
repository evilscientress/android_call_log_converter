import os.path
import sys
from argparse import ArgumentParser
from datetime import date, datetime
from pathlib import Path

from .models import PhoneCall


def _parse_date(date: str) -> date:
    return datetime.strptime(date, '%Y-%m-%d').date()

def cli():
    prog = os.path.basename(sys.argv[0])
    if prog == '__main__.py':
        prog = 'python -m call_log_converter'
    parser = ArgumentParser(
        prog=prog,
        description='Converts a call log exported from a Android phone in json format to a csv file.'
    )
    parser.add_argument('infile', metavar='infile.json',
                        help='The file to convert or "-" to read from stdin.')
    parser.add_argument('-o', '--output', required=False, metavar='output.csv',
                        help='The file to write to or "-" to write to stdout. If not specified the input filename '
                             '(with .csv) or stdout will be used.',)
    parser.add_argument('--start', required=False, metavar='YYYY-MM-DD', type=_parse_date,
                        help='Limit export to calls on or after specified date.')
    parser.add_argument('--stop', required=False, metavar='YYYY-MM-DD', type=_parse_date,
                        help='Limit export to calls until (including) specified date.')
    args = parser.parse_args()
    output = args.output

    if args.infile == '-':
        infile = sys.stdin
    else:
        if not output:
            output = args.infile.rsplit('.', 1)[0] + '.csv'
        infile = Path(args.infile)

    if not output or output == '-':
        output = sys.stdout
    else:
        output = Path(output)

    PhoneCall.convert_to_csv(infile, output=output, start_date=args.start, stop_date=args.stop)
