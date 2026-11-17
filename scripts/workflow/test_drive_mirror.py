import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

from drive_mirror import Drive, FOLDER, sync
from build_archive_index import build

NOW = datetime(2026, 11, 17, tzinfo=timezone.utc)


def item(file_id, name, mime='text/plain', modified='2026-11-17T00:00:00Z'):
    return {'id': file_id, 'name': name, 'mimeType': mime, 'modifiedTime': modified, 'webViewLink': 'https://drive.google.com/open?id=' + file_id, 'capabilities': {'canDownload': True}}


class FakeDrive:
    def __init__(self):
        self.tree = {'root': [item('research', 'Research', FOLDER), item('judge', 'Judge', FOLDER)],
                     'research': [item('d1', 'Research-IBF-20261117-test.md', 'application/vnd.google-apps.document'), item('b1', 'chart.png', 'image/png')],
                     'judge': [item('j1', 'judge.md', 'text/markdown')]}
        self.data = {'d1': 'Known: 原始研究摘要\nOpportunity Hypothesis: 示例标题\nFinal Status: KILL'.encode(), 'b1': b'\x89PNG\r\n', 'j1': b'Judge text'}
        self.fetches = []

    def metadata(self, file_id):
        if file_id == 'root':
            return {'id': file_id, 'mimeType': FOLDER, 'capabilities': {'canListChildren': True}}
        return next(item for children in self.tree.values() for item in children if item['id'] == file_id)

    def children(self, file_id):
        return [dict(item) for item in self.tree[file_id]]

    def content(self, file_id, mime):
        self.fetches.append(file_id)
        return self.data[file_id]


class DriveMirrorTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.drive = FakeDrive()

    def manifest(self):
        return json.loads((self.root / 'drive-mirror/manifest.json').read_text())

    def test_nested_tree_full_content_noop_and_update(self):
        result = sync(self.root, self.drive, 'root', NOW)
        self.assertEqual((result['files'], result['folders']), (3, 2))
        entries = {x['id']: x for x in self.manifest()['entries']}
        self.assertEqual(entries['d1']['folder_path'], ['Research'])
        self.assertEqual((self.root / entries['b1']['path']).read_bytes(), b'\x89PNG\r\n')
        self.assertEqual(entries['d1']['export_mime_type'], 'text/plain')
        before = (self.root / 'drive-mirror/manifest.json').read_bytes()
        self.drive.fetches.clear()
        self.assertFalse(sync(self.root, self.drive, 'root', NOW)['changed'])
        self.assertEqual(self.drive.fetches, [])
        self.assertEqual((self.root / 'drive-mirror/manifest.json').read_bytes(), before)
        self.drive.tree['research'][0]['modifiedTime'] = '2026-11-18T00:00:00Z'
        self.drive.data['d1'] = b'changed'
        sync(self.root, self.drive, 'root', NOW)
        self.assertEqual(self.drive.fetches, ['d1'])
        self.assertEqual((self.root / entries['d1']['path']).read_bytes(), b'changed')

    def test_disappearance_retains_file_and_marks_unseen(self):
        sync(self.root, self.drive, 'root', NOW)
        old = next(x for x in self.manifest()['entries'] if x['id'] == 'd1')
        self.drive.tree['research'].pop(0)
        sync(self.root, self.drive, 'root', NOW)
        current = next(x for x in self.manifest()['entries'] if x['id'] == 'd1')
        self.assertEqual(current['source_status'], 'not_seen')
        self.assertTrue((self.root / old['path']).is_file())

    def test_failure_does_not_change_existing_mirror(self):
        sync(self.root, self.drive, 'root', NOW)
        before = (self.root / 'drive-mirror/manifest.json').read_bytes()
        self.drive.tree['research'].append(item('new', 'unsupported', 'application/vnd.google-apps.form'))
        with self.assertRaisesRegex(ValueError, 'unsupported'):
            sync(self.root, self.drive, 'root', NOW)
        self.assertEqual((self.root / 'drive-mirror/manifest.json').read_bytes(), before)
        self.assertEqual(len(self.manifest()['entries']), 3)

    def test_duplicate_identifier_and_unsafe_paths_are_not_written(self):
        self.drive.tree['research'].append(item('d1', '../../bad'))
        with self.assertRaisesRegex(ValueError, 'duplicate'):
            sync(self.root, self.drive, 'root', NOW)
        self.assertFalse((self.root / 'drive-mirror/manifest.json').exists())

    def test_symlinked_mirror_root_is_rejected(self):
        outside = self.root / 'outside'
        outside.mkdir()
        (self.root / 'drive-mirror').symlink_to(outside, target_is_directory=True)
        with self.assertRaisesRegex(ValueError, 'symlink'):
            sync(self.root, self.drive, 'root', NOW)
        self.assertEqual(list(outside.iterdir()), [])

    def test_symlinked_files_directory_is_rejected(self):
        mirror = self.root / 'drive-mirror'
        mirror.mkdir()
        outside = self.root / 'outside'
        outside.mkdir()
        (mirror / 'files').symlink_to(outside, target_is_directory=True)
        with self.assertRaisesRegex(ValueError, 'unsafe'):
            sync(self.root, self.drive, 'root', NOW)
        self.assertEqual(list(outside.iterdir()), [])

    def test_changed_source_during_download_aborts_scan(self):
        original = self.drive.content
        def changed(file_id, mime):
            result = original(file_id, mime)
            if file_id == 'd1':
                self.drive.tree['research'][0]['modifiedTime'] = '2026-11-18T00:00:00Z'
            return result
        with patch.object(self.drive, 'content', side_effect=changed):
            with self.assertRaisesRegex(ValueError, 'changed while downloading'):
                sync(self.root, self.drive, 'root', NOW)
        self.assertFalse((self.root / 'drive-mirror/manifest.json').exists())

    def test_index_deduplicates_legacy_document_and_includes_other_files(self):
        sync(self.root, self.drive, 'root', NOW)
        legacy = self.root / 'or-archive/research/legacy.md'
        legacy.parent.mkdir(parents=True)
        legacy.write_text('old content')
        (self.root / 'or-archive/manifest.json').write_text(json.dumps({'entries': [{'doc_id': 'd1', 'title': 'old', 'path': 'or-archive/research/legacy.md', 'sync_status': 'mirrored'}]}))
        cards = build(self.root)['entries']
        self.assertEqual(len(cards), 3)
        doc = next(x for x in cards if x['id'] == 'd1')
        self.assertEqual((doc['title'], doc['status']), ('示例标题', 'KILL'))
        self.assertEqual(doc['tags'], ['IBF'])
        self.assertTrue(any(x['id'] == 'b1' for x in cards))

    def test_workspace_exports_and_binary_download_use_correct_api(self):
        api = Drive('fake')
        with patch.object(api, 'request', return_value=b'content') as request:
            self.assertEqual(api.content('doc1', 'application/vnd.google-apps.document'), b'content')
            request.assert_called_with('files/doc1/export', {'mimeType': 'text/plain'})
            api.content('sheet1', 'application/vnd.google-apps.spreadsheet')
            self.assertIn('spreadsheetml', request.call_args.args[1]['mimeType'])
            api.content('image1', 'image/png')
            request.assert_called_with('files/image1', {'alt': 'media', 'supportsAllDrives': 'true'})
            with self.assertRaisesRegex(ValueError, 'unsupported'):
                api.content('form1', 'application/vnd.google-apps.form')

    def test_pagination_is_complete_and_repeated_token_rejected(self):
        api = Drive('fake')
        pages = [{'files': [{'id': 'a'}], 'nextPageToken': 'next'}, {'files': [{'id': 'b'}]}]
        with patch.object(api, 'request', side_effect=[json.dumps(x).encode() for x in pages]):
            self.assertEqual([x['id'] for x in api.children('root')], ['a', 'b'])
        pages = [{'files': [], 'nextPageToken': 'same'}, {'files': [], 'nextPageToken': 'same'}]
        with patch.object(api, 'request', side_effect=[json.dumps(x).encode() for x in pages]):
            with self.assertRaisesRegex(ValueError, 'pagination'):
                api.children('root')


if __name__ == '__main__':
    unittest.main()
