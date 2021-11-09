import urllib.request
import shutil
import os

from loguru import logger

_project_root_dir = f'.{os.path.sep}'
_generated_dir = f"generated{os.path.sep}"


def download_file(url: str, destination_path: str):
    with urllib.request.urlopen(url) as response:
        if response.status != 200:
            msg = f"fetch URL {url} failed with STATUS CODE {response.status}\n" \
                  f"HEADERS: {response.headers}"
            raise RuntimeError(msg)
        # save to download_path
        with open(destination_path, 'wb') as out_file:
            shutil.copyfileobj(response, out_file)


def download_dir_for(source_name: str) -> str:
    """
    :param source_name: the name of the source requiring the directory. As this name will be part of the path, it is
    important that a source issues always the same name in order to get a stable path.
    :return: the path to an existing and usable folder.
    """
    path = f"{_project_root_dir}{_generated_dir}{source_name}{os.path.sep}"
    if not os.path.exists(path):
        os.makedirs(path, exist_ok=True)
    return path


def remove_file(file_path):
    if os.path.exists(file_path):
        try:
            os.remove(file_path)
        except OSError as e:
            logger.error(f"Failed to remove file {file_path} with error: {e.strerror}")


def change_project_root_dir(path: str):
    global _project_root_dir
    _project_root_dir = path


if __name__ == '__main__':
    path = f"{_project_root_dir}{_generated_dir}"
    print(f"path is {path}")
    from os.path import abspath
    print(f"absolute path is {abspath(path)}")

    change_project_root_dir("../")
    path = f"{_project_root_dir}{_generated_dir}"
    print(f"path is {path}")
    from os.path import abspath
    print(f"absolute path is {abspath(path)}")
