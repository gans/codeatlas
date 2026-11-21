from pathlib import Path
import shutil
import subprocess

repo = Path('.fixture-repo')
if not (repo / '.git').exists():
    shutil.copytree('fixtures/repository', repo, dirs_exist_ok=True)
    def git(*args): subprocess.run(['git', '-C', str(repo), *args], check=True, stdout=subprocess.DEVNULL)
    git('init', '-q')
    git('add', '.')
    git('-c', 'user.name=CodeAtlas Fixture', '-c', 'user.email=fixture@example.invalid', 'commit', '-qm', 'Fixture')
