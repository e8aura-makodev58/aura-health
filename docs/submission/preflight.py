"""Read-only submission metadata/file checks; no network, upload or app mutation."""
import argparse
import json
from pathlib import Path
import struct
from urllib.parse import urlsplit
from zipfile import ZipFile, BadZipFile


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--require-ready', action='store_true')
    args = parser.parse_args()
    root = Path(__file__).resolve().parent
    manifest = json.loads((root / 'manifest.json').read_text())
    issues = []
    if manifest.get('status') != 'READY':
        issues.append('Package remains DRAFT; set READY only after final review/approval.')
    if not 1 <= len(manifest['short_blurb'].split()) <= 9:
        issues.append('Short blurb must be 1–9 words.')
    form_path = (root / manifest['form_copy']).resolve()
    if not form_path.is_relative_to(root) or not form_path.is_file():
        issues.append('Form copy missing or path leaves submission folder.')
    else:
        form = form_path.read_text()
        for heading, key in (('Project Title', 'project_title'), ('Short Blurb', 'short_blurb'),
                             ('Project Web Link', 'project_web_link'), ('Demo Video Link', 'demo_video_link'),
                             ('Source Code', 'source_code_link')):
            if not manifest.get(key):
                continue
            marker = '\n## ' + heading + '\n\n'
            actual = form.split(marker, 1)[1].split('\n\n', 1)[0].strip() if marker in form else None
            if actual != manifest[key]:
                issues.append(f'Form copy and manifest disagree: {heading}.')
    for key in ('project_web_link', 'demo_video_link', 'source_code_link'):
        value = manifest.get(key)
        if not value or urlsplit(value).scheme != 'https' or not urlsplit(value).netloc:
            issues.append(f'{key}: missing or invalid HTTPS URL.')
    duration = manifest.get('demo_video_duration_seconds')
    if type(duration) is not int or not 300 <= duration <= 480:
        issues.append('Video duration must be recorded as 300–480 seconds.')
    for name, item in manifest['assets'].items():
        target = (root / item['path']).resolve()
        if not target.is_relative_to(root):
            issues.append(f'{name}: path leaves submission folder.')
            continue
        if not target.is_file():
            issues.append(f'{name}: upload file missing ({item["path"]}).')
            continue
        if not 0 < target.stat().st_size <= item['max_bytes']:
            issues.append(f'{name}: empty or exceeds size ceiling.')
        if item['status'] != 'APPROVED':
            issues.append(f'{name}: human review/approval missing.')
        if name == 'cover':
            with target.open('rb') as stream:
                header = stream.read(24)
            if len(header) != 24 or header[:8] != b'\x89PNG\r\n\x1a\n' or header[12:16] != b'IHDR':
                issues.append('cover: proposed upload must be a genuine PNG.')
            else:
                width, height = struct.unpack('>II', header[16:24])
                if not width or not height or width * 9 != height * 16:
                    issues.append('cover: exact 16:9 ratio required.')
        elif name == 'conversation_history':
            with target.open('rb') as stream:
                if stream.read(5) != b'%PDF-':
                    issues.append('conversation_history: proposed bundle must be a genuine PDF.')
        elif name == 'architecture_ppt':
            try:
                with ZipFile(target) as deck:
                    names = deck.namelist()
                    if 'ppt/presentation.xml' not in names or not any(name.startswith('ppt/slides/slide') and name.endswith('.xml') for name in names):
                        issues.append('architecture_ppt: presentation/slides missing.')
            except (BadZipFile, OSError):
                issues.append('architecture_ppt: not a readable PPTX.')
    history = manifest['assets']['conversation_history']
    if type(history.get('screenshot_count')) is not int or history['screenshot_count'] < 3 or not history.get('chat_history_included'):
        issues.append('Conversation history requires actual chat history and at least 3 screenshots; inspect manually.')
    release = manifest['release']
    if not release.get('tested_commit'):
        issues.append('Final release/tested commit not recorded.')
    for key in ('signed_out_links_verified', 'claims_reviewed', 'user_approved'):
        if release.get(key) is not True:
            issues.append(f'Release approval missing: {key}.')
    print(f'Blurb: {len(manifest["short_blurb"].split())} words; limit under 10.')
    if issues:
        print('DRAFT / NOT READY — outstanding items:')
        for issue in issues:
            print('- ' + issue)
    else:
        print('Metadata checks PASS. Human artifact/permissions/claims review still required.')
    return 1 if issues and args.require_ready else 0


if __name__ == '__main__':
    raise SystemExit(main())
