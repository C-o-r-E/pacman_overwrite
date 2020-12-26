#/usr/bin/python
"""
    This program is for dealing with the situation where many packages on a given system
    have become out-of-sync with pacman's package database specifically regarding the
    files owned by the packages. As a result, pacman will refuse to upgrade or even re-
    install many packages because /var/lib/pacman/local/<pkg_name>/files doesnt know
    about some files on the file system.

    TLDR: This parses the output of pacman to see what it complains about existing
    in the file system already and then will invoke pacman with the appropriate
    --overwrite list
"""

import argparse
import re
import subprocess
import sys
from typing import List

def get_pkg_conflict_files(pkg_name: str, err_msg: str) -> List[str]:
    """
        Using the package name and the output from pacman, return a list containig
        all the files that need to be overwritten
    """
    ret_lst = []
    file_pattern = f"^{pkg_name}: (.*) exists in filesystem$"

    lines = err_msg.split("\n")

    for line in lines:
        file_match = re.match(file_pattern, line, re.MULTILINE)

        if file_match:
            for fname in file_match.groups():
                print(f"got match: [{fname}]")
                ret_lst.append(fname)
    return ret_lst

def make_pacman_cmd(pkg_name, files: List[str]) -> str:
    """
        construct the command required to overwrite detected conflicts
    """
    conflicts = ",".join(files)
    return f"pacman -S --overwrite {conflicts} {pkg_name}"

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="overwrite all 'file exists' errors for package")
    parser.add_argument('package', type=str, help="Name of the package")

    args = parser.parse_args()

    if args.package:
        pkg = args.package

        pac_one = subprocess.run(["pacman","-S", pkg, "--noprogressbar", "--noconfirm"],
                                 capture_output=True, check=False)

        # we are expecting a specific error
        RE_MSG_CONFLICT = r"failed to commit transaction \(conflicting files\)"

        if pac_one.stderr and re.search(RE_MSG_CONFLICT, pac_one.stderr.decode(), re.MULTILINE):
            conflict_files = get_pkg_conflict_files(pkg, pac_one.stdout.decode())
            cmd = make_pacman_cmd(pkg, conflict_files)
            print("Use the following command to overwrite the conflicting files:")
            print(f"\t{cmd}")
        else:
            if pac_one.stdout:
                print("===stdout===")
                print(pac_one.stdout)

            if pac_one.stderr:
                print("===stderr===")
                print(pac_one.stderr)

            print(f"{sys.argv[0]}: Did not get expcted error message.")
            print("stdout and stderr are printed above...")
            sys.exit(1)
