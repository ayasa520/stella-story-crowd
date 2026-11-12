"""Expose installed scripts/assets to the production player for local review.

The online repository requires private authentication. This adapter avoids
altering that boundary: it serves only local read-only resources and invokes
the exact website compiler. It has no project/data mutation endpoints.
"""

import argparse
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import signal
import subprocess
import time
from urllib.parse import parse_qs, unquote, urlparse


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
SITE_ROOT = ROOT / 'story_crowd'
MEMORY_SCOPES = json.loads((HERE / 'approved-memory-previews.json').read_text())


class Handler(SimpleHTTPRequestHandler):
    def end_headers(self):
        # Installed scripts and resource metadata change between guarded
        # repair batches. This local review endpoint has no immutable commit
        # in its URLs, so each response must represent the installed files
        # that the production compiler reads during that same review run.
        self.send_header('Cache-Control', 'no-store')
        super().end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        name = unquote(parsed.path)
        assets = ROOT / 'story_crowd_data/assets'
        if name == '/health':
            payload = json.dumps(dict(kind='stella-readonly-production-adapter',
                                      root=str(ROOT), siteRoot=str(SITE_ROOT), pid=os.getpid())).encode()
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)
            return
        if name == '/program':
            query = parse_qs(parsed.query)
            scene, node = query.get('scene', ['10280014'])[0], query.get('node', [''])[0]
            native_preview = query.get('nativePreview', [''])[0]
            if not scene.isdigit() or (node and not node.isdigit()):
                self.send_error(400)
                return
            # The compiler independently verifies the registry's packet hash,
            # field guards and target bounds. HTTP accepts only the same named
            # starts; adding a proposal does not create any data-write endpoint.
            approved = any(scope['sceneId'] == int(scene) and node and
                           int(node) in scope['allowedStarts'] and
                           native_preview in scope['exampleIds']
                           for scope in MEMORY_SCOPES)
            if native_preview and not approved:
                self.send_error(400, 'Unknown bounded native-layout review')
                return
            process = subprocess.run([
                'node', '--import', str(ROOT / 'story_crowd/node_modules/tsx/dist/loader.mjs'),
                str(HERE / 'compile.mjs'), str(ROOT), scene, node, native_preview, str(SITE_ROOT)],
                cwd=SITE_ROOT, capture_output=True, check=False)
            if process.returncode:
                self.log_error('COMPILER_ERROR %s', process.stderr.decode()[-2000:])
                self.send_error(500)
                return
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', str(len(process.stdout)))
            self.end_headers()
            self.wfile.write(process.stdout)
            return
        self.resolved = None
        if name == '/':
            self.resolved = HERE / 'index.html'
        elif name.startswith('/resource/'):
            self.resolved = assets / name.removeprefix('/resource/')
        elif name.startswith('/player-assets/'):
            self.resolved = assets / 'player' / name.removeprefix('/player-assets/')
        elif name in ('/speaker_names_zh.json', '/quake_clips.json'):
            self.resolved = assets / 'player' / name.lstrip('/')
        else:
            catalog = json.loads((assets / 'catalog.json').read_text())
            if name.startswith('/scene-thumbnail/'):
                thumbnail = catalog['thumbnails']['scene'].get(name.removeprefix('/scene-thumbnail/'))
                if thumbnail:
                    self.resolved = assets / thumbnail
            mappings = {
                '/asset/': ('asset_members', None), '/background/': ('backgrounds', 'url'),
                '/picture/': ('pictures', 'url'), '/movie/': ('movies', 'url'),
                '/music/': ('music', 'url'), '/api/music/': ('music', 'metadata_url'),
                '/api/voices/': ('voices', 'detail_url'), '/api/model/': ('models', 'detail_url'),
            }
            for prefix, (section, field) in mappings.items():
                if not name.startswith(prefix):
                    continue
                identity = name.removeprefix(prefix)
                if section == 'models':
                    identity = 'live2d/AC_' + identity
                row = catalog[section].get(identity)
                if row:
                    self.resolved = assets / (row[field] if field else row)
                break
            if name.startswith('/pairing/'):
                tail = name.removeprefix('/pairing/')
                viewer = json.loads((assets / 'player/preview_config.json').read_text())
                if tail == viewer['motion_index']:
                    self.resolved = assets / 'player/motion_states.json'
                elif tail == 'preview_config.json':
                    self.resolved = assets / 'player/preview_config.json'
                else:
                    self.resolved = SITE_ROOT / 'public' / name.lstrip('/')
            elif name.startswith(('/studio/', '/player/')):
                # Review the same /player/ iframe opened by the online Studio.
                # The editor's material player is a separate entry point and
                # cannot establish that production-only integration works.
                self.resolved = SITE_ROOT / 'public' / name.lstrip('/')
        if self.resolved is None or not self.resolved.resolve().is_relative_to(ROOT):
            self.send_error(404)
            return
        super().do_GET()

    def translate_path(self, path):
        return str(self.resolved)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', type=int, default=5178)
    parser.add_argument('--site-root', type=Path, default=SITE_ROOT)
    arguments = parser.parse_args()
    # Never swap source roots behind an active review process. The explicit
    # startup argument and /health receipt bind every static module/compiler
    # response to one checkout; no endpoint changes data or checkout contents.
    SITE_ROOT = arguments.site_root.resolve()
    if not SITE_ROOT.is_relative_to(ROOT) or not (SITE_ROOT / 'lib/preview.ts').is_file():
        parser.error('Site source must be an existing checkout inside this workspace')
    def interrupted(signum, _frame):
        # Preserve authoritative termination evidence across goal turns.
        # A connection refusal must not be assigned to data or rendering when
        # the owned review process actually received a termination signal.
        print('REPAIR_PLAYER_SIGNAL ' + json.dumps(dict(signal=signum, pid=os.getpid(),
              parent=os.getppid(), monotonic=time.monotonic())), flush=True)
        raise SystemExit(128 + signum)
    signal.signal(signal.SIGTERM, interrupted)
    signal.signal(signal.SIGINT, interrupted)
    print(f'REPAIR_PLAYER_READONLY http://127.0.0.1:{arguments.port}', flush=True)
    print('REPAIR_PLAYER_PROCESS ' + json.dumps(dict(pid=os.getpid(), parent=os.getppid(),
          port=arguments.port, monotonic=time.monotonic())), flush=True)
    ThreadingHTTPServer(('127.0.0.1', arguments.port), Handler).serve_forever()
