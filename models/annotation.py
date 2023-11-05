class Annotation:
    """
    This class is responsible for creating an annotation from given parameters.
    It provides methods to get the duration, resolution, URL, subset, and annotations of a video file.
    """

    def __init__(self, parent_label: str, filename: str, label: str, coordinates: list, video_info: tuple):
        self.parent_label = parent_label
        self.filename = filename
        self.label = label
        self.coordinates = coordinates
        self.duration = video_info[0] if video_info is not None else 0
        self.resolution = video_info[1] if video_info is not None else ''
        self.url = video_info[2] if video_info is not None else ''
        self.subset = 'training'
        self.annotations = self._get_annotations()

    def _get_annotations(self):
        return [{
            'segment': coordinate * self.duration,
            'label': self.label
        } for coordinate in self.coordinates]
