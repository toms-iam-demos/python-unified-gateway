"""Export committed website source without local profiles, state or build outputs."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import tarfile
import io


def prepare(root: Path, output: Path, ref: str = 'HEAD'):
    commit = subprocess.check_output(['git', '-C', str(root), 'rev-parse', '--verify', ref + '^{commit}'], text=True).strip()
    archive = subprocess.check_output(['git', '-C', str(root), 'archive', '--format=tar', commit, 'www'])
    with tarfile.open(fileobj=io.BytesIO(archive)) as source:
        files = [member.name for member in source.getmembers() if member.isfile()]
    forbidden = ('.venv', 'profiles.local', '__pycache__', 'build', 'dist', 'node_modules')
    if any(any(part in forbidden or part.startswith('._') or part.startswith('.env') for part in Path(name).parts) or name.endswith(('.sqlite', '.db', '.pem', '.key')) for name in files):
        raise ValueError('Release contains a forbidden local or runtime file')
    output.mkdir(parents=True, exist_ok=True)
    name = 'pug-www-' + commit[:12] + '.tar'
    target = output / name
    target.write_bytes(archive)
    manifest = {'source_commit': commit, 'source_component': 'www', 'archive': name, 'sha256': hashlib.sha256(archive).hexdigest(), 'files': len(files), 'activation': 'not performed', 'profile': 'external', 'required_gate': 'Preserve visitor access and legacy connected routes before any ingress cutover.'}
    (output / (name + '.json')).write_text(json.dumps(manifest, indent=2) + '\n')
    return manifest


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--ref', default='HEAD')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(prepare(Path(__file__).resolve().parents[1], args.output, args.ref), indent=2))
