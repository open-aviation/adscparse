from typing import Any, Dict, List, Optional

import click

from .parser import parse_data, read_data, save_output


@click.command()
@click.argument("input_file", type=click.Path(exists=True))
@click.argument("output_file", type=click.Path())
@click.option("--limit", type=int, help="Limit the number of flight blocks to process")
def main(input_file: str, output_file: str, limit: Optional[int]) -> None:
    """
    Parse ADSC data from INPUT_FILE and save to OUTPUT_FILE
    in format based on extension.
    """

    print(f"Reading data{f' (estimated {limit * 40} lines)' if limit else ''}...")
    data: str = read_data(input_file, limit)

    print(f"Starting to parse data{f' (first {limit} blocks)' if limit else ''}...")
    parsed_data: List[Dict[str, Any]] = parse_data(data, limit)

    save_output(parsed_data, output_file)
    print(f"Data parsed and saved to {output_file}")


if __name__ == "__main__":
    main()
