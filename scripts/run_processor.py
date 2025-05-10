import subprocess
import sys
import os

def main():
    input_dir = "docs/"
    output_dir = "tmp/"
    os.makedirs(output_dir, exist_ok=True)
    cmd = [
        "poetry",
        "run",
        "python",
        "-m",
        "knowledgebase_processor.cli.main",
        "--knowledge-base",
        input_dir,
        "--metadata-store",
        output_dir,
        "process",
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