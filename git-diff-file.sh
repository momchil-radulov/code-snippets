#!/usr/bin/env python3
"""Compare one working-tree file with a source branch, without changing either."""

import argparse
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

DEFAULT_SOURCE = 'your-branch'


def git(root, *args):
    result = subprocess.run(
        ['git', '-C', str(root), *args], stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if result.returncode:
        raise ValueError(result.stderr.decode(errors='replace').strip())
    return result.stdout


def select_file(argument, root, script_dir, source_files, source):
    path = Path(argument).expanduser()
    candidates = [path] if path.is_absolute() else [Path.cwd() / path, root / path, script_dir / path]
    for candidate in candidates:
        # Resolve the app's models symlink to its tracked common/ path.
        resolved = candidate.resolve()
        try:
            relative = resolved.relative_to(root).as_posix()
        except ValueError:
            continue
        if relative in source_files:
            return relative
        if resolved.is_file():
            raise ValueError(f'Файлът не съществува в {source}: {relative}')

    if path.is_absolute() or '..' in path.parts:
        raise ValueError(f'Файлът не е намерен в {source}: {argument}')

    suffix = path.as_posix()
    matches = sorted(name for name in source_files if name == suffix or name.endswith('/' + suffix))
    if len(matches) == 1:
        return matches[0]
    if matches:
        raise ValueError('Има няколко съвпадения. Подай по-пълен път:\n  ' + '\n  '.join(matches))
    raise ValueError(f'Файлът не е намерен в {source}: {argument}')


def main():
    parser = argparse.ArgumentParser(
        description='Показва diff: избран бранч → текущия файл, включително незакомитени промени.',
        epilog='Пример: ./git-diff-file settings.php your-branch',
    )
    parser.add_argument('file', help='Име, относителен път или абсолютен път на файл')
    parser.add_argument('branch', nargs='?', default=DEFAULT_SOURCE,
                        help='Изходен бранч (по подразбиране: your-branch)')
    args = parser.parse_args()
    source = args.branch
    script_dir = Path(__file__).resolve().parent

    try:
        root = Path(os.fsdecode(git(script_dir, 'rev-parse', '--show-toplevel')).strip()).resolve()
        # Pin the branch for a consistent file list and content during this run.
        revision = git(root, 'rev-parse', '--verify', '--end-of-options', source + '^{commit}').decode().strip()
        source_files = {
            os.fsdecode(name) for name in
            git(root, 'ls-tree', '-r', '--name-only', '-z', revision).split(b'\0') if name
        }
        relative = select_file(args.file, root, script_dir, source_files, source)
        current = root / relative
        if current.exists() and not current.is_file():
            raise ValueError(f'Текущият път не е обикновен файл: {relative}')
        source_content = git(root, 'show', revision + ':' + relative)
        if current.is_file() and current.read_bytes() == source_content:
            print(f'Без разлики: {relative} съвпада с {source}.')
            return 0

        interactive = sys.stdout.isatty()
        print(f'Файл: {relative}\n- {source} ({revision[:9]})\n+ текущото работно копие', flush=True)
        if not current.is_file():
            print('Файлът липсва тук; сравнява се с празен файл.', flush=True)

        with tempfile.TemporaryDirectory(prefix='git-diff-file-') as directory:
            original = Path(directory) / 'source'
            original.write_bytes(source_content)
            result = subprocess.run([
                'diff', '-u', '--color=' + ('always' if interactive else 'never'),
                '--label', source + '/' + relative,
                '--label', 'current/' + relative,
                str(original), str(current) if current.is_file() else os.devnull,
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if result.returncode not in (0, 1):
            raise ValueError(result.stderr.decode(errors='replace').strip())

        if interactive and shutil.which('less'):
            subprocess.run(['less', '-R'], input=result.stdout, check=False)
        else:
            sys.stdout.buffer.write(result.stdout)
        # Differences are the normal result, not a script failure.
        return 0
    except (ValueError, OSError) as error:
        print(f'Грешка: {error}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        sys.exit(130)
    except BrokenPipeError:
        sys.exit(0)
