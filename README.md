# Parser for OpenSky ADS-C files

A Python tool for parsing ADS-C text files from the OpenSky Network: <https://zenodo.org/records/13919610>

## Installation

Then install the package:

```bash
pip install git+https://github.com/open-aviation/adscparse 
```

## Usage

```bash
adscparse INPUT_FILE OUTPUT_FILE [--limit N]
```

### Arguments
- `INPUT_FILE`: Path to the input ADSC data file
- `OUTPUT_FILE`: Path for the output file (supports .json, .jsonl, and .csv formats)
- `--limit`: Optional parameter to limit the number of flight blocks to process for testing purposes
