"""Run the official Site helper with this task's inherited scheduling bound.

Credentials still arrive only on the helper's hidden stdin. These temporary
child-only Git settings keep packing single-threaded and allow the project's
authorized unsigned commit; existing inherited Git entries are preserved.
"""
import os
import resource

assert os.getpriority(os.PRIO_PROCESS, 0) == 19
assert sorted(os.sched_getaffinity(0)) == [0, 1]
resource.setrlimit(resource.RLIMIT_NICE, (1, 1))
count = int(os.environ.get('GIT_CONFIG_COUNT', '0'))
for key, value in [('pack.threads', '1'), ('commit.gpgsign', 'false')]:
    os.environ['GIT_CONFIG_KEY_' + str(count)] = key
    os.environ['GIT_CONFIG_VALUE_' + str(count)] = value
    count += 1
os.environ['GIT_CONFIG_COUNT'] = str(count)
arguments = ['/usr/bin/node',
             '/home/rikka/.codex/plugins/cache/openai-curated-remote/sites/1.1.6/scripts/site-workflow.mjs',
             '--project-id', 'appgprj_6af1d18573a88191a1ddd6ffa41999ad']
os.execv(arguments[0], arguments)
