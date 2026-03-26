#!/usr/bin/env python3
"""
vault_append.py - append summary to existing vault .md file
Usage: python3 vault_append.py <filename> <summary>
"""
import sys
import os
import subprocess

VAULT_DIR = '/root/obsidian-vault'
VAULT_SUBDIR = 'YouTube'

if len(sys.argv) < 3:
    print('Usage: vault_append.py <filename> <summary>')
    sys.exit(1)

filename = sys.argv[1]
summary = sys.argv[2]

filepath = os.path.join(VAULT_DIR, VAULT_SUBDIR, filename)

if not os.path.exists(filepath):
    print(f'ERROR: File not found: {filepath}')
    sys.exit(1)

# Append summary section
with open(filepath, 'a', encoding='utf-8') as f:
    f.write(f'\n## Саммари\n\n{summary}\n')

# git push
subprocess.run(['git', '-C', VAULT_DIR, 'pull', '--rebase'], capture_output=True)
subprocess.run(['git', '-C', VAULT_DIR, 'add', filepath], capture_output=True)
subprocess.run(['git', '-C', VAULT_DIR, 'commit', '-m', f'Add summary: {filename}'], capture_output=True)
result = subprocess.run(['git', '-C', VAULT_DIR, 'push'], capture_output=True, text=True)

if result.returncode == 0:
    print(f'✅ Саммари сохранено в Obsidian: {filename}')
else:
    print(f'⚠️ Файл обновлён локально, ошибка push: {result.stderr}')
