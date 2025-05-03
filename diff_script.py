import os
import pathlib
import signal
import tempfile
import yaml
import subprocess
from dataclasses import dataclass
from argparse import ArgumentParser
from difflib import HtmlDiff
from colorama import Fore, Style
from typing import Optional

import extract


HTML_CONTENT = '''
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN"
          "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">

<html>
<head>
    <meta http-equiv="Content-Type"
          content="text/html; charset=utf-8" />
    <title></title>
    <style type="text/css">
        table.diff {{font-family:Courier; border:medium;}}
        .diff_header {{background-color:#e0e0e0}}
        td.diff_header {{text-align:right}}
        .diff_next {{background-color:#c0c0c0}}
        .diff_add {{background-color:#aaffaa}}
        .diff_chg {{background-color:#ffff77}}
        .diff_sub {{background-color:#ffaaaa}}
    </style>
</head>

<body>
    <table class="diff" summary="Legends">
        <tr> <th colspan="2"> Legends </th> </tr>
        <tr> <td> <table border="" summary="Colors">
                      <tr><th> Colors </th> </tr>
                      <tr><td class="diff_add">&nbsp;Added&nbsp;</td></tr>
                      <tr><td class="diff_chg">Changed</td> </tr>
                      <tr><td class="diff_sub">Deleted</td> </tr>
                  </table></td>
             <td> <table border="" summary="Links">
                      <tr><th colspan="2"> Links </th> </tr>
                      <tr><td>(f)irst change</td> </tr>
                      <tr><td>(n)ext change</td> </tr>
                      <tr><td>(t)op</td> </tr>
                  </table></td> </tr>
    </table>
    {DIFFS_CONTENT}
</body>
</html>
'''
HTML_DIFF = HtmlDiff()

Lines = list[str]


@dataclass
class Test:
    id: str
    compile_flags: str
    input: str
    expected: list[Lines]


@dataclass
class CompletedTest:
    id: str
    tables: list[str]


@dataclass
class SubmissionName:
    first_name: str
    last_name: str
    csd_id: str
    def get(self) -> str: return f'{self.first_name}_{self.last_name}_{self.csd_id}'
    def get_with_order(self, order: int) -> str: return f'{order}_{self.get()}'


ORDERED_NAMES: list[SubmissionName] = [
    SubmissionName('JESUS', 'ORTEGA_CASTILLO', 'csd5881'),
    SubmissionName('ΑΛΕΞΑΝΔΡΟΣ', 'ΓΑΙΤΑΝΑΚΗΣ', 'csd4853'),
    SubmissionName('ΙΩΑΝΝΗΣ', 'ΓΡΗΓΟΡΙΑΔΗΣ', 'csd5385'),
    SubmissionName('ΑΓΓΕΛΟΣ', 'ΜΠΑΛΛΗΣ', 'csd4689'),
    SubmissionName('ΔΗΜΟΚΡΑΤΗΣ', 'ΣΤΑΘΑΚΗΣ', 'csd5010'),
    SubmissionName('ΜΑΡΙΑ', 'ΚΡΟΥΣΑΝΙΩΤΑΚΗ', 'csd4665'),
    SubmissionName('ΒΙΚΤΩΡΙΑ', 'ΚΑΤΣΑΜΑΝΗ', 'csd5420'),
    SubmissionName('ΙΩΑΝΝΗΣ', 'ΜΑΡΚΑΚΗΣ', 'csd5448'),
    SubmissionName('ΜΑΡΙΑ-ΑΝΑΣΤΑΣΙΑ', 'ΧΡΙΣΤΑΚΗ', 'csd5036'),
    SubmissionName('ΒΑΣΙΛΕΙΟΣ', 'ΚΑΡΑΒΑΣ', 'csd4893'),
    SubmissionName('ΝΟΡΙΑΝΑ', 'ΤΖΑΤΖΑΪ', 'csd5016'),
    SubmissionName('ΟΔΥΣΣΕΑΣ', 'ΠΕΡΔΙΚΑΚΗΣ', 'csd4989'),
    SubmissionName('ΠΑΝΑΓΙΩΤΗΣ_ΕΜΜΑΝΟΥΗΛ', 'ΑΝΤΩΝΑΚΑΚΗΣ', 'csd5137'),
    SubmissionName('ΑΡΗΣ', 'ΠΑΤΡΑΜΑΝΗΣ', 'csd5249'),
    SubmissionName('ΕΡΥΦΙΛΗ', 'ΚΑΣΤΑΝΙΔΟΥ', 'csd4440'),
    SubmissionName('ΔΗΜΗΤΡΙΟΣ', 'ΣΕΓΚΕΣΣΕΡ', 'csd5006'),
    SubmissionName('ΑΝΤΩΝΙΟΣ', 'ΑΙΒΑΛΙΩΤΗΣ', 'csd4837'),
    SubmissionName('ΕΜΜΑΝΟΥΗΛ', 'ΑΜΑΝΑΚΗΣ', 'csd4838'),
    SubmissionName('ΕΜΜΑΝΟΥΗΛ', 'ΜΑΣΤΟΡΑΚΗΣ', 'csd5255'),
    SubmissionName('ΑΛΕΞΑΝΔΡΟΣ', 'ΠΑΠΑΦΡΑΓΚΑΚΗΣ', 'csd5084'),
    SubmissionName('ΝΙΚΟΛΑΟΣ', 'ΜΠΟΡΜΠΟΥΔΑΚΗΣ', 'csd4962'),
    SubmissionName('RAUL', 'RODRIGUEZ_HERNANDEZ', 'csd5880'),
    SubmissionName('ΑΘΑΝΑΣΙΟΣ', 'ΤΕΜΠΕΛΗΣ', 'csd1431'),
    SubmissionName('ΝΙΚΟΛΑΟΣ', 'ΛΑΖΑΡΙΔΗΣ', 'csd4922'),
    SubmissionName('ΔΗΜΗΤΡΙΟΣ', 'ΚΑΤΣΙΜΠΑΡΟΣ', 'csd4551'),
    SubmissionName('ΓΕΩΡΓΙΟΣ', 'ΠΑΠΑΣΙΔΕΡΗΣ', 'csd5219'),
    SubmissionName('ΠΑΝΤΕΛΕΗΜΩΝ', 'ΤΣΑΓΚΑΡΑΚΗΣ', 'csd5075'),
    SubmissionName('ΖΑΧΑΡΙΑΣ_ΚΥΠΡΙΑΝΟΣ', 'ΒΛΑΧΑΚΗΣ', 'csd4602'),
    SubmissionName('ΑΝΔΡΕΑΣ', 'ΚΑΝΤΙΛΙΕΡΑΚΗΣ', 'csd5411'),
    SubmissionName('ΑΡΓΥΡΙΟΣ', 'ΠΑΤΡΑΜΑΝΗΣ', 'csd4379'),
    SubmissionName('ΑΝΑΣΤΑΣΙΟΣ', 'ΑΘΑΝΑΣΙΑΔΗΣ', 'csd4579'),
    SubmissionName('ΜΕΛΕΤΙΟΣ', 'ΒΑΣΙΛΕΙΑΔΗΣ', 'csd4847'),
    SubmissionName('ΜΙΧΑΗΛ_ΙΑΣΩΝ', 'ΓΙΑΝΝΑΚΟΠΟΥΛΟΣ', 'csd4612'),
    SubmissionName('ΝΙΚΟΛΕΤΑ', 'ΞΕΝΑΚΗ', 'csd4968'),
    SubmissionName('ΙΩΑΝΝΗΣ', 'ΠΕΤΣΗΣ', 'csd4993'),
    SubmissionName('ΙΩΑΝΝΗΣ', 'ΜΠΑΡΜΠΟΥΝΗΣ', 'csd4468'),
    SubmissionName('ΚΩΝΣΤΑΝΤΙΝΟΣ', 'ΛΗΜΝΑΙΟΣ', 'csd4927'),
    SubmissionName('ΛΟΥΙΖΑ-ΜΑΡΘΑ', 'ΑΠΟΣΤΟΛΑΚΗ', 'csd4842'),
    SubmissionName('ΝΙΚΟΛΑΟΣ', 'ΛΑΣΗΘΙΩΤΑΚΗΣ', 'csd4924'),
    SubmissionName('ΔΗΜΗΤΡΙΟΣ', 'ΠΑΠΑΔΟΠΟΥΛΟΣ', 'csd4976'),
    SubmissionName('ΜΙΧΑΗΛ', 'ΝΤΙΤΟΥΡΑΣ', 'csd4467'),
]

"""
Parameters
    ROOT(str): Root directory containing student submission sub-directories
    OUTPUT(str): Full path of the generated html file, containing student submission diff tables

student submission sub-directories whose names do not begin with a numerical digit are ignored
"""
ROOT = 'submissions'
OUTPUT = 'diffs.html'


def parse_project_output(s: str) -> str:
    for char in '<>,:':
        s = s.replace(char, ' ')  # replace annoying characters with whitespace
    for word in ['done', 'Done']:
        s = s.replace(word, word.upper())  # convert to upper case annoying words
    s = s.replace('\t', ' ').replace('\r', ' ')  # replace tabs and carriage returns with whitespace
    lines = s.split('\n')
    parsed_lines: list[str] = []
    for line in lines:
        line = line.strip()
        line = ' '.join(line.split())  # merge multiple whitespaces into one
        if line:
            parsed_lines.append(line)
    return '\n'.join(parsed_lines)


def parse_args() -> str:
    parser = ArgumentParser()
    parser.add_argument('test_collection_file_path', nargs='?', default='./tests_hy486_spring_2025_phase_1.yaml')
    args = parser.parse_args()
    return args.test_collection_file_path


def load_test_collection_yaml(path: str) -> dict:
    with open(path, 'r') as f:
        return yaml.safe_load(f)


def parse_tests(data) -> list[Test]:
    tests = []
    for test_data in data['tests']:
        test = Test(test_data['id'], test_data['compile_flags'], test_data['input'],
                    [parse_project_output(expected_item).splitlines() for expected_item in test_data['expected']])
        tests.append(test)
    return tests


def get_ordered_submission_name(name: str) -> str:
    for order, submission_name in enumerate(ORDERED_NAMES):
        if name in submission_name.get():
            return submission_name.get_with_order(order)
    print(f'Name {name} not found in ORDERED_NAMES')
    return f'999_{name}'


def order_submission_dirs(submission_dirs: list[str]) -> list[str]:
    ordered_submission_dirs: list[str] = []
    for dir in submission_dirs:
        dir_path: pathlib.Path = pathlib.Path(dir)
        assert dir_path.is_dir()
        if (dir_path.name[0].isdigit()):
            ordered_submission_dirs.append(str(dir_path))
            continue
        old_name: str = dir_path.name
        new_name: str = get_ordered_submission_name(old_name)
        new_dir_path = dir_path.rename(dir_path.with_name(new_name))
        ordered_submission_dirs.append(str(new_dir_path))
    return sorted(ordered_submission_dirs)


def print_success(msg: str) -> None:
    print(f'{Fore.GREEN}{msg}{Style.RESET_ALL}')


def print_failure(msg: str) -> None:
    print(f'{Fore.RED}{msg}{Style.RESET_ALL}')


def file_not_found(path: str) -> bool:
    return not os.path.exists(path)


def error_occurred(err: bool, msg: str):
    if err:
        print_failure(msg)
    return err


def run_process(args: list[str], cwd: str) -> str:
    try:
        # The process is run with stdout/stderr buffering disabled in order to capture the output in real-time
        completed_process = subprocess.run(
            ['stdbuf', '-o0', '-e0'] + args, cwd=cwd, capture_output=True, text=True, check=True, timeout=10.0)
        return completed_process.stdout
    except subprocess.TimeoutExpired as e:
        out = ''
        if e.stdout is not None:
            out = e.stdout.decode()
        return out + f'\n{e.timeout} sec timeout expired'
    except subprocess.CalledProcessError as e:
        out = ''
        if e.stdout is not None:
            out = e.stdout
        return out + f'\n{signal.strsignal(abs(e.returncode))}'


def find_file(base_str: str, filename: str) -> Optional[str]:
    base = pathlib.Path(base_str)  # current directory

    # Check in current directory
    for file in base.iterdir():
        if file.is_file() and file.name == filename:
            print(f'Makefile found in {str(base)}')
            return str(base)

    # Check in top-level subdirectories
    for subdir in base.iterdir():
        if not subdir.is_dir():
            continue
        for file in subdir.iterdir():
            if file.is_file() and file.name == filename:
                print(f'Makefile found in {str(subdir)}')
                return str(subdir)  # / operator is overloaded to join paths

    print(f'Makefile NOT found in {str(base)}')
    return None


def generate_completed_tests(tests: list[Test], submission_directories: list[str]) -> list[CompletedTest]:
    completed_tests: list[CompletedTest] = []
    for student_info in submission_directories:
        opt_dir: Optional[str] = find_file(student_info, 'Makefile')
        if error_occurred(opt_dir is None, f'{student_info:<60}Makefile not found'):
            continue
        assert opt_dir is not None
        directory: str = opt_dir
        tables: list[str] = []
        for test in tests:
            run_process(['make', 'clean'], cwd=directory)
            make_output: str = run_process(['make', f'{test.compile_flags}'], cwd=directory)
            print(make_output)
            if error_occurred(file_not_found(f'{directory}/main'), f'{directory:<60}main not found'):
                continue

            with tempfile.NamedTemporaryFile(mode='w+', delete=True) as input_file:
                input_file.write(test.input or '')
                input_file.flush()  # important
                stdout = run_process(['./main', f'{input_file.name}'], cwd=directory)
            output = parse_project_output(stdout).splitlines()
            expected_tables: list[str] = [  # multiple expected outputs for the same test input
                HTML_DIFF.make_table(expected, output, f'{test.id}_expected{i}', f'{test.id}_output')
                for i, expected in enumerate(test.expected)
            ]
            tables.extend(expected_tables)
        completed_tests.append(CompletedTest(student_info, tables))  # submission_directory is student id
        print_success(f'{student_info:<60}Generated Completed Tests')
    return completed_tests


def generate_html_file(completed_tests: list[CompletedTest]):
    SUBMISSION_TITLE = '<h4>{id} {suffix}</h4>'
    TABLE_SEPARATOR = '<br/>'
    diffs = [
        f'{SUBMISSION_TITLE.format(id=test.id, suffix="BEGIN")}\n{TABLE_SEPARATOR.join(test.tables)}\n{SUBMISSION_TITLE.format(id=test.id, suffix="END")}'
        for test in completed_tests
    ]
    diffs_content = '\n'.join(diffs)
    html_content = HTML_CONTENT.format(DIFFS_CONTENT=diffs_content)
    with open(OUTPUT, 'w') as f:
        f.write(html_content)


def main():
    if error_occurred(file_not_found(f'{ROOT}'), f'{ROOT} directory not found, exiting...'):
        return
    test_collection_file_path: str = parse_args()
    test_collection_yaml = load_test_collection_yaml(test_collection_file_path)
    tests: list[Test] = parse_tests(test_collection_yaml)

    extracted_submission_dirs: list[str] = extract.extract_submissions(ROOT)  # also modifies extracted directory names
    submission_dirs = order_submission_dirs(extracted_submission_dirs)
    completed_tests: list[CompletedTest] = generate_completed_tests(tests, submission_dirs)
    generate_html_file(completed_tests)


if __name__ == "__main__":
    main()
