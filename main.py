import csv
import argparse
import os
import jsonpickle
from io import StringIO
from moviepy.editor import VideoFileClip
import re


class LabelProcessor:
    def __init__(self):
        pass

    @staticmethod
    def get_filename_label(file_name):
        file_name = os.path.basename(file_name)
        pattern = r'VID_\d{8}_\d{6}_\d{1}_\d{2}_(.*?)\.csv'
        match = re.search(pattern, file_name)
        if match:
            group = match.group(1)
            label_name = re.sub(r'\(\d+\)', '', group)
            return label_name


class ViaCSVReader:
    def __init__(self, csv_folder):
        self.data = []
        self.read(csv_folder)

    def read(self, csv_folder):
        for csv_file in self.get_csv_list(csv_folder):
            for row in csv.DictReader(StringIO(self.process_csv_header(csv_file))):
                parent_label = LabelProcessor.get_filename_label(csv_file)
                file_name = jsonpickle.decode(row['file_list'])[0]
                label = jsonpickle.decode(row['metadata'])['1']
                temporal_coordinates = jsonpickle.decode(
                    row['temporal_coordinates'])

                self.data.append(
                    (parent_label, file_name, label, temporal_coordinates))

    def get_csv_list(self, csv_folder):
        return [os.path.join(csv_folder, filename)
                for filename in os.listdir(csv_folder)
                if filename.endswith('.csv')]

    def process_csv_header(self, filename):
        try:
            with open(filename, 'r') as original_file:
                modified_text = '\n'.join(line.replace('# CSV_HEADER = ', '')
                                          for line in original_file.readlines()
                                          if not (line.startswith('#') and 'CSV_HEADER' not in line))

                return modified_text
        except FileNotFoundError:
            print(f'Error: File not found - {filename}')
            return None
        except Exception as e:
            print(f'Error: {e}')
            return None

    def __getitem__(self, index):
        return self.data[index]


class Taxonomy:
    def __init__(self, labels):
        self.labels = labels
        self.nodes = []

        self.convert()

    def _create_node(self, nodeName, parentName=None, parentId=None):
        return {
            'parentName': parentName,
            'nodeName': nodeName,
            'nodeId': len(self.nodes),
            'parentId': parentId
        }

    def _find_node(self, node_name):
        for node in self.nodes:
            if node['nodeName'] == node_name:
                return (node['nodeId'], node['nodeName'])
        return None

    def convert(self):
        self.nodes.append(self._create_node('Root'))

        parent_id = 1

        second_node_names = {label.parent_label for label in self.labels}

        for second_node_name in second_node_names:
            self.nodes.append(self._create_node(
                second_node_name, 'Root', parent_id))

        for label in self.labels:
            parent_id, parent_name = self._find_node(label.parent_label)
            for annotation in label.annotations:
                self.nodes.append(self._create_node(
                    annotation['label'], parent_id, parent_name)
                )

    def get(self):
        return self.nodes


class ActivityNetParser:
    def __init__(self, output_file, data):
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
        name, extension = os.path.splitext(basename)

        new_name = name.replace(name, 'taxonomy')
        return os.path.join(dirname, new_name + extension)

    def write_json_data(self):
        try:
            folder_path, _ = os.path.split(self.output_file)
            os.makedirs(folder_path, exist_ok=True)

            with open(self.output_file, "w") as json_file:
                json_data = jsonpickle.encode(
                    self.annotation, unpicklable=False, make_refs=False)
                json_file.write(json_data)
            print(f"JSON data written to {self.output_file}")

            taxonomy_name = self._get_taxonomy_filename()

            with open(taxonomy_name, "w") as json_file:
                json_data = jsonpickle.encode(
                    self.taxonomy, unpicklable=False, make_refs=False)
                json_file.write(json_data)
            print(f"JSON data written to {taxonomy_name}")

        except Exception as e:
            print(f"Error writing JSON data: {str(e)}")


class VideoExtractor:
    def __init__(self, folder, filename):
        self.folder = folder
        self.filename = filename

    def get_info(self):
        try:
            url = os.path.join(self.folder or os.getcwd(), self.filename)
            if os.path.exists(url):
                video = VideoFileClip(url)
                return (video.duration, video.size, url)
            else:
                return None
        except Exception as e:
            print(f"Error: {e}")
            return None


class Annotation:
    def __init__(self, parent_label, filename, label, temporal_coordinates, video_info):
        self.parent_label = parent_label
        self.filename = filename
        self.annotations = []
        self.duration = video_info[0] if video_info is not None else 0
        self.resolution = video_info[1] if video_info is not None else ''
        self.url = video_info[2] if video_info is not None else ''
        self.subset = 'training'

        self._add_label_segment(label, temporal_coordinates)

    def _add_label_segment(self, label, temporal_coordinates):
        self.annotations.append(
            {'label': label, 'segment': temporal_coordinates})


def main(csv_folder, video_folder, output_filepath):
    csv_annotations = []

    for parent_label, filename, label, coordinates in ViaCSVReader(csv_folder):
        video_extractor = VideoExtractor(video_folder, filename)
        csv_annotations.append(Annotation(
            parent_label, filename, label, coordinates, video_extractor.get_info()))

    if len(csv_annotations) > 0:
        parser = ActivityNetParser(output_filepath, csv_annotations)
        parser.write_json_data()
    else:
        print("No annotation data found or an error occurred.")


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--csv-folder', default='./annotations',
                        help='Path to the folder containing CSV files.')
    parser.add_argument('--video-folder', default=None,
                        help='Path to the folder containing video files.')
    parser.add_argument('--output-file', default='./output/annotation.json',
                        help='Path to the folder for storing output files.')

    args = parser.parse_args()

    main(args.csv_folder, args.video_folder, args.output_file)
