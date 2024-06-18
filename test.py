import pytest
import argparse

class ArgsParser:
    def __init__(self) -> None:
        self.parser = argparse.ArgumentParser(
            description="Run pytest with specified arguments",
            epilog="""
Example Usage:
    python test.py -k test_setTheme
    python test.py -f tests/ui/test_output_tab.py -k test_initial_state
""",
            formatter_class=argparse.RawTextHelpFormatter
        )
        self._populateArgs()
    
    def _populateArgs(self) -> None:
        self.parser.add_argument(
            "-k", "--keyword",
            action="store",
            help="Run tests by keyword."
        )
        self.parser.add_argument(
            "-f", "--file",
            action="store",
            help="Run tests from the specified file."
        )
    
    def parseArgs(self):
        return self.parser.parse_args()

if __name__ == "__main__":
    parser = ArgsParser()
    args = parser.parseArgs()
    pytest_args = ["-q"]

    if args.file:
        pytest_args.extend([args.file])
    else:
        pytest_args.extend(["tests/"])

    if args.keyword:
        pytest_args.extend(["-k", args.keyword])

    pytest.main(pytest_args)