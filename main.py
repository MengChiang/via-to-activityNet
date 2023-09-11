import csv
import json
import os



def main():
    folder_path = './annotations'

    file_list = os.listdir(folder_path)
    for filename in file_list:
        base_name, extension = os.path.splitext(filename)
        if extension == '.csv':
            copy_file_path = copyfile_without_prefix(
                folder_path, base_name, extension)
            via_csv_reader(copy_file_path)
            os.remove(copy_file_path)


def copyfile_without_prefix(folder_path, base_name, extension):
    file_path = os.path.join(folder_path, base_name + extension)
    copy_file_path = os.path.join(folder_path, base_name + '_temp' + extension)

    modified_lines = []
    with open(file_path, newline='') as oringal_file:
        modified_lines = [line.replace('# CSV_HEADER = ', '')
                          for line in oringal_file.readlines()]
        modified_lines = list(filter(lambda line: '#' not in line, modified_lines))

    with open(copy_file_path, 'w') as new_file:
        new_file.writelines(modified_lines)

    return copy_file_path


def via_csv_reader(csv_name):
    annotation_list = {}
    annotation_obj = {'annotations': [], 'duraction': 0.0,
                      'resolution': '', 'subset': '', 'url': ''}
    label_obj = {'label': '', 'segment': []}

    with open(csv_name, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            file_name = json.loads(row['file_list'])[0]
            temporal_coordinates = json.loads(row['temporal_coordinates'])
            label = json.loads(row['metadata'])['1']
            label_id = row['metadata_id']
            
            csv_obj = label_obj.copy()
            csv_obj['label'] = label
            csv_obj['segment'].add(temporal_coordinates)

            if file_name not in annotation_list:
                annotation_list[file_name].add(file_name, annotation_obj)

            annotation_list[file_name]['annotations'].add(csv_obj)


if __name__ == '__main__':
    main()
