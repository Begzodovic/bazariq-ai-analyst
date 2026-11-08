"""Restore the read-only UZEX register from small GitHub-uploadable gzip parts."""
from pathlib import Path
import gzip
import hashlib
import os
import shutil
import tempfile


def ensure_database(path):
    path = Path(path)
    if path.is_file():
        return path
    packed = path.with_suffix(path.suffix + '.gz')
    parts = sorted(path.parent.glob(packed.name + '.part*'))
    if not packed.is_file() and not parts:
        raise FileNotFoundError(f'Missing {path.name}, {packed.name} and parts')
    if parts and not packed.is_file():
        expected = [packed.name + f'.part{i:02d}' for i in range(1, len(parts) + 1)]
        if [p.name for p in parts] != expected:
            raise FileNotFoundError('Database archive is missing one or more sequential parts')
    sources = [packed] if packed.is_file() else parts
    fingerprint = hashlib.sha256(''.join(str(f.resolve()) + ':' + str(f.stat().st_size) for f in sources).encode()).hexdigest()[:16]
    target = Path(tempfile.gettempdir()) / f'bazariq-{fingerprint}-{path.name}'
    if target.is_file() and target.stat().st_size > 0:
        return target
    tmp_packed = target.with_suffix('.gz.tmp')
    tmp_db = target.with_suffix('.db.tmp')
    try:
        if packed.is_file():
            source_path = packed
        else:
            with tmp_packed.open('wb') as output:
                for part in parts:
                    with part.open('rb') as source:
                        shutil.copyfileobj(source, output, length=1024 * 1024)
            source_path = tmp_packed
        with gzip.open(source_path, 'rb') as source, tmp_db.open('wb') as output:
            shutil.copyfileobj(source, output, length=1024 * 1024)
        if tmp_db.stat().st_size == 0:
            raise ValueError('Empty restored database')
        os.replace(tmp_db, target)
    finally:
        tmp_packed.unlink(missing_ok=True)
        tmp_db.unlink(missing_ok=True)
    return target
