import json
import re
from datetime import datetime
from typing import Any, Dict, List, Optional, Pattern

import pandas as pd
from tqdm import tqdm


def to_snake_case(text: str) -> str:
    """Convert text to snake_case."""
    # Replace spaces and hyphens with underscores
    s1 = re.sub(r"[\s-]", "_", text)
    # Add underscore between camelCase
    s2 = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", s1)
    # Convert to lowercase
    return s2.lower()


def parse_data(data: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
    flights: List[Dict[str, Any]] = []
    flight_pattern: Pattern = re.compile(
        r"Registration: ([^\n]*?)\s+ICAO ID: ([^\n]*?)\s+ATSU Adress: ([^\n]*?)\n"
        r"Channel Frequency: ([^\n]*?)\n(.*?)CRC: ([^\n]*?)(?=\n\n|$)",
        re.DOTALL,
    )

    # Count total matches first for the progress bar
    matches = list(flight_pattern.finditer(data))
    total_flights = min(len(matches), limit) if limit else len(matches)

    for match in tqdm(
        matches[:limit] if limit else matches,
        total=total_flights,
        desc="Processing flights",
    ):
        icao_id = match.group(2).strip()

        # Skip if ICAO ID is not exactly 6 characters
        if len(icao_id) != 6:
            continue

        flight: Dict[str, Any] = {
            "registration": match.group(1).strip(),
            "icao_id": icao_id,
            "atsu_address": match.group(3).strip(),
            "channel_frequency": match.group(4).strip(),
            "tags": [],
            "crc": match.group(6).strip(),
        }

        tags_data: List[str] = match.group(5).strip().split("\n")
        current_tag: Optional[Dict[str, Any]] = None

        for line in tags_data:
            if line.startswith("Tag "):
                if current_tag:
                    flight["tags"].append(current_tag)

                tag_match = re.match(r"Tag (\d+) (.*?): (.*?)$", line)
                if tag_match:
                    current_tag = {
                        "tag_number": int(tag_match.group(1)),
                        "tag_type": tag_match.group(2).strip(),
                        "tag_value": tag_match.group(3).strip(),
                        "details": {},
                    }
            elif line.strip() and current_tag:  # Detail line
                detail_match = re.match(r"\s+(.*?): (.*?)$", line)
                if detail_match:
                    key = to_snake_case(detail_match.group(1).strip())
                    value = detail_match.group(2).strip()
                    if key == "timestamp":
                        try:
                            value = (
                                datetime.strptime(value, "%Y-%m-%d %H:%M:%S.%f")
                                .replace(tzinfo=datetime.timezone.utc)
                                .isoformat()
                            )
                        except ValueError:
                            pass  # Keep original value if parsing fails
                    current_tag["details"][key] = value

        # Don't forget to append the last tag
        if current_tag:
            flight["tags"].append(current_tag)

        flights.append(flight)
    return flights


def read_data(file_path: str, limit: Optional[int] = None) -> str:
    """Read complete file or only enough lines based on limit."""
    if not limit:
        with open(file_path, "r") as f:
            return f.read()

    estimated_lines = limit * 40  # Assuming each flight block is around 40 lines
    lines = []
    with open(file_path, "r") as f:
        for _ in range(estimated_lines):
            line = f.readline()
            if not line:
                break
            lines.append(line)

    return "".join(lines)


def save_output(data: List[Dict[str, Any]], output_file: str) -> None:
    """Save parsed data in the format determined by file extension."""
    extension = output_file.lower().split(".")[-1]
    print(f"Saving results in {extension.upper()} format...")

    if extension == "json":
        with open(output_file, "w") as f:
            json.dump(data, f, indent=2)

    elif extension == "jsonl":
        with open(output_file, "w") as f:
            for flight in data:
                f.write(json.dumps(flight, separators=(",", ":")) + "\n")

    elif extension == "csv":
        # Flatten the nested structure for CSV
        flattened_data = []
        for flight in data:
            base_info = {
                "registration": flight["registration"],
                "icao_id": flight["icao_id"],
                "atsu_address": flight["atsu_address"],
                "channel_frequency": flight["channel_frequency"],
                "crc": flight["crc"],
            }

            for tag in flight["tags"]:
                row = base_info.copy()
                row.update(
                    {
                        "tag_number": tag["tag_number"],
                        "tag_type": tag["tag_type"],
                        "tag_value": tag["tag_value"],
                    }
                )
                # Add all details as separate columns
                for key, value in tag["details"].items():
                    row[key] = value
                flattened_data.append(row)

        df = pd.DataFrame(flattened_data)
        df.to_csv(output_file, index=False)
    else:
        raise ValueError(f"Unsupported file extension: {extension}")
