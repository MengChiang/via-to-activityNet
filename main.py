import csv
import json
import os
import argparse
import logging
from moviepy.editor import VideoFileClip


CSV_HEADER_PREFIX = "# CSV_HEADER = "
# Define a function to copy a file while removing lines with '#' and a specific prefix.
# This function takes the 'folder_path', 'base_name', and 'extension' of the file to be copied.
# It reads the original file, removes lines starting with '#' and a specific prefix, and creates a new temporary file.
# Parameters:
#   - folder_path: The path to the folder containing the original file.
#   - base_name: The base name of the original file.
#   - extension: The file extension (including the dot) of the original file.
# Returns:
#   - The path to the newly created temporary file.
def copy_file_without_header_comment(filename):
    
    base_name, extension = os.path.splitext(filename)
    new_file_name = base_name + '_temp' + extension

    try:
        with open(filename, 'r') as original_file:
            modified_lines = [line.replace(CSV_HEADER_PREFIX, '')
                              for line in original_file.readlines()
                              if not line.startswith('#') or 'CSV_HEADER' in line]

        with open(new_file_name, 'w') as new_file:
            new_file.writelines(modified_lines)

            return new_file_name
    except FileNotFoundError:
        print(f'Error: File not found - {filename}')
        return None
    except Exception as e:
        print(f'Error: {e}')
        return None


# Define a function to read data from a CSV file and populate an annotation list.
# This function takes a CSV file name and an annotation list as input. It processes each row in the CSV file,
# extracts relevant information, and adds it to the annotation list in a structured format.
# Parameters:
#   - csv_name: The name of the CSV file containing video annotations.
#   - annotation_list: A dictionary to store video annotations.
def update_annotation_list_from_csv(csv_name, video_folder, annotation_list):
    # Define initial annotation template for videos
    annotation_template = {
        'annotations': [],
        'duration': 0.0,
        'resolution': '',
        'subset': '',
        'url': ''
    }
    sub_annotation_template = {'label': '', 'segment': []}

    # taxonomy = json.loads

    # Open and read the CSV file
    with open(csv_name, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            file_name, extension = os.path.splitext(
                json.loads(row['file_list'])[0])

            temporal_coordinates = json.loads(row['temporal_coordinates'])
            label = json.loads(row['metadata'])['1']
            label_id = row['metadata_id']

            # Create a new annotation object for the video
            sub_annotation = sub_annotation_template.copy()
            sub_annotation['label'] = label
            sub_annotation['segment'] = temporal_coordinates

            # If the video file is not already in the annotation list, add it
            if file_name not in annotation_list:
                annotation_list[file_name] = annotation_template

            # Update the annotation information for the video
            annotation_list[file_name]['annotations'].append(sub_annotation)
            annotation_list[file_name]['subset'] = 'training'
            
            if video_folder is not None:
                 # Get the video URL and extract its duration and resolution
                video_url = get_video_url(file_name + extension, video_folder)
                duration, resolution = get_video_info(video_url)
                
                annotation_list[file_name]['duration'] = duration
                annotation_list[file_name]['resolution'] = resolution
                annotation_list[file_name]['url'] = video_url
            
           


# Define a function to retrieve video information, including duration and resolution.
# This function attempts to open the video file specified by 'file_path' using the 'VideoFileClip' class from a video processing library.
# It then extracts the video's duration and resolution and returns them as a tuple.
# In case of any exceptions during video processing, an error message is printed, and None values are returned.
# Parameters:
#   - file_path: The path to the video file to be analyzed.
# Returns:
#   - A tuple containing the video's duration (in seconds) and resolution (as a tuple of width and height).
#     If an error occurs, None values are returned.
def get_video_info(file_path):
    try:
        video = VideoFileClip(file_path)
        duration = video.duration
        resolution = video.size
        return duration, resolution
    except Exception as e:
        print(f"Error: {e}")
        return None, None

# Define a function to generate a file URL based on the given file name.
# This function first obtains the current working directory and then gets the parent directory.
# It combines the parent directory and the provided file name using os.path.join() to create the file's URL.
# Parameters:
#   - file_name: The name of the file to be included in the URL.
# Returns:
#   - The URL of the file, which includes the parent directory and the specified file name.


def get_video_url(file_name, video_folder=None):
    base_path = os.getcwd() if video_folder is None else video_folder

    return os.path.join(base_path, file_name)


def process_annotation_files(annotation_folder, output_folder, video_folder=None):
    try:
        annotation_list = {}
        
        annotation_files = [os.path.join(annotation_folder, filename)
                            for filename in os.listdir(annotation_folder)
                            if filename.endswith('.csv')]

        for annotation_file in annotation_files:
            temp_file_path = copy_file_without_header_comment(annotation_file)
            update_annotation_list_from_csv(temp_file_path, video_folder, annotation_list)
            os.remove(temp_file_path)

        return annotation_list

    except Exception as e:
        logging.error(f'An error occurred: {e}')

# Define the main function
def main(annotation_folder, output_folder, video_folder=None):
    annotation_list = process_annotation_files(annotation_folder, output_folder, video_folder)
    
    if annotation_list:
        print(annotation_list)
    else:
        print("No annotation data found or an error occurred.")

# Entry point of the script
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--annotation-folder', default='./annotations',
                        help='Path to the folder containing CSV files.')
    parser.add_argument('--output-folder', default='./output',
                        help='Path to the folder for storing output files.')
    parser.add_argument('--video-folder', default=None,
                        help='Path to the folder containing video files.')

    args = parser.parse_args()
    main(args.annotation_folder, args.output_folder, args.video_folder)
