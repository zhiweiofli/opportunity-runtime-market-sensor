#!/usr/bin/env python3
"""Read the PR type from the body without interpreting it as a shell command."""
import os
import sys
from github_evidence import pr_type

try:
    print(pr_type(os.environ.get('PR_BODY', '')))
except ValueError as exc:
    print(str(exc), file=sys.stderr)
    sys.exit(1)
