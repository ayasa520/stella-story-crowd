"""Serve a separately released, frozen ARM production comparison on loopback.

This author kit is inert until its exact fresh R root is reviewed/bound and
given a root-confirmed release, explicit fresh registry and verified toolchain.
There are no write, reload, registration, browser or installation endpoints.
"""

import argparse
import hashlib
from http.server import HTTPServer, SimpleHTTPRequestHandler
import json
import os
from pathlib import Path
import signal
import subprocess
import time
from urllib.parse import parse_qs, unquote, urlparse

from adapter_config import AdapterConfig, NODE, ROOT, SITE_ROOT


HERE = Path(__file__).resolve().parent
ASSETS = ROOT / 'story_crowd_data/assets'
COMPILER_TIMEOUT_SECONDS = 45


def log_event(name, **fields):
    payload = dict(fields)
    payload.update(adapterPid=os.getpid(), monotonic=time.monotonic())
    print(name + ' ' + json.dumps(payload), flush=True)


class Handler(SimpleHTTPRequestHandler):
    """Map only known GET routes to guarded input files or a bounded compiler."""

    def end_headers(self):
        self.send_header('Cache-Control', 'no-store')
        super().end_headers()

    def json_response(self, value):
        raw = json.dumps(value).encode('utf-8')
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def do_GET(self):
        try:
            parsed = urlparse(self.path)
            name = unquote(parsed.path)
            if name == '/health':
                self.json_response(self.server.config.health())
            elif name == '/program':
                self.program(parse_qs(parsed.query, keep_blank_values=True))
            else:
                self.static_file(name)
        except Exception as error:
            # Log concrete input/exception context. A failed response is never
            # attributed to installation, cache, or data corruption by this API.
            log_event('ARM_ADAPTER_REQUEST_REJECTED', path=urlparse(self.path).path,
                      exception=type(error).__name__, message=str(error))
            self.send_error(500, 'Read-only adapter input or compiler rejected the request')

    def program(self, query):
        if any(len(values) != 1 for values in query.values()):
            self.send_error(400, 'Ambiguous repeated program argument')
            return
        scene = query.get('scene', [''])[0]
        node = query.get('node', [''])[0]
        preview = query.get('nativePreview', [''])[0]
        if not scene.isascii() or not scene.isdecimal() or int(scene) <= 0 or (node and
                (not node.isascii() or not node.isdecimal() or int(node) <= 0)):
            self.send_error(400, 'An explicit positive scene and optional positive node are required')
            return
        config = self.server.config
        config.verify()
        approved = any(scope['sceneId'] == int(scene) and node and
            int(node) in scope['allowedStarts'] and preview in scope['exampleIds']
            for scope in config.scopes())
        if preview and not approved:
            self.send_error(400, 'Unknown bounded native-layout review')
            return
        command = [str(NODE), '--import', str(config.loader), str(config.compiler),
            str(ROOT), scene, node, preview, str(SITE_ROOT), str(config.registry),
            config.registry_sha256]
        started = time.monotonic()
        directory = HERE / 'compiler-runs' / str(time.time_ns())
        directory.mkdir(parents=True, exist_ok=False)
        environment = dict(os.environ, OMP_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1',
            MKL_NUM_THREADS='1', UV_THREADPOOL_SIZE='1', GOMAXPROCS='1',
            PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD='1', NO_UPDATE_NOTIFIER='1', CI='1')
        # The absolute installed Node and loader from the ARM payload manifest
        # are the only execution path. Descendants inherit nice19/CPU0,1. This
        # single-threaded HTTP owner cannot start parallel compiler requests.
        process = subprocess.Popen(command, cwd=SITE_ROOT, env=environment,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, start_new_session=True)
        log_event('ARM_COMPILER_STARTED', child=process.pid, command=command,
                  timeoutSeconds=COMPILER_TIMEOUT_SECONDS)
        timed_out = False
        interrupted = None
        try:
            stdout, stderr = process.communicate(timeout=COMPILER_TIMEOUT_SECONDS)
        except subprocess.TimeoutExpired:
            timed_out = True
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            stdout, stderr = process.communicate()
        except BaseException as error:
            # SIGTERM/SIGINT can interrupt communicate while the child's new
            # process group is still alive. Own and reap that entire group
            # before re-raising, otherwise a stopped adapter could leave an
            # unobserved compiler/esbuild process behind on the tablet.
            interrupted = error
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            stdout, stderr = process.communicate()
        (directory / 'stdout.bin').write_bytes(stdout)
        (directory / 'stderr.bin').write_bytes(stderr)
        receipt = dict(command=command, cwd=str(SITE_ROOT), pid=process.pid,
            processGroup=process.pid, exitCode=process.returncode, timedOut=timed_out,
            interruptedBy=type(interrupted).__name__ if interrupted else None,
            elapsedSeconds=time.monotonic() - started,
            stdoutSha256=hashlib.sha256(stdout).hexdigest(),
            stderrSha256=hashlib.sha256(stderr).hexdigest(),
            registrySha256=config.registry_sha256, compilerSha256=config.compiler_sha256,
            compilerLoaderSha256=config.loader_sha256,
            affinity=sorted(os.sched_getaffinity(0)), nice=os.nice(0),
            formalWrites=False, browserStarted=False)
        (directory / 'receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
        log_event('ARM_COMPILER_FINISHED', **receipt)
        if interrupted:
            raise interrupted
        if process.returncode or timed_out:
            raise RuntimeError('Compiler rejected the frozen input; inspect ' + str(directory))
        config.verify()
        config.reader.parse(stdout, 'compiler stdout ' + str(directory))
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(stdout)))
        self.end_headers()
        self.wfile.write(stdout)

    def static_file(self, name):
        candidate, permitted = None, ASSETS
        if name == '/':
            candidate, permitted = HERE / 'index.html', HERE
        elif name.startswith('/resource/'):
            candidate = ASSETS / name.removeprefix('/resource/')
        elif name.startswith('/player-assets/'):
            candidate = ASSETS / 'player' / name.removeprefix('/player-assets/')
        elif name in ('/speaker_names_zh.json', '/quake_clips.json'):
            candidate = ASSETS / 'player' / name.lstrip('/')
        else:
            catalog = self.server.config.reader.read(ASSETS / 'catalog.json')
            if name.startswith('/scene-thumbnail/'):
                thumbnail = catalog['thumbnails']['scene'].get(name.removeprefix('/scene-thumbnail/'))
                if thumbnail:
                    candidate = ASSETS / thumbnail
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
                    candidate = ASSETS / (row[field] if field else row)
                break
            if name.startswith('/pairing/'):
                tail = name.removeprefix('/pairing/')
                viewer = self.server.config.reader.read(ASSETS / 'player/preview_config.json')
                if tail == viewer['motion_index']:
                    candidate = ASSETS / 'player/motion_states.json'
                elif tail == 'preview_config.json':
                    candidate = ASSETS / 'player/preview_config.json'
                else:
                    candidate, permitted = SITE_ROOT / 'public' / name.lstrip('/'), SITE_ROOT / 'public'
            elif name.startswith(('/studio/', '/player/')):
                candidate, permitted = SITE_ROOT / 'public' / name.lstrip('/'), SITE_ROOT / 'public'
        # Containment is checked against the route's actual public asset root,
        # never the whole project. A GET cannot expose arbitrary workspace files
        # or directory listings through traversal or a symlinked asset member.
        if candidate is None or not candidate.resolve().is_relative_to(permitted.resolve()) or not candidate.is_file():
            self.send_error(404)
            return
        self.resolved = candidate.resolve()
        super().do_GET()

    def translate_path(self, path):
        return str(self.resolved)

    def reject_write(self):
        self.send_error(405, 'Only read-only GET routes are implemented')

    do_POST = do_PUT = do_PATCH = do_DELETE = do_HEAD = reject_write


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', type=int, required=True)
    parser.add_argument('--site-root', required=True)
    parser.add_argument('--registry', required=True)
    parser.add_argument('--registry-sha256', required=True)
    parser.add_argument('--toolchain-receipt', required=True)
    parser.add_argument('--toolchain-sha256', required=True)
    parser.add_argument('--release', required=True)
    parser.add_argument('--release-sha256', required=True)
    arguments = parser.parse_args()
    if not 1024 <= arguments.port <= 65535:
        parser.error('Use an explicit unprivileged loopback port')
    config = AdapterConfig.load(arguments, HERE)

    def interrupted(signum, _frame):
        log_event('ARM_ADAPTER_SIGNAL', signal=signum, parent=os.getppid())
        raise SystemExit(128 + signum)

    signal.signal(signal.SIGTERM, interrupted)
    signal.signal(signal.SIGINT, interrupted)
    # Binding is literal loopback. There is no command-line switch to make this
    # research adapter reachable on another interface or to swap its roots.
    with HTTPServer(('127.0.0.1', arguments.port), Handler) as server:
        server.config = config
        log_event('ARM_ADAPTER_READY', port=arguments.port, health=config.health())
        server.serve_forever()


if __name__ == '__main__':
    main()
