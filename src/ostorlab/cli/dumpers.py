"""Module responsible for dumping data to different formats."""

import abc
import json
import csv
from typing import Dict


FIELDNAMES = ['id', 'title', 'risk_rating', 'cvss_v3_vector', 'short_description']


class VulnzDumper(abc.ABC):
    """Dumper Base class: All dumpers should inherit from this class to access the dump method."""

    def __init__(self, output_path: str, data: Dict[str, Dict]) -> None:
        """Constructs all the necessary attributes for the object.

        Args:
            output_path: path to the output file.
            data: dictionary, with vulnerability id as a key,
                  and a dictionary of the vulnerability information as values.

        Returns:
            None
        """
        self.output_path = output_path
        self.data = data

    @abc.abstractmethod
    def dump(self) -> None:
        """Dump the vulnerabilities in the right format."""
        raise NotImplementedError('Missing implementation')


class VulnzJsonDumper(VulnzDumper):
    """Vulnerability dumper to json."""

    def dump(self) -> None:
        """Dump vulnerabilities to json file.

        Raises:
            FileNotFoundError: in case the path or file name are invalid.
        """
        if not self.output_path.endswith('.json'):
            self.output_path+= '.json'
        with open(self.output_path , 'w', encoding='utf-8') as outfile:
            json.dump(self.data, outfile)


class VulnzCsvDumper(VulnzDumper):
    """Vulnerability dumper to csv."""

    def dump(self) -> None:
        """Dump vulnerabilities to csv file.

        Raises:
            FileNotFoundError: in case the path or file name are invalid.
        """
        if not self.output_path.endswith('.csv'):
            self.output_path+= '.csv'
        with open(self.output_path , 'w', encoding='utf-8') as outfile:
            csv_writer = csv.DictWriter(outfile, fieldnames = FIELDNAMES)
            csv_writer.writeheader()
            for key in self.data:
                csv_writer.writerow({field: self.data[key].get(field) or key for field in FIELDNAMES})
        