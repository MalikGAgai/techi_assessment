"""Regenerate all offline analysis outputs from the two preserved CSV inputs."""
from pathlib import Path
import subprocess
import sys

if __name__ == '__main__':
    root = Path(__file__).resolve().parent
    for script in ['validate_data.py', 'analyze_articles.py', 'analyze_traffic.py', 'combine_evidence.py']:
        subprocess.run([sys.executable, str(root / script)], cwd=root, check=True)
