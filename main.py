import csv
import argparse
import os
import jsonpickle
from io import StringIO
from moviepy.editor import VideoFileClip


class ViaCSVReader:
    def __init__(self, csv_folder):
        self.data = []
        self.read(csv_folder)

    def read(self, csv_folder):
        for csv_file in self.get_csv_list(csv_folder):
            for row in csv.DictReader(StringIO(self.process_csv_header(csv_file))):
                file_name = jsonpickle.decode(row['file_list'])[0]
                label = jsonpickle.decode(row['metadata'])['1']
                temporal_coordinates = jsonpickle.decode(
                    row['temporal_coordinates'])

                self.data.append((file_name, label, temporal_coordinates))

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


class ActivityNetParser:
    def __init__(self, output_file, data):
        self.output_file = output_file
        self.annotation = {
            'database': {},
            'version': "VERSION 1.0",
            'taxonomy': []
        }
        self._parse_annotation(data)

    def _parse_annotation(self, data):
        for item in data:
            basename, _ = os.path.splitext(item.filename)
            self.annotation['database'][basename] = item

            if basename in self.annotation['database']:
                self.annotation['database'][basename].annotations.append(
                    item.annotations[0])
            else:
                self.annotation['database'][basename] = item

    def write_json_data(self):
        try:
            folder_path, _ = os.path.split(self.output_file)
            os.makedirs(folder_path, exist_ok=True)

            with open(self.output_file, "w") as json_file:
                json_data = jsonpickle.encode(
                    self.annotation, unpicklable=False, make_refs=False)
                json_file.write(json_data)
            print(f"JSON data written to {self.output_file}")
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
    def __init__(self, filename, label, temporal_coordinates, video_info):
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
    csv_data = []

    for filename, label, coordinates in ViaCSVReader(csv_folder):
        video_extractor = VideoExtractor(video_folder, filename)
        csv_data.append(Annotation(
            filename, label, coordinates, video_extractor.get_info()))

    if len(csv_data) > 0:
        parser = ActivityNetParser(output_filepath, csv_data)
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
