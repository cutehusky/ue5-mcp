"""Run single-phase live smoke scripts against a running editor and write a JSON summary.

Phased (prepare/verify) scripts and scripts that launch their own editor are skipped; run them separately.
"""
import argparse
import json
import re
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
SELF_LAUNCHING = {'smoke_sequencer_persistence.py', 'smoke_source_control_git_added_live.py',
                  'smoke_source_control_git_live.py', 'smoke_source_control_history_live.py',
                  'smoke_source_control_project_files_live.py'}


def is_phased(text):
    return bool(re.search(r"'--phase'|choices=\[.prepare|'prepare'", text))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', required=True)
    parser.add_argument('--only', nargs='*')
    parser.add_argument('--timeout', type=int, default=900)
    args = parser.parse_args()
    results = {}
    scripts = sorted(HERE.glob('smoke_*.py'))
    for script in scripts:
        if args.only and script.name not in args.only:
            continue
        text = script.read_text(encoding='utf-8')
        if script.name in SELF_LAUNCHING or is_phased(text):
            continue
        start = time.time()
        try:
            proc = subprocess.run([sys.executable, str(script)], cwd=HERE, capture_output=True,
                                  text=True, timeout=args.timeout)
            status = 'pass' if proc.returncode == 0 else 'fail'
            tail = (proc.stdout[-1500:] + proc.stderr[-3000:]).strip()
        except subprocess.TimeoutExpired as e:
            status, tail = 'timeout', str(e)[-1500:]
        results[script.name] = {'status': status, 'seconds': round(time.time() - start, 1), 'tail': tail}
        print(f"{status:7} {results[script.name]['seconds']:7.1f}s {script.name}", flush=True)
        Path(args.out).write_text(json.dumps(results, indent=1), encoding='utf-8')
    counts = {}
    for r in results.values():
        counts[r['status']] = counts.get(r['status'], 0) + 1
    print(counts)


if __name__ == '__main__':
    main()
