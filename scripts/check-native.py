#!/usr/bin/env python3
"""Check pack discovery using an isolated OpenCode v2 server, without model calls."""
import argparse
import base64
import json
import os
from pathlib import Path
import queue
import re
import subprocess
import tempfile
import threading
import time
import urllib.parse
import urllib.request

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
args = parser.parse_args()
root = args.root.resolve()
expected_skills = {'pstack-' + p.parent.name for p in (root / 'skills').glob('*/SKILL.md')}
expected_commands = {'pstack:' + name.removeprefix('pstack-') for name in expected_skills if not name.startswith('pstack-principle-')}
with tempfile.TemporaryDirectory(prefix='pstack-native-') as tmp:
    base = Path(tmp)
    location = base / 'project'
    location.mkdir()
    config = base / 'config/opencode'
    config.mkdir(parents=True)
    (config / 'opencode.json').write_text(json.dumps({
        'plugins': [str(root)],
        'agents': {'existing-user-agent': {'description': 'Preserve this agent', 'mode': 'subagent', 'system': 'Existing prompt'}},
        'commands': {'existing-user-command': {'template': 'Keep this command'}}
    }))
    env = dict(os.environ, OPENCODE_CONFIG_DIR=str(config), XDG_CONFIG_HOME=str(base / 'config'), XDG_DATA_HOME=str(base / 'data'), XDG_STATE_HOME=str(base / 'state'), XDG_CACHE_HOME=str(base / 'cache'))
    process = subprocess.Popen(['opencode', 'serve', '--hostname', '127.0.0.1', '--port', '0'], cwd=location, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    lines = queue.Queue()
    def read_output():
        for line in process.stdout:
            lines.put(line)
    threading.Thread(target=read_output, daemon=True).start()
    try:
        deadline = time.monotonic() + 45
        endpoint = password = None
        while time.monotonic() < deadline and not (endpoint and password):
            try:
                line = lines.get(timeout=0.2)
            except queue.Empty:
                if process.poll() is not None:
                    raise RuntimeError('OpenCode test server exited before readiness')
                continue
            match = re.search(r'server listening on (http://127\.0\.0\.1:\d+)', line)
            if match:
                endpoint = match[1]
            if line.startswith('server password '):
                password = line.removeprefix('server password ').strip()
        assert endpoint and password, 'OpenCode test server did not report readiness'
        authorization = 'Basic ' + base64.b64encode(f'opencode:{password}'.encode()).decode()
        query = urllib.parse.urlencode({'location[directory]': str(location)})
        while time.monotonic() < deadline:
            data = {}
            for kind in ('skill', 'command', 'agent', 'plugin'):
                request = urllib.request.Request(f'{endpoint}/api/{kind}?{query}', headers={'Authorization': authorization})
                with urllib.request.urlopen(request, timeout=5) as response:
                    data[kind] = json.load(response)['data']
            skills = {p['id']: p for p in data['skill']}
            commands = {p['name'] for p in data['command']}
            agents = {p['id']: p for p in data['agent']}
            if expected_skills <= skills.keys() and expected_commands <= commands and 'existing-user-agent' in agents and any(p.get('id') == 'pstack' for p in data['plugin']) and all(Path(skills[name]['path']).resolve() == root / f'skills/{name.removeprefix("pstack-")}/SKILL.md' for name in expected_skills):
                break
            time.sleep(0.2)
        else:
            raise AssertionError(f'Plugin discovery incomplete: {[p.get("id") for p in data["plugin"] if p.get("id") == "pstack"]}; poteto path={skills.get("poteto-mode", {}).get("path")}')
        for name in expected_skills:
            assert Path(skills[name]['path']).resolve() == root / f'skills/{name.removeprefix("pstack-")}/SKILL.md', name
            assert 'OpenCode runtime contract' in skills[name]['content'], name
            if 'opencode/autoinvoke: false' in (root / f'skills/{name.removeprefix("pstack-")}/SKILL.md').read_text():
                assert skills[name]['autoinvoke'] is False, name
        assert 'existing-user-command' in commands
        assert agents['existing-user-agent']['system'] == 'Existing prompt'
        print(f'Native pstack plugin loaded through plugins configuration. Verified {len(expected_skills)} skills and {len(expected_commands)} commands; existing user agent and command preserved.')
    finally:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()
