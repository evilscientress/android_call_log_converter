import csv
import dataclasses
import sys
from argparse import ArgumentParser
from collections.abc import Iterable, Sequence
from contextlib import nullcontext
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from enum import Enum, Flag, IntEnum, IntFlag, UNIQUE, verify
from io import StringIO
from os import PathLike
from pathlib import Path
from typing import Self, TypeVar, ClassVar, TextIO
import json
import pytz


tz = pytz.timezone('Europe/Vienna')

T = TypeVar('T')


class PrettyEnum(Enum):
    def __str__(self):
        if not self.name:
            return str(self.value)
        return ' '.join(w.capitalize() for w in self.name.replace('_', ' ').split(' '))


class PrettyFlag(Flag):
    def __str__(self):
        if self.value == 0:
            return ''
        if not self.name:
            return str(self.value)
        return ' '.join(w.capitalize() for w in self.name.replace('|', ', ').replace('_', ' ').split(' '))


@verify(UNIQUE)
class CallType(PrettyEnum, IntEnum):
    INCOMING = 1
    OUTGOING = 2
    MISSED = 3
    VOICEMAIL = 4
    REJECTED = 5
    BLOCKED = 6
    ANSWERED_EXTERNALLY = 7


@verify(UNIQUE)
class NumberType(PrettyEnum, IntEnum):
    _ = 0
    HOME = 1
    MOBILE = 2
    WORK = 3
    FAX_WORK = 4
    FAX_HOME = 5
    PAGER = 6
    OTHER = 7
    CALLBACK = 8
    CAR = 9
    COMPANY_MAIN = 10
    ISDN = 11
    MAIN = 12
    OTHER_FAX = 13
    RADIO = 14
    TELEX = 15
    TTY_TDD = 16
    WORK_MOBILE = 17
    WORK_PAGER = 18
    ASSISTANT = 19
    MMS = 20

    def __str__(self):
        if self.value == 0:
            return ''
        return super().__str__()


@verify(UNIQUE)
class MissedReason(PrettyFlag, IntFlag):
    NOT_MISSED = 0
    # Call was automatically rejected by system because an ongoing emergency call.
    AUTO_MISSED_EMERGENCY_CALL = 1
    # Call was automatically rejected by system because the system cannot support any more ringing calls.
    AUTO_MISSED_MAXIMUM_RINGING = 2
    # Call was automatically rejected by system because the system cannot support any more dialing calls.
    AUTO_MISSED_MAXIMUM_DIALING = 4
    # Bit is set when the call was missed just because user didn't answer it.
    USER_MISSED_NO_ANSWER = 0x0000000000010000
    # Bit is set when this call rang for a short period of time.
    USER_MISSED_SHORT_RING = 0x0000000000020000
    # Bit is set when this call is silenced because the phone is in 'do not disturb mode'.
    USER_MISSED_DND_MODE = 0x0000000000040000
    # Bit is set when this call rings with a low ring volume.
    USER_MISSED_LOW_RING_VOLUME = 0x0000000000080000
    # When CallLog.Calls#TYPE is CallLog.Calls#MISSED_TYPE set this bit when this call rings without vibration.
    USER_MISSED_NO_VIBRATE = 0x0000000000100000
    # Bit is set when this call is silenced by the call screening service.
    USER_MISSED_CALL_SCREENING_SERVICE_SILENCED = 0x0000000000200000
    # Bit is set when the call filters timed out.
    USER_MISSED_CALL_FILTERS_TIMEOUT = 0x0000000000400000


@verify(UNIQUE)
class BlockedReason(PrettyEnum, IntEnum):
    NOT_BLOCKED = 0
    CALL_SCREENING_SERVICE = 1
    DIRECT_TO_VOICEMAIL = 2
    BLOCKED_NUMBER = 3
    UNKNOWN_NUMBER = 4
    RESTRICTED_NUMBER = 5
    PAY_PHONE = 6
    NOT_IN_CONTACTS = 7


@verify(UNIQUE)
class NumberPresentation(PrettyEnum, IntEnum):
    ALLOWED = 1
    RESTRICTED = 2
    UNKNOWN = 3
    PAYPHONE = 4
    UNAVAILABLE = 5


@verify(UNIQUE)
class CallFeatures(PrettyFlag, IntFlag):
    ASSISTED_DIALING_USED = 16
    HD_CALL = 4
    PULLED_EXTERNALLY = 2
    RTT = 32
    VIDEO = 1
    VOLTE = 64
    WIFI = 8

    def __str__(self):
        return (super().__str__()
                .replace('Rtt', 'RTT')
                .replace('Volte', 'VoLTE')
                .replace('Wifi', 'WiFi')
                )


@dataclass(slots=True)
class PhoneCall:
    date: datetime
    phone_account_hidden: bool
    photo_id: int
    subscription_component_name: str
    # The type of the call (incoming, outgoing or missed).
    type: CallType
    # A geocoded location for the number associated with this call.
    presentation: NumberPresentation
    duration: timedelta
    subscription_id: int
    # Whether this item has been read or otherwise consumed by the user.
    is_read: bool
    number: str
    features: CallFeatures
    via_number: str
    # The date the row is last inserted, updated, or marked as deleted, in milliseconds since the epoch.
    last_modified: datetime
    # Whether or not the call has been acknowledged
    new: bool
    # Indicates factors which may have lead the user to miss the call.
    missed_reason: MissedReason
    phone_account_address: str
    add_for_all_users: bool
    block_reason: BlockedReason
    # The priority of the call, as delivered via call composer.
    priority: int
    countryiso: str
    is_call_log_phone_account_migration_pending: bool
    post_dial_digits: str
    transcription_state: bool
    _id: int
    subject: str = None
    matched_number: str = None
    formatted_nummer: str = None
    normalized_number: str = None
    lookup_uri: str = None
    name: str = ""
    display_name: str = ""
    numbertype: NumberType = None
    data_usage: int = None
    geocoded_location: str = ""

    default_csv_fields: ClassVar[Sequence[str]] = (
        'date', 'time', 'type', 'duration', 'number', 'display_name', 'numbertype', 'presentation', 'missed_reason',
        'block_reason', 'features', 'countryiso')

    @classmethod
    def from_json(cls, obj_or_list: dict | Iterable[dict]) -> Self | list[Self]:
        multiple = not isinstance(obj_or_list, dict)
        fields = dataclasses.fields(cls)
        calls = []
        for obj in (obj_or_list if multiple else [obj_or_list]):
            call = {}
            for key, field in ((f.name, f) for f in fields):
                if field.default is not dataclasses.MISSING and key not in obj:
                    continue
                value = obj.pop(key)
                try:
                    if issubclass(field.type, datetime):
                        call[key] = datetime.utcfromtimestamp(int(value)/1000).replace(tzinfo=pytz.UTC).astimezone(tz)
                    elif issubclass(field.type, timedelta):
                        call[key] = timedelta(seconds=int(value))
                    elif issubclass(field.type, Enum) and isinstance(value, str):
                        call[key] = field.type(int(value))
                    elif field.type is bool and isinstance(value, str):
                        call[key] = True if value == "1" else False
                    elif not isinstance(value, field.type):
                        call[key] = field.type(value)
                    else:
                        call[key] = value
                    # ToDo: Complain if stuff is left in obj
                except TypeError:
                    print(f'Failed parsing field {key} for value "{value}".')
                    if multiple:
                        print(f'Call {len(calls) + 1}')
                    raise
            calls.append(cls(**call))

        if multiple:
            return calls
        return calls[0]

    @classmethod
    def csv_header(cls, fields: Sequence[str] = None):
        if fields is None:
            fields = cls.default_csv_fields
        return (' '.join(w.capitalize() for w in (f.replace('_', ' ').split(' '))) for f in fields)

    def csv_row(self, fields: Sequence[str] = None):
        if fields is None:
            fields = self.__class__.default_csv_fields
        out_fields = set(fields)
        call_fields = set((f.name for f in dataclasses.fields(self)))
        csv_aliases = {'time'}

        if not (out_fields - csv_aliases) <= call_fields:
            raise ValueError('Unknown field(s) in list: "%s"' % ', '.join(out_fields - csv_aliases - call_fields))
        row = []
        for field in fields:
            value = getattr(self, field, None)
            match field, value:
                case 'date', _:
                    if 'time' in out_fields:
                        value = self.date.strftime('%d.%m.%Y')
                    else:
                        value = self.date.strftime('%d.%m.%Y %H:%M:%S')
                case 'time', _:
                    value = self.date.strftime('%H:%M:%S')
                case _, datetime():
                    value = value.strftime('%d.%m.%Y %H:%M:%S')
                case _, timedelta():
                    value = str(value).rjust(8, '0')
                case 'formatted_numer', _:
                    if not value:
                        value = self.normalized_number if self.normalized_number else self.number
                case _, bool():
                    value = 'Yes' if value else 'No'
                case _, None:
                    value = ''
                case _:
                    value = str(value)
            row.append(value)

        return row

    @classmethod
    def convert_to_csv(cls, infile: str | PathLike[str] | TextIO, output: PathLike[str] | TextIO | None = None,
                       start_date: date | datetime | None = None, stop_date: date | datetime | None = None,
                       ) -> str | None:
        if isinstance(start_date, date):
            start_date = datetime.combine(start_date, time(), tzinfo=tz)
        if isinstance(stop_date, date):
            stop_date = datetime.combine(stop_date, time(), tzinfo=tz)
        if stop_date:
            stop_date += timedelta(days=1)

        match infile:
            case str():
                calls = json.loads(infile)
            case Path():
                with open(infile, 'r') as fp:
                    calls = json.load(fp)
            case _:
                calls = json.load(infile)

        match output:
            case Path():
                output_io = None
            case None:
                output_io = StringIO(newline='')
            case _:
                output_io = output

        calls = PhoneCall.from_json(calls)

        with (open(output, 'w', newline='') if isinstance(output, Path) else nullcontext(output_io)) as fp:
            writer = csv.writer(fp, dialect=csv.unix_dialect)
            writer.writerow(PhoneCall.csv_header())
            for call in calls:
                if start_date and call.date < start_date:
                    break
                if stop_date and call.date >= stop_date:
                    continue
                writer.writerow(call.csv_row())

        if output is None:
            try:
                return output_io.getvalue()
            finally:
                output_io.close()


def _parse_date(date: str) -> date:
    return datetime.strptime(date, '%Y-%m-%d').date()


if __name__ == '__main__':
    parser = ArgumentParser(
        prog='Android Call Log Converter',
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
