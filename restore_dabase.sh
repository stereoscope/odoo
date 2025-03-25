#!/usr/bin/env python3

import platform
import subprocess

system = platform.system()

if system == 'Darwin':  # Note: platform.system() returns 'Darwin' on macOS
    subprocess.run(["python", "cli.py", "restore-db", "--path-to-dump", "./db/dump.sql", "--db-user", "fritz"])
elif system == 'Linux':
    subprocess.run(["python", "cli.py", "restore-db", "--path-to-dump", "./db/dump.sql", "--db-user", "postgres"])

subprocess.run(["python", "cli.py", "modify-user", "-u", "friedrich@gaschler.at", "-p", "test", "--disable-2fa"])
