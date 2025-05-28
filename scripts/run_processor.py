import subprocess
import sys
import os

def main():
    input_dir = "docs/"
    output_dir = "tmp/"
    rdf_output_dir_value = "rdf_output/" # New RDF output directory

    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(rdf_output_dir_value, exist_ok=True) # Create RDF output dir

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
        "--rdf-output-dir", # Add the new argument
        rdf_output_dir_value # Add its value
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