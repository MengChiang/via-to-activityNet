import argparse
from utils.csv_reader import ViaCSVReader
from utils.video_extractor import VideoExtractor

from models.annotation import Annotation

from parsers.activity_net_parser import ActivityNetParser


def main(csv_folder: str, video_folder: str, output_filepath: str):
    """
    This is the main function that orchestrates the process of reading CSV files from VIA Annotation Tool,
    extracting video information, creating annotations, parsing the data into the ActivityNet format,
    and writing the data into a JSON file.

    Parameters:
    csv_folder (str): The path to the folder containing the CSV files.
    video_folder (str): The path to the folder containing the video files.
    output_filepath (str): The path to the output file.
    """

    # Initialize an empty list to store the annotations
    csv_annotations = []

    # Iterate over the data in the CSV files
    for parent_label, filename, label, coordinates in ViaCSVReader(csv_folder):

        # Create a VideoExtractor object and get the video information
        video_extractor = VideoExtractor(video_folder, filename)
        video_info = video_extractor.get_info()

        # Create an Annotation object and add it to the list of annotations
        annotation = Annotation(parent_label, filename, label, coordinates, video_info)
        csv_annotations.append(annotation)

    # If there are any annotations, parse them into the ActivityNet format and write them to a JSON file
    if len(csv_annotations) > 0:
        parser = ActivityNetParser(output_filepath, csv_annotations)
        parser.write_json_data()
    else:
        print("No annotation data found or an error occurred.")


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--csv-folder', default='./annotations',
                        help='Path to the folder containing CSV files.')
    parser.add_argument('--video-folder', default='./videos',
                        help='Path to the folder containing video files.')
    parser.add_argument('--output-file', default='./output/annotation.json',
                        help='Path to the folder for storing output files.')

    args = parser.parse_args()

    main(args.csv_folder, args.video_folder, args.output_file)
