"""Shared ownership and evidence helpers for deferred StateTree verification."""
import json
import uuid

import httpx
from smoke_navigation_mesh import PROJECT


class StateTreeVerification:
    def __init__(self, name, base):
        self.base = base
        self.manifest = PROJECT / 'Saved' / 'UE5MCP_Test' / (name + '.json')
        self.paths = []

    def call(self, method, route, body=None, **params):
        response = httpx.request(method, self.base + route, json=body, params=params, timeout=180)
        assert response.is_success, (response.status_code, response.text)
        return response.json()

    def create(self, name, **values):
        created = self.call('POST', '/state-trees/create',
                            {'AssetPath': '/Game/UE5MCP_Test/ST_' + name + '_' + uuid.uuid4().hex[:8]} | values)
        self.paths.append(created['asset_path'])
        return created['asset_path'], created['states'][0]['id']

    def inspect(self, path):
        return self.call('GET', '/state-trees/inspect', asset_path=path)

    def state(self, path, identity):
        return next(state for state in self.inspect(path)['states'] if state['id'] == identity)

    def edit(self, path, method, route, **values):
        return self.call(method, '/state-trees/' + route, {'AssetPath': path} | values)

    @staticmethod
    def stable(snapshot):
        return {key: value for key, value in snapshot.items() if key not in
                ['affected_assets', 'selected_id', 'would_change', 'dry_run', 'saved',
                 'diagnostics', 'validation_compiled_copy']}

    def snapshots(self, stable=False):
        return {path: self.stable(self.inspect(path)) if stable else self.inspect(path) for path in self.paths}

    def reject(self, path, method, route, **values):
        before = self.snapshots()
        response = httpx.request(method, self.base + '/state-trees/' + route,
                                 json={'AssetPath': path} | values, timeout=180)
        assert response.status_code >= 400, (route, str(values)[:400], response.status_code, response.text[:600])
        assert self.snapshots() == before, 'Rejected request changed an owned asset'

    def transaction_check(self, action):
        before = self.snapshots(stable=True)
        result = action()
        after = self.snapshots(stable=True)
        self.call('POST', '/editor/transactions/undo')
        assert self.snapshots(stable=True) == before, 'Undo failed to restore owned assets'
        self.call('POST', '/editor/transactions/redo')
        assert self.snapshots(stable=True) == after, 'Redo failed to restore owned assets'
        return result

    def save(self):
        for path in self.paths:
            self.edit(path, 'POST', 'compile', bSave=True)
        snapshots = self.snapshots(stable=True)
        for snapshot in snapshots.values():
            assert snapshot['ready_to_run'] and not snapshot['dirty']
            assert snapshot['editor_hash'] == snapshot['compiled_hash']
        self.manifest.parent.mkdir(parents=True, exist_ok=True)
        self.manifest.write_text(json.dumps({'paths': self.paths, 'snapshots': snapshots}, indent=2))

    def verify(self):
        saved = json.loads(self.manifest.read_text())
        self.paths = saved['paths']
        assert self.snapshots(stable=True) == saved['snapshots'], 'Cold snapshots differ'
        for path in self.paths:
            snapshot = self.inspect(path)
            assert snapshot['ready_to_run'] and not snapshot['dirty']
            assert snapshot['editor_hash'] == snapshot['compiled_hash']
            assert self.call('GET', '/state-trees/validate', asset_path=path)['diagnostics'].startswith('success')
            assert self.inspect(path) == snapshot

    def cleanup(self):
        if not self.paths and self.manifest.exists():
            self.paths = json.loads(self.manifest.read_text())['paths']
        for path in reversed(self.paths):
            self.call('POST', '/assets/delete', {'AssetPath': path})
        self.manifest.unlink(missing_ok=True)
