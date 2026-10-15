"""Package an explicit allowlist, verify every member hash, and exclude local config."""
import hashlib
import json
from pathlib import Path
from zipfile import ZipFile, ZipInfo, ZIP_DEFLATED

ROOT = Path(__file__).resolve().parent
ZIP_PATH = ROOT / 'techi_assessment.zip'
MANIFEST = ROOT / 'outputs/final_audit/package_manifest.json'


def main():
    audit = json.loads((ROOT / 'outputs/final_audit/audit_results.json').read_text(encoding='utf-8'))
    if not audit['all_checks_passed']:
        raise ValueError('Final audit failed; do not package as ready')
    for name, expected in audit['sha256'].items():
        if hashlib.sha256((ROOT / name).read_bytes()).hexdigest() != expected:
            raise ValueError(f'Source changed since final audit: {name}')
    docs = ['traffic_table.csv', 'requirements.txt', 'requirements-lock.txt', 'README.md',
            'SCRAPING_RULES.md', 'ASSESSMENT_REQUIREMENTS.md', 'memo.md', 'method.txt']
    paths = [ROOT / name for name in docs] + list(ROOT.glob('*.py')) + list((ROOT / 'tests').glob('*.py'))
    extensions = {'.csv', '.md', '.json', '.jsonl', '.txt', '.xml', '.html', '.png'}
    paths += [p for p in (ROOT / 'outputs').rglob('*') if p.is_file() and p.suffix in extensions and p != MANIFEST]
    entries = {p.relative_to(ROOT).as_posix(): p for p in paths}
    entries['techi_articles.csv'] = ROOT / 'outputs/techi_articles.csv'
    if sum(name.endswith('.png') for name in entries) != 2:
        raise ValueError('Submission must contain exactly two final figures')
    hashes = {name: {'sha256': hashlib.sha256(path.read_bytes()).hexdigest(), 'bytes': path.stat().st_size}
              for name, path in sorted(entries.items())}
    manifest = {'files': hashes, 'note': 'This manifest excludes its own hash; root techi_articles.csv is a byte-identical deliverable copy of outputs/techi_articles.csv.'}
    MANIFEST.write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    entries[MANIFEST.relative_to(ROOT).as_posix()] = MANIFEST
    with ZipFile(ZIP_PATH, 'w', compression=ZIP_DEFLATED, compresslevel=9) as archive:
        for name, path in sorted(entries.items()):
            info = ZipInfo(name, date_time=(2026, 10, 15, 0, 0, 0))
            info.compress_type = ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            archive.writestr(info, path.read_bytes(), compress_type=ZIP_DEFLATED, compresslevel=9)
    with ZipFile(ZIP_PATH) as archive:
        if archive.testzip() is not None or len(archive.namelist()) != len(entries):
            raise ValueError('ZIP integrity/member-count check failed')
        for name, path in entries.items():
            if archive.read(name) != path.read_bytes():
                raise ValueError(f'Archive does not match source: {name}')
        for name, expected in hashes.items():
            if hashlib.sha256(archive.read(name)).hexdigest() != expected['sha256']:
                raise ValueError(f'Manifest hash mismatch: {name}')
    digest = hashlib.sha256(ZIP_PATH.read_bytes()).hexdigest()
    ZIP_PATH.with_suffix('.zip.sha256').write_text(f'{digest}  {ZIP_PATH.name}\n', encoding='utf-8')
    print(f'Created {ZIP_PATH.name}: {len(entries)} files, {ZIP_PATH.stat().st_size:,} bytes')
    print('PASS: ZIP CRC, exact member bytes, manifest hashes, two charts and audited source hashes')
    print(f'SHA-256: {digest}')


if __name__ == '__main__':
    main()
