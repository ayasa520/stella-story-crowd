"""Bind a fresh ARM adapter to immutable inputs before it can serve requests.

Preparation receipts describe installed files; they grant no execution authority.
A separate, exact-hash root release must authorize this adapter and compilation.
No historical registry, legacy checkout, desktop dependency or PATH-selected Node
is a fallback. This module performs no work merely because it is imported.
"""

from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import struct
import subprocess
import time

from target_verified_utf8_v1 import decode_verified


ROOT = Path('/home/rikka/Projects/stella')
R = ROOT / 'data/native_recovery/royal-capital-20261110/repair-20261111'
SITE_ROOT = ROOT / 'artifacts/stella-site-repair-source/.sites-checkout'
ADAPTER_ROOT = R / 'target-arm-adapter-20261112-v2'
TOOLS_ROOT = R / 'target-arm-tools-20261112-v1'
TOOLS_RECEIPT = TOOLS_ROOT / 'toolchain-receipt.json'
TOOLS_RECEIPT_SHA256 = '1348b6ee3de36beac729002e6dc5812f5fc544b93e767e946352e3c283e08753'
NODE = Path('/usr/bin/node')
HISTORICAL_REGISTRY = R / 'playback/approved-memory-previews.json'
SOURCE_CLOSURE = (
    'lib/preview.ts', 'lib/preview-commands.ts', 'lib/story-directory.ts',
    'lib/native.ts', 'lib/errors.ts', 'config/commands.json',
    'config/lighting.json', 'config/effects.json', 'config/semantics.json',
    'config/story-directory.json', 'config/preview-policy.json', 'tsconfig.json',
    'package-lock.json',
)
ADAPTER_FILES = ('serve.py', 'adapter_config.py', 'compile.mjs', 'index.html',
                 'target_verified_utf8_v1.py')


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha256(raw):
    return hashlib.sha256(raw).hexdigest()


def absolute_file(value, parent=ROOT):
    """Resolve containment before reading a caller-supplied file or symlink."""
    path = Path(value)
    require(path.is_absolute(), 'An explicit absolute input path is required')
    actual = path.resolve(strict=True)
    require(actual.is_relative_to(parent.resolve()) and actual.is_file(),
            'Input file is outside its permitted root: ' + str(path))
    return actual


def bound_bytes(path, expected):
    require(isinstance(expected, str) and len(expected) == 64 and
            all(char in '0123456789abcdef' for char in expected),
            'An exact lowercase SHA-256 binding is required')
    raw = Path(path).read_bytes()
    require(sha256(raw) == expected, 'Bound file changed: ' + str(path))
    return raw


class JsonReader:
    """Retain raw evidence when decoding or JSON parsing rejects an input.

    The copied decoder requires byte-for-byte UTF-8 roundtrip on the same raw
    input. Parsing is attempted once after that boundary. A parse exception's
    document is archived separately because prior target evidence showed a
    mismatch between captured bytes and the exception document. Neither failure
    causes normalization, a file rewrite or a retry of an external operation.
    """

    def __init__(self, directory):
        self.directory = Path(directory)

    def parse(self, raw, context):
        text = decode_verified(raw, context)
        try:
            return json.loads(text)
        except json.JSONDecodeError as error:
            directory = self.directory / str(time.time_ns())
            directory.mkdir(parents=True, exist_ok=False)
            (directory / 'input.bin').write_bytes(raw)
            rejected = error.doc.encode('utf-8', errors='strict')
            (directory / 'exception-document-utf8.bin').write_bytes(rejected)
            receipt = dict(status='json_parse_rejected', context=context,
                inputSha256=sha256(raw), inputBytes=len(raw),
                exceptionDocumentSha256=sha256(rejected),
                exceptionDocumentBytes=len(rejected),
                exceptionDocumentEqualsVerifiedText=error.doc == text,
                message=error.msg, position=error.pos, line=error.lineno,
                column=error.colno, parseAttempts=1, dataRewritten=False,
                normalizationApplied=False, cause='unknown')
            (directory / 'receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
            raise

    def read(self, path, expected=None):
        raw = bound_bytes(path, expected) if expected else Path(path).read_bytes()
        return self.parse(raw, str(path))


def arm_elf(path):
    with Path(path).open('rb') as stream:
        header = stream.read(64)
    require(header[:6] == b'\x7fELF\x02\x01' and len(header) >= 20 and
            struct.unpack_from('<H', header, 18)[0] == 183,
            'Required host binary is not AArch64 ELF: ' + str(path))


@dataclass(frozen=True)
class AdapterConfig:
    here: Path
    registry: Path
    registry_sha256: str
    release: Path
    release_sha256: str
    toolchain: Path
    toolchain_sha256: str
    node_sha256: str
    loader: Path
    loader_sha256: str
    compiler: Path
    compiler_sha256: str
    guards: tuple
    versions: dict
    reader: JsonReader

    @classmethod
    def load(cls, arguments, here):
        here = Path(here).resolve()
        # The root selected two already fresh, independently guarded R roots.
        # A convenience copy is not evidence of ARM provenance. Bind these
        # exact roots and the immutable prepared receipt instead of selecting
        # any directory that merely happens to sit under an artifacts parent.
        require(here == ADAPTER_ROOT,
                'Only the explicitly reviewed fresh ARM adapter root is permitted')
        require(Path(arguments.site_root).resolve() == SITE_ROOT,
                'Only the canonical Site checkout is permitted')
        require(os.uname().machine == 'aarch64' and os.nice(0) == 19 and
                set(os.sched_getaffinity(0)) == {0, 1},
                'Launch must already be nice 19 on CPUs 0 and 1')
        reader = JsonReader(here / 'json-rejections')
        registry = absolute_file(arguments.registry, ADAPTER_ROOT)
        require(registry != HISTORICAL_REGISTRY, 'Historical registry cannot be reused')
        release = absolute_file(arguments.release)
        authority = reader.read(release, arguments.release_sha256)
        require(authority.get('schema') == 'stella.target_arm_adapter_release.v1',
                'Unknown fresh adapter release schema')
        for flag in ('rootConfirmed', 'adapterLaunchAuthorized',
                     'compilerExecutionAuthorized', 'registryApproved'):
            require(authority.get(flag) is True, 'Root release prerequisite is false: ' + flag)
        require(authority.get('formalWritesAllowed') is False,
                'This adapter never accepts formal write authority')
        require(authority.get('canonicalSiteRoot') == str(SITE_ROOT), 'Release Site binding differs')
        require(authority.get('adapterRoot') == str(ADAPTER_ROOT) and
                authority.get('toolRoot') == str(TOOLS_ROOT),
                'Release must bind the exact fresh adapter and tool roots')
        require(authority.get('registryBinding') == dict(path=str(registry), sha256=arguments.registry_sha256),
                'Release registry binding differs')
        toolchain = absolute_file(arguments.toolchain_receipt)
        require(toolchain == TOOLS_RECEIPT and arguments.toolchain_sha256 == TOOLS_RECEIPT_SHA256,
                'Use the exact immutable independently verified ARM toolchain receipt')
        require(authority.get('toolchainReceiptBinding') ==
                dict(path=str(toolchain), sha256=arguments.toolchain_sha256),
                'Release toolchain receipt binding differs')
        tools = reader.read(toolchain, arguments.toolchain_sha256)
        require(tools.get('schema') == 'stella.target_arm_host_toolchain_receipt.v1' and
                tools.get('architecture') == 'aarch64', 'An independently prepared ARM receipt is required')
        tool_root = Path(tools['toolRoot']).resolve()
        require(tool_root == TOOLS_ROOT,
                'Only the exact independently prepared ARM dependency root is permitted')
        require(tools['tools']['node']['executable']['file'] == str(NODE),
                'Node must be the explicit installed /usr/bin/node')
        bound_bytes(NODE, tools['tools']['node']['executable']['sha256'])
        arm_elf(NODE)
        inventory_binding = tools['installedFileManifest']
        inventory = reader.read(absolute_file(inventory_binding['file']), inventory_binding['sha256'])
        require(inventory['root'] == str(tool_root), 'Installed ARM manifest root differs')
        entries = {row['relativePath']: row for row in inventory['files'] if 'sha256' in row}
        loader_key = 'node_modules/tsx/dist/loader.mjs'
        require(loader_key in entries, 'Verified ARM tsx loader is missing')
        loader = absolute_file(str(tool_root / loader_key), tool_root)
        loader_sha = entries[loader_key]['sha256']
        bound_bytes(loader, loader_sha)
        esbuild = absolute_file(tools['tools']['esbuild']['armExecutable']['file'], tool_root)
        bound_bytes(esbuild, tools['tools']['esbuild']['armExecutable']['sha256'])
        arm_elf(esbuild)
        versions = {key: tools['tools'][key]['version'] for key in ('node', 'tsx', 'esbuild', 'playwrightCli')}
        require(versions['tsx'] == '4.22.1' and versions['esbuild'] == '0.28.0',
                'Compiler versions differ from reviewed source pins')
        for name, wanted in [('tsx', versions['tsx']), ('esbuild', versions['esbuild'])]:
            require(reader.read(tool_root / 'node_modules' / name / 'package.json')['version'] == wanted,
                    'Installed compiler package version differs')
        result = subprocess.run([str(NODE), '--version'], capture_output=True, check=True, timeout=10)
        require(result.stdout.decode('ascii').strip() == 'v' + versions['node'], 'Actual Node version differs')
        scopes = reader.read(registry, arguments.registry_sha256)
        require(isinstance(scopes, list), 'Fresh registry must retain the original list schema')
        guards = authority.get('guardFiles')
        require(isinstance(guards, list) and guards, 'Fresh source/data/tool guards are required')
        by_path = {}
        for guard in guards:
            path = absolute_file(guard['path'])
            require(str(path) == guard['path'] and str(path) not in by_path,
                    'Guards must have unique, resolved absolute paths')
            bound_bytes(path, guard['sha256'])
            by_path[str(path)] = guard['sha256']
        required = [here / name for name in ADAPTER_FILES]
        required += [SITE_ROOT / name for name in SOURCE_CLOSURE]
        required += [toolchain, loader, esbuild, tool_root / 'package-lock.json',
                     Path(inventory_binding['file']), ROOT / 'story_crowd_data/manifest.json',
                     ROOT / 'story_crowd_data/assets/catalog.json',
                     ROOT / 'story_crowd_data/review/native-restoration.json']
        # Every native/review source consumed by compilePreview must belong to
        # this frozen read set. A global ownership count cannot bind the actual
        # rows loaded by this subprocess, and registry bytes are intentionally
        # separate so registration does not create a circular static freeze.
        manifest = reader.read(ROOT / 'story_crowd_data/manifest.json')
        for scene in manifest['scenes']:
            required.extend(ROOT / 'story_crowd_data' / scene[key] for key in ('path', 'reviewPath'))
        required.extend(tool_root / name for name in entries)
        require({str(path.resolve()) for path in required} <= set(by_path),
                'Fresh release is missing source/data/adapter/ARM-payload guards')
        require(str(registry) not in by_path, 'Registry uses its separate exact binding, not static guards')
        compiler = here / 'compile.mjs'
        return cls(here, registry, arguments.registry_sha256, release,
            arguments.release_sha256, toolchain, arguments.toolchain_sha256,
            tools['tools']['node']['executable']['sha256'],
            loader, loader_sha, compiler, by_path[str(compiler)],
            tuple(by_path.items()), versions, reader)

    def verify(self):
        """Reject drift before/after compile and before a health acknowledgement."""
        bound_bytes(self.release, self.release_sha256)
        bound_bytes(self.registry, self.registry_sha256)
        bound_bytes(NODE, self.node_sha256)
        for path, expected in self.guards:
            bound_bytes(path, expected)

    def scopes(self):
        return self.reader.read(self.registry, self.registry_sha256)

    def health(self):
        self.verify()
        return dict(kind='stella-readonly-production-adapter', root=str(ROOT),
            siteRoot=str(SITE_ROOT), pid=os.getpid(), parent=os.getppid(),
            nodeExecutable=str(NODE), nodeExecutableSha256=self.node_sha256,
            compilerLoader=str(self.loader), compilerLoaderSha256=self.loader_sha256,
            compilerPath=str(self.compiler), compilerSha256=self.compiler_sha256,
            registryPath=str(self.registry), registrySha256=self.registry_sha256,
            registryScopeCount=len(self.scopes()), releasePath=str(self.release),
            releaseSha256=self.release_sha256, toolchainReceiptPath=str(self.toolchain),
            toolchainReceiptSha256=self.toolchain_sha256, versions=self.versions,
            affinity=sorted(os.sched_getaffinity(0)), nice=os.nice(0),
            adapterEntry=str(self.here / 'serve.py'),
            adapterEntrySha256=sha256((self.here / 'serve.py').read_bytes()),
            readOnly=True, browserStartedByAdapter=False)
