"""Module responsible for dumping data to different formats."""

import abc
import csv
import json
from typing import List

FIELDNAMES = [
    "id",
    "title",
    "location",
    "risk_rating",
    "cvss_v3_vector",
    "short_description",
    "description",
    "recommendation",
    "references",
    "technical_detail",
]


class VulnzDumper(abc.ABC):
    """Dumper Base class: All dumpers should inherit from this class to access the dump method."""

    def __init__(self, output_path: str) -> None:
        """Constructs all the necessary attributes for the object.

        Args:
            output_path: path to the output file.
            data: dictionary, with vulnerability id as a key,
                  and a dictionary of the vulnerability information as values.

        Returns:
            None
        """
        self.output_path: str = output_path

    @abc.abstractmethod
    def dump(self, data: List[object]) -> None:
        """Dump the vulnerabilities in the right format."""
        raise NotImplementedError("Missing implementation")


class VulnzJsonDumper(VulnzDumper):
    """Vulnerability dumper to json."""

    def dump(self, data: List[object]) -> None:
        """Dump vulnerabilities to json file.

        Raises:
            FileNotFoundError: in case the path or file name are invalid.
        """
        if not self.output_path.endswith(".jsonl"):
            self.output_path += ".jsonl"
        with open(self.output_path, "a", encoding="utf-8") as f:
            for item in data:
                f.write(json.dumps(item) + "\n")


class VulnzCsvDumper(VulnzDumper):
    """Vulnerability dumper to csv."""

    def dump(self, data: List[object]) -> None:
        """Dump vulnerabilities to csv file.

        Raises:
            FileNotFoundError: in case the path or file name are invalid.
        """
        if not self.output_path.endswith(".csv"):
            self.output_path += ".csv"
        with open(self.output_path, "a", encoding="utf-8") as outfile:
            csv_writer = csv.DictWriter(outfile, fieldnames=FIELDNAMES)
            csv_writer.writeheader()
            for item in data:
                csv_writer.writerow(item)
