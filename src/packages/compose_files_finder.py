import os
import re

from src.packages.compose_file_names_validator import ComposeFileNamesValidator
from src.packages.compose_files_sorter import ComposeFilesSorter


class ComposeFilesFinder:
    files = []

    def __init__(self, directory, environment, exclude):
        validator = ComposeFileNamesValidator(environment)

        for directory_path, sub_directories_paths, files_names in os.walk(directory):
            for file_name in files_names:
                file_path = f"{directory_path}/{file_name}"
                if validator.validate(file_name) and not re.search(exclude, file_path):
                    self.files.append(file_path.replace(directory + "/", ""))

        ComposeFilesSorter().sort(self.files)

    def get_files_as_raw(self):
        return ":".join(self.files)
