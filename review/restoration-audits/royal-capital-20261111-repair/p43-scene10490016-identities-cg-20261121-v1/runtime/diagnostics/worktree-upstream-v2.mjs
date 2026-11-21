import { readFile, realpath, appendFile } from "node:fs/promises";
import { createHash } from "node:crypto";
import { fileURLToPath } from "node:url";
import { resolve, sep } from "node:path";

const root = await realpath(fileURLToPath(new URL("../data-checkout/", import.meta.url)));
const repository = "/ayasa520/stella-story-crowd";
// A content-derived alias gives this fresh server an isolated read-only
// snapshot identity. It is a transport alias, not a claim of a Git commit for
// the dirty saved native/review files being validated.
const revision = process.env.STELLA_REVIEW_REVISION;
if (!/^[0-9a-f]{40}$/.test(revision ?? "")) throw Error("Missing review snapshot alias");

// This offline adapter changes only the upstream transport used by the saved
// Worker. Its normal projection and player prepare routes still consume the
// installed native/review files, including their sparse fields and real links.
// Deny outbound requests so a missing worktree resource cannot silently fall
// back to another revision or to an unrelated deployed script.
globalThis.fetch = async (input, init) => {
  const request = new Request(input, init);
  const url = new URL(request.url);
  if (request.method !== "GET") throw Error("Offline review permits upstream GET only");
  if (url.origin === "https://github.com" && url.pathname === repository + "/commits/main.atom") {
    return new Response(`<id>tag:github.com,2008:Grit::Commit/${revision}</id>`);
  }
  if (url.origin !== "https://raw.githubusercontent.com" || !url.pathname.startsWith(repository + "/")) {
    throw Error(`Unexpected offline upstream ${url.origin}${url.pathname}`);
  }
  const [ref, ...parts] = decodeURIComponent(url.pathname.slice(repository.length + 1)).split("/");
  const relative = parts.join("/");
  if (![revision, "main"].includes(ref) || parts.some(part => !part || part === "." || part === "..") ||
      !/^(?:manifest\.json|(?:native|review)\/scenes\/\d+\.json|assets\/[-\w./]+)$/.test(relative)) {
    return new Response(null, { status: 404 });
  }
  const path = await realpath(resolve(root, relative)).catch(error => {
    if (["ENOENT", "ENOTDIR"].includes(error.code)) return null;
    throw error;
  });
  if (!path?.startsWith(root + sep)) return new Response(null, { status: 404 });
  const bytes = await readFile(path);
  // Record the original member actually read by the saved Worker. This
  // observes model/controller/atlas delivery without replacing the program
  // or inferring which resource a logical client URL selected.
  if (/^assets\/(?:preview\/)?models\/(?:rom01|subaru01|emilia01|elsa_nomantle01|reinhard01)\//.test(relative) ||
      relative === 'assets/player/animation.json' || relative === 'assets/catalog.json' ||
      /^assets\/(?:preview\/pictures\/ADV_pic_103006\.webp|pictures\/ADV_pic_103006\.(?:png|webp))$/.test(relative)) {
    await appendFile(resolve(process.env.STELLA_REVIEW_OUTPUT ?? fileURLToPath(new URL('./', import.meta.url)), 'provider-events.jsonl'), JSON.stringify({
      epochMilliseconds: Date.now(), url: request.url, relative, revision: ref,
      range: request.headers.get('range'), completeFileBytes: bytes.length,
      sha256: createHash('sha256').update(bytes).digest('hex'),
    })+'\n');
  }
  const headers = { "Accept-Ranges": "bytes", "Content-Length": String(bytes.length) };
  const range = request.headers.get("range")?.match(/^bytes=(\d*)-(\d*)$/);
  if (range && (range[1] || range[2])) {
    const start = range[1] ? Number(range[1]) : Math.max(0, bytes.length - Number(range[2]));
    const end = range[1] && range[2] ? Math.min(Number(range[2]), bytes.length - 1) : bytes.length - 1;
    if (start > end) return new Response(null, { status: 416 });
    return new Response(bytes.subarray(start, end + 1), { status: 206, headers: {
      ...headers, "Content-Length": String(end - start + 1), "Content-Range": `bytes ${start}-${end}/${bytes.length}`,
    } });
  }
  return new Response(bytes, { headers });
};
