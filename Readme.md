# diff-script

A script to assist in the procedure of checking test outputs for line differences.  
This tool is meant to compliment parts of the grading process, not replace them.  
Critical thinking is required while using this tool.  
Do not blindly trust the produced results.  

## Setup

- Clone the repository
- Create virtual environment
- Activate virtual environment
- Install dependencies

On Linux

```
git clone https://github.com/myronfirst/diff-script.git
cd diff-script
python3 -m venv .venv
source ./.venv/bin/activate
python3 -m pip install -r requirements.txt
```

## Usage
```
python3 diff_script.py
```
**Recommended** Run under vscode python debugger.  

## Description
A tests collection is provided in the file `phase_b_tests.yaml`.  
Each test consists of
- an input
- a list of expected outputs matching the input

The script receives a ROOT directory as parameter (default value: `Submissions`)  
In the root directory the following sub-directory structure is expected, following this example
```
Submissions/00_3592_MYRON_TSATSARAKIS/
Submissions/01_3593_STELIOS_TSATSARAKIS/
Submissions/.../
```
Each student folder contains a submitted project, including a `Makefile`.  
The script traverses this sub-directory structure and on each one performs the commands
- `make clean`
- `make`
- for each test_input in the tests collection
  - `./main test_input`

The output of the `main` executable is captured and compared with the expected test output.  
An output .html file is produced (default value: `Diffs.html`), containing the line-by-line output-expected comparisons for each test  

**Drag-n-drop `Diffs.html` to a browser to interpret the results**  

Check `diff_script.py` for parameters documentation.  
These results are compimentary to the grading process, not a replacement of common logic.
