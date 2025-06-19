import fileinput
import os
from pathlib import Path

SRC_DIR = str(Path(os.environ.get("PAWS_SRC_DIR", os.getcwd())).resolve())
REPO_DIR = str(Path(os.environ.get("PAWS_REPO_DIR", os.getcwd())).resolve())

print(f"Replacing {REPO_DIR!r} with {SRC_DIR!r}")

if __name__ == "__main__":
    for line in fileinput.input():
        print(line.rstrip().replace(REPO_DIR, SRC_DIR))
