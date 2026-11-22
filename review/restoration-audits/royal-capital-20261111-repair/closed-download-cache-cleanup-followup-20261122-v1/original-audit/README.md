# Read-only follow-up: closed installer archive inventory

No cleanup was performed. Root alone decides and executes any later action.
This audit gives one exact three-file archive whitelist, not permission to
remove directories. The allocated-byte total is a stat observation and not
a guaranteed future filesystem-free increase.

The priority caches are small: pacman/pkg86016B allocated with only four0B
partial payloads; pip20480B; uv28672B. The earlier ARM download staging is
155648B after the recorded37-archive cleanup. Those removed files are checked
absent but are not relisted as candidates. The remaining old antlr wheel and
configure_target.py are preserved.

The proposed whitelist contains only:

- CC Switch3.20.1-1 cached pkg.tar.xz;
- its extracted src/data.tar.gz, byte-identical to the data.tar.gz member of
  the retained original.deb;
- paru2.2.0-1 cached pkg.tar.xz.

The actual paths, current bytes/allocated bytes/mtime/inode/nlink/SHA, package
versions, installed copies and proof records are in archive-whitelist.rootfalse.json.
Pacman reports both packages fully present:17/93 files, zero missing.
Archive main programs hash-identically to /usr/bin/cc-switch and /usr/bin/paru,
and to their separate preserved staging copies. Installed paths are regular
files resolving to themselves, not symlinks or hardlinks into the cache.
The running CC Switch maps /usr/bin/cc-switch, not its cached staging copy.

Original.deb and paru release.tar.zst are preserved, including their existing
src symlinks. All pkg/src trees, installed ELF/config/launchers, package
recipes and install.log remain outside the whitelist. No Qt/venv, tablet,
plugin/skill, media/evidence/log/history, Git-object or browser-profile content
is proposed for cleanup. No credentials or mail were read.

FD/maps observations are bounded by read permissions. An initial snapshot
overlapped this audit's archive-proof command and observed a bsdtar FD on
data.tar.gz; the archive read completed before the final sequential snapshot.
Both facts are retained. Final readable-process observations and all EACCES/
process-race errors are reported exactly; no sudo was attempted and global
absence is not claimed. No process environments or command lines were read,
and nonmatching FD/map paths are not published.

The reported free-space decline remains cause unknown. This report provides
only measured directory/file facts. Before any root cleanup, recheck each
exact recorded stat/hash and live-use snapshot; preserve every other path.
