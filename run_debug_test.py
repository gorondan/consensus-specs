import os
import subprocess

# Ensure correct Python environment
PYTHON_BIN = "python3"

# Set required environment variables
env = os.environ.copy()
env["PYTHONPATH"] = "eth2spec"

# You can set this to '1' to force single-threaded debug-friendly mode
NUM_WORKERS = "1"

# Target test and test directory
# test_keyword = "test_process_deposit_request_min_activation"
test_keyword = "test_deposit_to_delegate_request_has_valid_signature"
test_dir = "tests/core/pyspec/eth2spec"

# JUnit output path
report_path = os.path.join(test_dir, "../test-reports/test_results.xml")

# Full pytest command
cmd = [
    PYTHON_BIN, "-m", "pytest",
    "-n", NUM_WORKERS,
    "--capture=no",
    f"-k={test_keyword}",
    "--fork=eipxxxx_eods",
    "--preset=minimal",
    "--bls-type=fastest",
    f"--junitxml={report_path}",
    test_dir
]

# Run with subprocess so PyCharm breakpoints / pdb will work
subprocess.run(cmd, env=env)
