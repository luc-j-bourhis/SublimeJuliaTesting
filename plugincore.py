from pathlib import Path
import re
from textwrap import dedent
import subprocess
import tempfile
import atexit
import shutil
import datetime

class JuliaPackage:
    
    project_toml: Path
    
    package_name_pat = re.compile(r'^name\s*=\s*"(\w+)"')
    
    def __init__(self, folder):
        self.project_toml = Path(folder) / 'Project.toml'
        try:
            with self.project_toml.open() as f:
                for li in f:
                    m = self.package_name_pat.search(li)
                    if m:
                        self.name = m.group(1)
                        break
                else:
                    self.name = None
        except:
            self.name = None
        self.can_test = (self.directory / 'test' / 'runtests.jl').is_file()
        
    @property
    def is_valid(self):
        return self.name is not None
    
    @property
    def directory(self):
        return self.project_toml.parent
    

class TestLog:
    
    path: Path
    
    ansi_escape_pat = re.compile(r'\x1b\[[0-9;]*m')

    def __init__(self):
        self.path = Path(tempfile.mkdtemp()) / 'julia_test_console.log'
        self.path.touch()
        atexit.register(self.cleanup)

    def cleanup(self):
        shutil.rmtree(self.path.parent)
        
    def __str__(self):
        return self.path.as_posix()
    
    def printout(self):
        with self.path.open() as f:
            log = f.read()
        print("."*80)
        print(self.ansi_escape_pat.sub('', log))
        print("."*80)
        
test_log = TestLog()
        
    
class ReTestRunner:
    julia_code = """\
        ARGS = [{retest_args}]
        include("test/runtests.jl")
    """
    
    command = "julia --project=test --color=yes -e"
    
    def __init__(self, package:JuliaPackage):
        self.package = package
    
    def run(self, selection=None, verbose=None):
        if not self.package.can_test:
            return
        header = '**** {title} ({now:%Y-%m-%d %H:%M:%S}) ****'.format(
            title=self.package.name,
            now=datetime.datetime.now())
        with test_log.path.open('a') as f:
            print(file=f)
            print(header, file=f)
            print(file=f)
        retest_args = []
        if selection:
            retest_args.append(f'"{selection}"')
        if verbose:
            retest_args.append(str(verbose))
        retest_args = ', '.join(retest_args)
        julia_code = '; '.join(dedent(self.julia_code).splitlines())
        command = self.command.split() + [julia_code.format(retest_args=retest_args)]
        print(command)
        completed = subprocess.run(command, cwd=self.package.directory,
                                   text=True,
                                   stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        with test_log.path.open('a') as f:
            f.flush()
            print(completed.stdout, file=f)
            f.flush()
        

if __name__ == '__main__':
    import argparse
    p = argparse.ArgumentParser(
        description="Test engine used by Sublime command classes")
    p.add_argument('--project', type=str, required=True, help='Project.toml')
    cmdargs = p.parse_args()
    
    jpack = JuliaPackage(cmdargs.project)
    assert jpack.is_valid
    print(f"Testing with {jpack.project_toml}")
    print("Command:")
    print(ReTestRunner.command)
    print("Julia Code:")
    print(ReTestRunner.julia_code)
    print("Run tests:")
    print()
    test_runner = ReTestRunner(jpack)
    test_runner.run(verbose=2)
    test_runner.run('NROWS', verbose=3)
    test_log.printout()
    print('OK')
    