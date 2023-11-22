# Android Call Log Converter

A simple python tool to parse and convert call logs exported from an android device with 
[SMS Import / Export](https://github.com/tmo1/sms-ie) to csv.

It can also be used for just parsing the json format into a Python data structure.

# Usage

## As a command line tool


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
