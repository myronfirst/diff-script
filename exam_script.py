"""
TODO author the test inputs and expected outputs
TODO pick an input format. probably keep everything in a single file
"""

"""
EXPECTED format:

#comment

BEGIN test0
expected0
expected0
expected0
END

BEGIN test0
expected1
expected1
END

BEGIN test1
expected2
expected2
END
"""


import os
import yaml
import subprocess
from dataclasses import dataclass
from argparse import ArgumentParser
from difflib import SequenceMatcher, HtmlDiff
HTML_CONTENT = """
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN"
          "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">

<html>
<head>
    <meta http-equiv="Content-Type"
          content="text/html; charset=utf-8" />
    <title></title>
    <style type="text/css">
        table.diff {font-family:Courier; border:medium;}
        .diff_header {background-color:#e0e0e0}
        td.diff_header {text-align:right}
        .diff_next {background-color:#c0c0c0}
        .diff_add {background-color:#aaffaa}
        .diff_chg {background-color:#ffff77}
        .diff_sub {background-color:#ffaaaa}
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
    <br/>
    #DIFFS
</body>
</html>
"""


def RunComparisons(root):
    """
    root: folder, where student project directories exist
    EXPECTED: file, global constant, collection of expected results
    for each student project directory in root:
        make clean
        make
        for each test: ./main test_input.txt and capture the output result
        run compare on the output result
    """
    pass


def compare(result, expected):
    """
    result: file, student output
    expected: file, collection of expected results
    if result is one of expected, then test case passes. if result is none of expected then fail

    extract each expected result from expected via a separator in the file eg ---
    preprocess each expected result and the student output:
        split result to lines
        replace < > : and , chars with whitespace
        trim leading/trailing whitespace, merge multiple whitespaces to, eliminate \t \r \n chars
        remove empty lines
    check ChatGPT Text Similarity Methods and implement one of them
    compare the student result with all expected and show the most similar one
    (maybe dont perform line by lien comparison. perform whole result comparison and output a percentage)
    print student output with each expected result - lines side by side, print similarity percentage of of student output with expected result
    """
    pass


DEBUG_OUTPUT = """
        A
        DONE
        D 0 10
          Districts
          0
        DONE
        S 0 0
          Stations [0]
          0
        DONE
        S 0 0
        DONE
"""

ROOT = 'Submissions'

Lines = list[str]


@dataclass
class Test:
    id: str
    input: str
    output: Lines
    expected: list[Lines]


def parse_project_output(s: str) -> str:
    for char in '<>,:':
        s = s.replace(char, ' ')  # replace annoying characters with whitespace
    s = s.replace('\t', ' ').replace('\r', ' ')  # replace tabs and carriage returns with whitespace
    lines = s.split('\n')
    parsed_lines: list[str] = []
    for line in lines:
        line = line.strip()
        line = ' '.join(line.split())  # merge multiple whitespaces into one
        if line:
            parsed_lines.append(line)
    return '\n'.join(parsed_lines)


def main():
    def parse_args():
        parser = ArgumentParser()
        parser.add_argument('executable', nargs='?', default='./main')
        parser.add_argument('tests_file', nargs='?', default='./phase_b_tests.yaml')
        args = parser.parse_args()
        return args.executable, args.tests_file
    executable, tests_file = parse_args()

    def LoadYAMLFile(path: str) -> dict:
        with open(path, 'r') as f:
            return yaml.safe_load(f)
    data = LoadYAMLFile(tests_file)

    def parse_tests(data) -> list[Test]:
        tests = []
        for test_data in data['tests']:
            test = Test(test_data['id'], test_data['input'], [''],
                        [parse_project_output(expected_item).splitlines() for expected_item in test_data['expected']])
            tests.append(test)
        return tests
    tests: list[Test] = parse_tests(data)

    for dirpath, dirnames, filenames in os.walk(ROOT):
        for dirname in dirnames:
            subdirectory = os.path.join(dirpath, dirname)

            def GenerateDiffs():
                subprocess.run(['make', 'clean'], cwd=subdirectory, capture_output=True).check_returncode()
                subprocess.run(['make'], cwd=subdirectory, capture_output=True).check_returncode()
                completed_process = subprocess.run(['./main'], cwd=subdirectory, capture_output=True)
                completed_process.check_returncode()
                output = completed_process.stdout.decode()
                output = parse_project_output(output).splitlines()
                title = f'<h4>{dirname}</h4>'

                def GenerateTables() -> str:
                    tables: list[str] = []
                    for test in tests:
                        for idx, expected in enumerate(test.expected):
                            t = HtmlDiff().make_table(output, expected, f'{test.id}_output', f'{test.id}_expected_{idx}')
                            tables.append(t)
                    return '<br/>'.join(tables)
                tables = GenerateTables()
                return title + tables
            diffs = GenerateDiffs()
            html_content = HTML_CONTENT.replace('#DIFFS', diffs)
            with open(f'diffs.html', 'w') as f:
                f.write(html_content)


if __name__ == "__main__":
    main()
