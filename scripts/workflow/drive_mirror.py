#!/usr/bin/env python3
"""Mirror a Drive tree into an isolated GitHub directory without writing to Drive."""
import hashlib
import json
import os
import re
import shutil
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[2]
API = 'https://www.googleapis.com/drive/v3/'
FOLDER = 'application/vnd.google-apps.folder'
EXPORTS = {
    'application/vnd.google-apps.document': ('text/plain', '.txt'),
    'application/vnd.google-apps.spreadsheet': ('application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', '.xlsx'),
    'application/vnd.google-apps.presentation': ('application/vnd.openxmlformats-officedocument.presentationml.presentation', '.pptx'),
    'application/vnd.google-apps.drawing': ('image/png', '.png'),
}
ID = re.compile(r'^[A-Za-z0-9_-]+$')


def checked_id(value):
    if not isinstance(value, str) or not ID.fullmatch(value):
        raise ValueError('invalid Drive identifier')
    return value


def segment(name, file_id):
    # Keep path components portable and distinct, even for identical names.
    slug = re.sub(r'[^A-Za-z0-9._-]+', '-', name).strip('.-_')[:60] or 'item'
    return slug + '--' + checked_id(file_id)


class Drive:
    def __init__(self, token):
        if not token:
            raise ValueError('Drive access token is missing')
        self.token = token

    def request(self, endpoint, params=None):
        url = API + endpoint + ('?' + urlencode(params) if params else '')
        request = Request(url, headers={'Authorization': 'Bearer ' + self.token, 'Accept': 'application/json'})
        try:
            with urlopen(request, timeout=60) as response:
                return response.read()
        except Exception as exc:
            raise ValueError('Drive API request failed: ' + type(exc).__name__) from exc

    def metadata(self, file_id):
        return json.loads(self.request('files/' + quote(checked_id(file_id), safe=''), {'fields': 'id,name,mimeType,modifiedTime,capabilities(canListChildren)', 'supportsAllDrives': 'true'}))

    def children(self, folder_id):
        result = []
        page = None
        seen = set()
        while True:
            params = {'q': "'" + checked_id(folder_id) + "' in parents and trashed = false", 'pageSize': 100,
                      'fields': 'nextPageToken,incompleteSearch,files(id,name,mimeType,modifiedTime,webViewLink,capabilities(canDownload))',
                      'supportsAllDrives': 'true', 'includeItemsFromAllDrives': 'true'}
            if page:
                params['pageToken'] = page
            data = json.loads(self.request('files', params))
            if data.get('incompleteSearch') or not isinstance(data.get('files'), list):
                raise ValueError('Drive folder listing is incomplete')
            result.extend(data['files'])
            page = data.get('nextPageToken')
            if not page:
                return result
            if page in seen:
                raise ValueError('Drive pagination repeated a page token')
            seen.add(page)

    def content(self, file_id, mime):
        path = 'files/' + quote(checked_id(file_id), safe='')
        if mime in EXPORTS:
            return self.request(path + '/export', {'mimeType': EXPORTS[mime][0]})
        if mime.startswith('application/vnd.google-apps.'):
            raise ValueError('unsupported Google Workspace file type: ' + mime)
        return self.request(path, {'alt': 'media', 'supportsAllDrives': 'true'})


def file_path(parent_path, name, file_id, mime):
    name_part = segment(name, file_id)
    extension = EXPORTS[mime][1] if mime in EXPORTS else ''
    return '/'.join(['drive-mirror', 'files', *parent_path, name_part + extension])


def safe_mirror_path(root, path):
    if not isinstance(path, str) or not path.startswith('drive-mirror/files/') or '\\' in path:
        return None
    parts = Path(path).parts
    if any(part in ('.', '..') for part in parts):
        return None
    current = root
    for part in parts:
        current = current / part
        if current.is_symlink():
            return None
    if not current.resolve().is_relative_to(root.resolve() / 'drive-mirror/files'):
        return None
    return current


def safe_existing(root, path):
    file = safe_mirror_path(root, path)
    return file if file and file.is_file() else None


def sync(root, drive, root_id, now=None):
    root = Path(root)
    checked_id(root_id)
    top = drive.metadata(root_id)
    if top.get('id') != root_id or top.get('mimeType') != FOLDER or top.get('capabilities', {}).get('canListChildren') is False:
        raise ValueError('Drive root is not an accessible folder')
    manifest_file = root / 'drive-mirror/manifest.json'
    if manifest_file.parent.is_symlink() or manifest_file.is_symlink():
        raise ValueError('mirror manifest must not be a symlink')
    previous = json.loads(manifest_file.read_text(encoding='utf-8')) if manifest_file.is_file() else {}
    if previous and previous.get('root_id') != root_id:
        raise ValueError('configured Drive root does not match previous mirror')
    prior = {x['id']: x for x in previous.get('entries', [])}
    entries, folders, visited = [], [], {root_id}
    queue = [(root_id, [], [])]
    # Stage all newly fetched bytes outside the tracked tree until the scan succeeds.
    with tempfile.TemporaryDirectory(prefix='drive-mirror-') as tmp:
        staging = Path(tmp)
        while queue:
            parent_id, safe_parts, labels = queue.pop(0)
            for item in drive.children(parent_id):
                file_id = checked_id(item.get('id'))
                if file_id in visited:
                    raise ValueError('duplicate Drive identifier or directory cycle')
                visited.add(file_id)
                name, mime = item.get('name'), item.get('mimeType')
                if not isinstance(name, str) or not name or not isinstance(mime, str):
                    raise ValueError('Drive item metadata is incomplete')
                if mime == FOLDER:
                    folders.append({'id': file_id, 'name': name, 'parent_id': parent_id, 'folder_path': labels})
                    queue.append((file_id, [*safe_parts, segment(name, file_id)], [*labels, name]))
                    continue
                if item.get('capabilities', {}).get('canDownload') is False:
                    raise ValueError('Drive item is not downloadable: ' + file_id)
                if mime.startswith('application/vnd.google-apps.') and mime not in EXPORTS:
                    raise ValueError('unsupported Google Workspace file type: ' + mime)
                modified = item.get('modifiedTime')
                if not isinstance(modified, str) or not modified:
                    raise ValueError('Drive item modified time is missing: ' + file_id)
                path = file_path(safe_parts, name, file_id, mime)
                old = prior.get(file_id, {})
                old_file = safe_existing(root, old.get('path'))
                cached = (old_file and old.get('modified_at') == modified and old.get('mime_type') == mime and
                          old.get('sha256') and hashlib.sha256(old_file.read_bytes()).hexdigest() == old['sha256'])
                content = old_file.read_bytes() if cached else drive.content(file_id, mime)
                if not cached:
                    fresh = drive.metadata(file_id)
                    if any(fresh.get(key) != item.get(key) for key in ('id', 'name', 'mimeType', 'modifiedTime')):
                        raise ValueError('Drive item changed while downloading: ' + file_id)
                staged = staging / file_id
                staged.write_bytes(content)
                entries.append({'id': file_id, 'title': name, 'folder_path': labels, 'mime_type': mime,
                                'export_mime_type': EXPORTS[mime][0] if mime in EXPORTS else None,
                                'modified_at': modified, 'drive_url': item.get('webViewLink'), 'path': path,
                                'sha256': hashlib.sha256(content).hexdigest(), 'source_status': 'present'})
        # A disappeared item is ambiguous: deletion, move out or lost access. Keep its bytes and mark it.
        for file_id, old in prior.items():
            if file_id not in visited:
                if not safe_existing(root, old.get('path')):
                    raise ValueError('previously mirrored file is missing locally: ' + file_id)
                entries.append({**old, 'source_status': 'not_seen'})
        entries.sort(key=lambda x: x['id'])
        folders.sort(key=lambda x: x['id'])
        payload = {'schema_version': 'drive-mirror@1', 'root_id': root_id, 'folders': folders, 'entries': entries}
        unchanged = all(previous.get(k) == v for k, v in payload.items())
        if unchanged:
            return {'changed': False, 'files': len(entries), 'folders': len(folders)}
        for entry in entries:
            staged = staging / entry['id']
            if not staged.exists():
                continue
            target = safe_mirror_path(root, entry['path'])
            if not target:
                raise ValueError('mirror target is unsafe: ' + entry['id'])
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(staged, target)
        payload['last_changed_at'] = (now or datetime.now(timezone.utc)).isoformat()
        manifest_file.parent.mkdir(parents=True, exist_ok=True)
        manifest_file.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        return {'changed': True, 'files': len(entries), 'folders': len(folders)}


if __name__ == '__main__':
    try:
        print(json.dumps(sync(ROOT, Drive(os.environ.get('DRIVE_ACCESS_TOKEN', '')), os.environ.get('DRIVE_ROOT_FOLDER_ID', ''))))
    except Exception as exc:
        print('Drive mirror failed:', exc, file=__import__('sys').stderr)
        raise SystemExit(1)
