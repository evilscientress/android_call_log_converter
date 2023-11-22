# Android Call Log Converter

A simple python tool to parse and convert call logs exported from an android device with 
[SMS Import / Export](https://github.com/tmo1/sms-ie) to csv.

It can also be used for just parsing the json format into a Python data structure.

## Usage

### As a command line tool


```shell
python -m call_log_converter calls-2023-11-22.json
```

There are a buch of optional command line arguments available, you can display the help with `-h`.

```
usage: python -m call_log_converter [-h] [-o output.csv] [--start YYYY-MM-DD] [--stop YYYY-MM-DD] infile.json

Converts a call log exported from a Android phone in json format to a csv file.

positional arguments:
  infile.json           The file to convert or "-" to read from stdin.

options:
  -h, --help            show this help message and exit
  -o output.csv, --output output.csv
                        The file to write to or "-" to write to stdout.
                        If not specified the input filename (with .csv) or stdout will be used.
  --start YYYY-MM-DD    Limit export to calls on or after specified date.
  --stop YYYY-MM-DD     Limit export to calls until (including) specified date.

```


### As a python package

#### To parse a json export into a Python data structure

```python
import json
from call_log_converter import PhoneCall
   
with open('calls-2023-11-22.json', 'r') as fp:
    calls = json.load(fp)
calls = PhoneCall.from_json(calls)
```
`calls` is now a list of `PhoneCall` objects.


#### To convert a json export into a csv file

```python
from pathlib import Path
from call_log_converter import PhoneCall

infile = Path('calls-2023-11-22.json')
output = Path('calls-2023-11-22.csv')
PhoneCall.convert_to_csv(infile, output)
```

The `infile` and `output` can either be a PathLike object for them to be treated as files, or a file like object.  
The `infile` additionally can also be a string, in which case it is directly parsed as json.  
If `output` is omitted the method returns the generated csv as a string.

The method also accepts two optional parameters `start_date` and `stop_date` which can be used to filter the data.
They can be either a [`date`](https://docs.python.org/3/library/datetime.html#datetime.date)
or [`datetime`](https://docs.python.org/3/library/datetime.html#datetime.datime) object.
