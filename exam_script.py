import os
import signal
import tempfile
import yaml
import subprocess
from dataclasses import dataclass
from argparse import ArgumentParser
from difflib import HtmlDiff
from colorama import Fore, Style

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
    input: str
    expected: list[Lines]


@dataclass
class CompletedTest:
    id: str
    tables: list[str]


"""
Parameters
    ROOT(str): Root directory containing student submission sub-directories
    OUTPUT(str): Full path of the generated html file, containing student submission diff tables

student submission sub-directories whose names do not begin with a numerical digit are ignored
"""
ROOT = 'Submissions'
OUTPUT = 'Diffs.html'


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
    parser.add_argument('test_collection_file_path', nargs='?', default='./phase_b_tests.yaml')
    args = parser.parse_args()
    return args.test_collection_file_path


def load_test_collection_yaml(path: str) -> dict:
    with open(path, 'r') as f:
        return yaml.safe_load(f)


def parse_tests(data) -> list[Test]:
    tests = []
    for test_data in data['tests']:
        test = Test(test_data['id'], test_data['input'],
                    [parse_project_output(expected_item).splitlines() for expected_item in test_data['expected']])
        tests.append(test)
    return tests


def get_submission_directories(root: str) -> list[str]:
    directories = []
    for dir_name in os.listdir(root):
        dir_path = os.path.join(root, dir_name)
        if os.path.isdir(dir_path) and dir_name[0].isdigit():
            directories.append(dir_path)
    return sorted(directories)


def print_success(msg: str) -> None:
    print(f'{Fore.GREEN}{msg}{Style.RESET_ALL}')


def print_failure(msg: str) -> None:
    print(f'{Fore.RED}{msg}{Style.RESET_ALL}')


def file_not_found(path: str) -> bool:
    return not os.path.exists(path)


def error_occured(err: bool, msg: str):
    if err:
        print_failure(msg)
    return err


def run_process(args: list[str], cwd: str) -> str:
    try:
        # The process is run with stdout/stderr buffering disabled in order to capture the output in real-time
        completed_process = subprocess.run(['stdbuf', '-o0', '-e0'] + args, cwd=cwd, capture_output=True, text=True, check=True)
        return completed_process.stdout
    except subprocess.CalledProcessError as e:
        return e.stdout + f'\n{signal.strsignal(abs(e.returncode))}'


def generate_completed_tests(tests: list[Test], submission_directories: list[str]) -> list[CompletedTest]:
    completed_tests: list[CompletedTest] = []
    for directory in submission_directories:
        if error_occured(file_not_found(f'{directory}/Makefile'), f'{directory:<50}Makefile not found'):
            continue
        run_process(['make', 'clean'], cwd=directory)
        run_process(['make'], cwd=directory)
        if error_occured(file_not_found(f'{directory}/main'), f'{directory:<50}main not found'):
            continue
        tables: list[str] = []
        for test in tests:
            with tempfile.NamedTemporaryFile(mode='w+', delete=True) as input_file:
                input_file.write(test.input)
                input_file.flush()  # important
                stdout = run_process(['./main', f'{input_file.name}'], cwd=directory)
            output = parse_project_output(stdout).splitlines()
            expected_tables: list[str] = [  # multiple expected outputs for the same test input
                HTML_DIFF.make_table(expected, output, f'{test.id}_expected{i}', f'{test.id}_output')
                for i, expected in enumerate(test.expected)
            ]
            tables.extend(expected_tables)
        completed_tests.append(CompletedTest(directory, tables))  # directory is student id
        print_success(f'{directory:<50}Generated Completed Tests')
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
    test_collection_file_path: str = parse_args()
    test_collection_yaml = load_test_collection_yaml(test_collection_file_path)
    tests: list[Test] = parse_tests(test_collection_yaml)
    submission_directories: list[str] = get_submission_directories(ROOT)
    completed_tests: list[CompletedTest] = generate_completed_tests(tests, submission_directories)
    generate_html_file(completed_tests)


if __name__ == "__main__":
    main()
