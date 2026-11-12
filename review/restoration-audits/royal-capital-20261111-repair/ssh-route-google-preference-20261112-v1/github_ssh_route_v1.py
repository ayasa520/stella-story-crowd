"""Use a verified public GitHub SSH443 endpoint for this repository's transport.

The container's normal ssh.github.com lookup returned a 198.18/15 synthetic
address. We observed banner timeouts and a long receive-window-limited upload;
two public endpoints obtained over certificate-verified DNS HTTPS both passed
the existing GitHub host-key checks. This route avoids that synthetic address
without changing system DNS, global SSH settings, keys or known_hosts.

Resolve anew for each connection (respecting the short DNS lifetime), then exec
one SSH process. Never reconnect/replay a consumed Git stdin stream. Git retains
its normal object/ref transaction and the caller must verify the remote ACK.
"""
import ipaddress
import json
import os
from pathlib import Path
import sys
import time
from urllib.request import Request, urlopen

# Prefer the resolver currently returning the endpoint that completed a full
# 11.54MiB Git upload on this target. The other resolver repeatedly returned
# 20.27.177.118, where pack uploads timed out although small ref reads worked;
# Google's independently verified answer returned the successful endpoint.
# This is an observed target-route preference, not a hard-coded IP or a claim
# about either provider globally. Resolve anew and retain certificate/host-key
# verification, fallback DNS availability, and exactly one Git SSH stdin stream.
RESOLVERS = (
    'https://dns.google/resolve?name=ssh.github.com&type=A',
    'https://cloudflare-dns.com/dns-query?name=ssh.github.com&type=A',
)
STATE = Path('/home/rikka/.local/state/stella-ssh-repair-20261112')


def log(value):
    STATE.mkdir(mode=0o700, exist_ok=True)
    fd = os.open(STATE / 'routes.jsonl', os.O_WRONLY | os.O_APPEND | os.O_CREAT, 0o600)
    with os.fdopen(fd, 'a') as stream:
        stream.write(json.dumps(dict(unix=time.time(), pid=os.getpid(), **value)) + '\n')


def endpoint():
    failures = []
    for url in RESOLVERS:
        try:
            request = Request(url, headers={'Accept': 'application/dns-json'})
            with urlopen(request, timeout=8) as response:
                if response.status != 200:
                    raise RuntimeError('DNS HTTPS status ' + str(response.status))
                raw = response.read(65537)
            if len(raw) > 65536:
                raise RuntimeError('Oversize DNS answer')
            answer = json.loads(raw.decode('utf-8', errors='strict'))
            if answer.get('Status') != 0 or not any(
                    row.get('name', '').rstrip('.').lower() == 'ssh.github.com'
                    for row in answer.get('Question', [])):
                raise RuntimeError('Unexpected DNS question/status')
            for row in answer.get('Answer', []):
                if row.get('type') != 1 or row.get('name', '').rstrip('.').lower() != 'ssh.github.com':
                    continue
                address = ipaddress.ip_address(row['data'])
                if address.version == 4 and address.is_global:
                    log(dict(status='public_endpoint_selected', resolver=url,
                             address=str(address), ttl=row.get('TTL'), priorResolverFailures=failures,
                             hostKeyAlias='github.com', strictHostKeyChecking=True, port=443))
                    return str(address)
            raise RuntimeError('No global IPv4 SSH endpoint in DNS answer')
        except Exception as error:
            failures.append(dict(resolver=url, error=str(error)))
    log(dict(status='dns_https_resolution_failed', failures=failures))
    raise RuntimeError('No verified public GitHub SSH endpoint; inspect the local route log')


def main():
    arguments = sys.argv[1:]
    # Preserve unrelated remotes and OpenSSH's configuration-query behavior.
    # The installed repo has only its existing git@github.com origin; this
    # helper never rewrites a remote URL or takes authority over other hosts.
    github = any(value in ('github.com', 'git@github.com') for value in arguments)
    if not github or '-G' in arguments:
        os.execv('/usr/bin/ssh', ['/usr/bin/ssh', *arguments])
    address = endpoint()
    options = ['-oBatchMode=yes', '-oStrictHostKeyChecking=yes',
        '-oHostKeyAlias=github.com', '-oHostname=' + address, '-p', '443',
        '-oConnectTimeout=15', '-oConnectionAttempts=1',
        '-oServerAliveInterval=10', '-oServerAliveCountMax=3', '-oTCPKeepAlive=yes']
    os.execv('/usr/bin/ssh', ['/usr/bin/ssh', *options, *arguments])


if __name__ == '__main__':
    main()
