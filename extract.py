import os
import re
import zipfile
import pathlib
import rarfile


ROOT = 'submissions'


def extract_all(dir: str):
    if len(os.listdir(dir)) > 1:  # already extracted
        return
    for filename in os.listdir(dir):
        if filename.lower().endswith(('.zip', '.rar')):
            archive_path: str = os.path.join(dir, filename)
            if zipfile.is_zipfile(archive_path):
                with zipfile.ZipFile(archive_path, 'r') as archive_ref:
                    archive_ref.extractall(dir)
            elif rarfile.is_rarfile(archive_path):
                with rarfile.RarFile(archive_path, 'r') as archive_ref:
                    archive_ref.extractall(dir)
            else:
                assert False, f'File {archive_path} is not an archive'


def pre_process_dir_names(root: str):
    for dir_path in pathlib.Path(root).iterdir():
        if not dir_path.is_dir():
            continue
        # replace whitespace with underscore, remove suffix
        new_name: str = dir_path.name.replace(' ', '_').replace('_assignsubmission_file', '')
        match = re.search(r'_\d+$', new_name)  # remove number suffix
        if match:
            new_name = new_name[:match.start()]
        new_path = dir_path.with_name(new_name)
        dir_path.rename(new_path)


def get_submission_dir_names(root: str):
    return [os.path.join(root, path)
            for path in os.listdir(root)
            if os.path.isdir(os.path.join(root, path))]


def extract_submissions(root: str) -> list[str]:
    extract_all(root)
    pre_process_dir_names(root)  # replace problematic characters in directory names
    submission_dirs: list[str] = get_submission_dir_names(root)
    for submission_dir in submission_dirs:  # Extract all archive files in each submission directory
        extract_all(submission_dir)
    return submission_dirs


if __name__ == '__main__':
    extract_submissions(ROOT)
