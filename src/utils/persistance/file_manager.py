import json
from pathlib import Path


class FileManager:
    def __init__(self, directory="data"):
        self.directory = Path(directory)
        self.directory.mkdir(exist_ok=True)

    def file_exists(self, filename: str) -> bool:
        """ Check if a file exists. """
        return (self.directory / filename).exists()

    def load_file(self, filename: str, default=None) -> dict:
        """ Load JSON data from a file. """
        file_path = self.directory / filename
        if file_path.exists():
            with open(file_path, "r") as file:
                return json.load(file)
        return default

    def save_file(self, filename: str, data: dict):
        """ Save JSON data to a file. """
        file_path = self.directory / filename
        with file_path.open("w") as file:
            json.dump(data, file, indent=4)

    def delete_file(self, filename: str):
        """ Delete a file. """
        file_path = self.directory / filename
        if file_path.exists():
            file_path.unlink()
