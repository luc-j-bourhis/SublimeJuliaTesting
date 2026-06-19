from pathlib import Path
import shutil
import re
import os
import subprocess
from datetime import datetime
import tempfile
import atexit

import sublime
import sublime_plugin 

from SublimeJuliaTesting import plugincore
    

JULIA_CONSOLE_TAG = "julia_test_console"
JULIA_CONSOLE_NAME = "Console (Julia)"


class TestLog:
    """ File-like object standing for the log file where testrunner writes """
    
    path: Path
    
    def __init__(self):
        self.path = Path(tempfile.mkdtemp()) / 'julia_test_console.log'
        self.path.touch()
        atexit.register(self.cleanup)

    def cleanup(self):
        shutil.rmtree(self.path.parent)
        
    def open(self):
        return open(self.path, 'a')
    
    def tail_command(self):
        return ["tail", "-f", str(self.path)]
        

test_log = TestLog()


def show_julia_console(window):
    """ Show a console that runs `tail -f` on the log file Julia test runner writes to  """
    for view in window.views():
            settings = view.settings()
            if settings.get("terminus_view.tag") == JULIA_CONSOLE_TAG:           
                window.focus_view(view)
                break
    else:
        window.run_command("terminus_open", {
            "cmd": test_log.tail_command(),           
            "title": JULIA_CONSOLE_NAME,
            "tag": JULIA_CONSOLE_TAG,
            "focus": True,
            "file_regex": r"^(?:.*Test Failed at |\s*@.*?)([~.]?/.+):(\d+)",
            })
        
        
def find_package(filepath:Path):
    """ Find the package a file belongs to """
    previous = None
    current:Path = filepath.parent
    while current != previous:
        if 'Project.toml' in [p.name for p in current.iterdir() if p.is_file()]:
            if current.name != 'test':
                return current
        previous = current
        current = previous.parent
    return None
        
    
def launch_testrunner(package:Path, runtests:Path):
    """ Pass the given runtests.jl to JETLS `testrunner` """
    header = '**** {title} ({now:%Y-%m-%d %H:%M:%S}) ****'.format(
        title=package.name,
        now=datetime.now())
    with test_log.open() as f:
        print(file=f)
        print(header, file=f)
        print(file=f)
    testrunner = Path("~/.julia/bin/testrunner").expanduser()
    command = [testrunner, "--project=test", "--verbose", runtests]
    completed = subprocess.run(command, cwd=package,
                               env=os.environ.update(FORCE_COLOR='yes'),
                               text=True,
                               stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    with test_log.open() as f:
        f.flush()
        print(completed.stdout, file=f)
        f.flush()
                

class JuliaRunTestsCommand(sublime_plugin.WindowCommand):
    """ Sublime text window command to run all tests """

    def run(self):
        self.window.run_command("save_all") 
        file_path = self.window.active_view().file_name()
        if file_path is None:
            sublime.error_message("Save the current buffer and try again!")
            return
        package = find_package(Path(file_path))
        if package is None:
            sublime.error_message("I could not file a package the current file belongs to")
            return
        runtests = package / 'test' / 'runtests.jl'
        if not runtests.is_file():
            sublime.error_message("I could not find `runtests.jl`")
            return
        show_julia_console(self.window)
        sublime.set_timeout_async(
            lambda package=package, runtests=runtests: 
                launch_testrunner(package, runtests))
        