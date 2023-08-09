import os
from pathlib import Path


def create_file_path(file_path):
    if not os.path.exists(file_path):
        path_end_index = file_path.rfind('/')
        if path_end_index == -1:
            path_end_index = file_path.rfind('\\')
        path = file_path[:path_end_index + 1]
        Path(path).mkdir(parents=True, exist_ok=True)
    return file_path


def create_file(file_path):
    if not (os.path.exists(file_path) and os.path.isfile(file_path)):
        create_file_path(file_path)
        open(file_path, 'a').close()
    return file_path


class PrefixSpliter:
    def __init__(self, prefix_keys: list[str]):
        self.prefix_keys = prefix_keys

    def __call__(self, line: str):
        return next(
            (
                (prefix, line.removeprefix(prefix))
                for prefix in self.prefix_keys
                if line.startswith(prefix)
            ),
            ('', line)
        )


def strings_to_dict(lines: list[str], spliter):
    result = {}
    for line in lines:
        key, val = spliter(line)
        result[key] = val.strip()
    return result