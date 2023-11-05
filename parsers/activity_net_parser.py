import json
import os
import jsonpickle

from models.taxonomy import Taxonomy

class ActivityNetParser:
    """
    This class is responsible for parsing csv data into the ActivityNet format.
    It provides methods to parse annotations from the data, get the taxonomy filename, and write the parsed data into a JSON file.
    """

    def __init__(self, output_file: str, data):
        self.output_file = output_file
        self.annotation = {
            'database': {},
            'version': 'VERSION 1.0',
            'taxonomy': []
        }
        self.taxonomy = Taxonomy(data).get()
        self._parse_annotation(data)

    def _parse_annotation(self, data):
        for item in data:
            basename, _ = os.path.splitext(item.filename)

            if basename in self.annotation['database']:
                self.annotation['database'][basename].annotations.append(
                    item.annotations[0])
            else:
                self.annotation['database'][basename] = item

    def _get_taxonomy_filename(self):
        dirname, basename = os.path.split(self.output_file)

        return os.path.join(dirname, 'taxonomy.json')

    def _write_json_file(self, filename, data):
        try:
            with open(filename, "w") as json_file:
                json_data = jsonpickle.encode(
                    data, unpicklable=False, make_refs=False)
                json_file.write(json_data)
            print(f"JSON data written to {filename}")
        except Exception as e:
            print(f"Error writing JSON data: {str(e)}")

    def write_json_data(self):
        folder_path, _ = os.path.split(self.output_file)
        os.makedirs(folder_path, exist_ok=True)

        self._write_json_file(self.output_file, self.annotation)
        taxonomy_name = self._get_taxonomy_filename()
        self._write_json_file(taxonomy_name, self.taxonomy)
