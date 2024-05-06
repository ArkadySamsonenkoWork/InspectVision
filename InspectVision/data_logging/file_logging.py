import typing as tp
import csv
import os
from datetime import datetime
import warnings
from pathlib import Path

class FileLogger:
    def __init__(self, subdir_path: str | Path, names: list[str]) -> None:
        self.subdir_path = self._get_subdir(subdir_path)
        self.names = names
        self.current_date = self._get_date_text()
        file_path = self.subdir_path / Path(self.current_date)
        self._file = open(file_path, "w", newline="")
        self.writer = self._create_get_writer()

    def _create_get_writer(self) -> csv.DictWriter:
        file_path = self.subdir_path / self.current_date
        if not self._file.closed:
            self._file.close()
        self._file = open(file_path, "w", newline="")
        writer = csv.DictWriter(self._file, delimiter="\t", fieldnames = self.names)
        writer.writeheader()
        return writer

    def _get_subdir(self, subdir_path: str | Path) -> str | Path:
        if not os.path.isdir(subdir_path):
            warnings.warn("The folder doesn't exist, I will create folder myself in working directory")
            current_working_dir = Path(os.getcwd())
            directory_name = Path("InspectVision")
            subdir_path = current_working_dir/directory_name
            os.makedirs(subdir_path)
        return Path(subdir_path)

    def _get_date_text(self) -> str:
        today = datetime.now()
        return f"{today.year}_{today.month}_{today.day}"

    def _data_updater(self):
        today = self._get_date_text()
        if today != self.current_date:
            self.current_date = today
            self.writer = self._create_get_writer()

    def write_results(self, update_data: dict[str, tp.Any]):
        self._data_updater()
        self.writer.writerow(update_data)

    def close(self):
        self._file.close()


