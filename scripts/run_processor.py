#!/usr/bin/env python
"""
DEPRECATED: This script is deprecated in favor of the new CLI interface.

Please use the 'kb' or 'kbp' commands instead:
  kb scan docs/ --rdf-output rdf_output/

For more information, run:
  kb --help
  kb scan --help
"""

import subprocess
import sys
import os

def main():
    print("=" * 70)
    print("DEPRECATION WARNING")
    print("=" * 70)
    print("This script is deprecated. Please use the 'kb' command instead:")
    print()
    print("  kb scan docs/ --rdf-output rdf_output/")
    print()
    print("For more information, run: kb --help")
    print("=" * 70)
    print()
    
    # Still run the command for backwards compatibility
    input_dir = "docs/"
    output_dir = "tmp/"
    rdf_output_dir_value = "rdf_output/"

    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(rdf_output_dir_value, exist_ok=True)

    cmd = [
        "poetry",
        "run",
        "kb",
        "scan",
        input_dir,
        "--rdf-output",
        rdf_output_dir_value
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    print(result.stdout)
    print(result.stderr, file=sys.stderr)
    return result.returncode == 0

if __name__ == "__main__":
    if main():
        sys.exit(0)
    else:
        sys.exit(1)