"""Module responsible for dumping data to different formats."""

import abc
import json
import csv


class Dumper(abc.ABC):
    """Dumper Base class: All dumpers should inherit from this class to access the dump method."""

    def __init__(self, output_path, data):
        """Initializer."""
        self.output_path = output_path
        self.data = data

    @abc.abstractmethod
    def dump(self):
        """Dump data."""
        raise NotImplementedError('Missing implementation')

class VulnzJsonDumper(Dumper):
    """Vulnerability dumper to json."""

    def dump(self):
        """Dump vulnerabilities to json file."""
        try:
            if self.output_path.endswith('.json'):
                self.output_path+= '.json'
            with open(self.output_path , 'w', encoding='utf-8') as outfile:
                json.dump(self.data, outfile)

        except FileNotFoundError as e:
            raise e


class VulnzCsvDumper(Dumper):
    """Vulnerability dumper to csv."""
    def __init__(self, output_path, data, fieldnames):
        """Initializer."""
        super().__init__(output_path, data)
        self.fieldnames = fieldnames

    def dump(self):
        """Dump vulnerabilities to csv file."""
        try:
            if self.output_path[-4:] != '.csv':
                self.output_path+= '.csv'
            with open(self.output_path , 'w', encoding='utf-8') as outfile:
                csv_writer = csv.DictWriter(outfile, fieldnames = self.fieldnames)
                csv_writer.writeheader()
                csv_writer.writerows(self.data['vulnerabilities'])
        except FileNotFoundError as e:
            raise e
