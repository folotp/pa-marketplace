"""Exercise the actual workflow shell in disposable repositories, with gh mocked."""
from pathlib import Path
import os
import subprocess
import tempfile
import unittest


class BumpWorkflowTests(unittest.TestCase):
    def test_new_and_existing_bot_branch_preserve_main(self):
        workflow = (Path(__file__).resolve().parents[1] / '.github/workflows/auto-bump-external-plugins.yml').read_text()
        text = workflow.split('      - name: Open or update bump pull request', 1)[1].split('        run: |\n', 1)[1].split('\n      - name:', 1)[0]
        commands = '\n'.join(line[10:] for line in text.splitlines())
        # Use the same shell procedure but put temporary snapshots in the fixture.
        with tempfile.TemporaryDirectory(prefix='marketplace-workflow-') as temp:
            root = Path(temp)
            commands = commands.replace('/tmp/marketplace-bump', str(root / 'snapshot'))
            def run(*args, cwd=root):
                return subprocess.check_output(args, cwd=cwd, text=True, stderr=subprocess.STDOUT)
            run('git', 'init', '--bare', '-q', str(root / 'remote.git'))
            run('git', 'init', '-q', '-b', 'main', str(root / 'repo'))
            repo = root / 'repo'
            for name in ('.claude-plugin/marketplace.json', '.agents/plugins/marketplace.json', 'README.md', 'scripts/validate-marketplace.py'):
                path = repo / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text('pass\n' if name.endswith('.py') else 'original\n')
            run('git', 'config', 'user.email', 'test@example.invalid', cwd=repo)
            run('git', 'config', 'user.name', 'Test', cwd=repo)
            run('git', 'add', '.', cwd=repo)
            run('git', 'commit', '-qm', 'fixture', cwd=repo)
            run('git', 'remote', 'add', 'origin', str(root / 'remote.git'), cwd=repo)
            run('git', 'push', '-u', 'origin', 'main', cwd=repo)
            original = run('git', 'rev-parse', 'main', cwd=repo)
            bin_dir = root / 'bin'
            bin_dir.mkdir()
            gh = bin_dir / 'gh'
            gh.write_text('#!/bin/sh\nif [ "$1 $2" = "pr list" ]; then echo 0; fi\n')
            gh.chmod(0o755)
            env = dict(os.environ, PATH=str(bin_dir) + os.pathsep + os.environ['PATH'])
            # New branch, existing open/merged branch, and repeated unchanged run.
            for iteration, version in enumerate(('first', 'second', 'second')):
                run('git', 'switch', 'main', cwd=repo)
                if 'chore/auto-bump-external-plugins' in run('git', 'branch', '--list', cwd=repo):
                    run('git', 'branch', '-D', 'chore/auto-bump-external-plugins', cwd=repo)
                (repo / 'README.md').write_text(version + '\n')
                subprocess.run(['bash', '-euo', 'pipefail', '-c', commands], cwd=repo, env=env, check=True, capture_output=True, text=True)
                self.assertEqual(run('git', 'show', 'origin/chore/auto-bump-external-plugins:README.md', cwd=repo).strip(), version)
                self.assertEqual(run('git', 'rev-parse', 'origin/main', cwd=repo), original)
                # Strict protection requires merge-only refreshes to reach the
                # remote even when the generated files match the existing PR.
                ancestor = subprocess.run(['git', 'merge-base', '--is-ancestor', 'origin/main', 'origin/chore/auto-bump-external-plugins'], cwd=repo)
                self.assertEqual(ancestor.returncode, 0)
                if iteration == 1:
                    run('git', 'switch', 'main', cwd=repo)
                    (repo / 'unrelated.txt').write_text('main advanced\n')
                    run('git', 'add', 'unrelated.txt', cwd=repo)
                    run('git', 'commit', '-qm', 'unrelated main change', cwd=repo)
                    run('git', 'push', 'origin', 'main', cwd=repo)
                    original = run('git', 'rev-parse', 'main', cwd=repo)


if __name__ == '__main__':
    unittest.main()
