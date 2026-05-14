from pathlib import Path
import shutil
import re
import subprocess
from datetime import datetime
import tempfile
import re

import sublime
import sublime_plugin 

from SublimeJuliaTesting import plugincore
    

JULIA_CONSOLE_TAG = "julia_test_console"
JULIA_CONSOLE_NAME = "Console (Julia)"


def show_julia_console(window):
    for view in window.views():
            settings = view.settings()
            if settings.get("terminus_view.tag") == JULIA_CONSOLE_TAG:           
                window.focus_view(view)
                break
    else:
        window.run_command("terminus_open", {
            "cmd": ["tail", "-f", str(plugincore.test_log)],           
            "title": JULIA_CONSOLE_NAME,
            "tag": JULIA_CONSOLE_TAG,
            "focus": True,
            "file_regex": r"^(?:.*Test Failed at |\s*@.*?)([~.]?/.+):(\d+)",
            })



class JuliaRunTestsCommand(sublime_plugin.WindowCommand):
    """
    Base class for all Julia test commands in this module. 
    It encapsulates common behaviour.
    """

    def prepare(self):
        self.window.run_command("save_all")
        folders = self.window.folders()
        if not folders:
            raise RuntimeError(
                "You need at least one folder in your window to run Julia tests!")
        packages = [plugincore.JuliaPackage(f.parent) 
                     for d in folders for f in Path(d).rglob('*.toml')]
        if not packages:
            raise RuntimeError(
                "You need at least one package to run Julia tests!")
        self.test_runners = map(plugincore.ReTestRunner, packages)
        show_julia_console(self.window)
        
    def _run_tests(self, *args, **kwds):
        for runner in self.test_runners:
            runner.run(*args, **kwds)
        
    def run_tests(self, *args, **kwds):
        sublime.set_timeout_async(
            lambda args=args, kwds=kwds: self._run_tests(*args, **kwds))
        

class JuliaRunAllTestsCommand(JuliaRunTestsCommand):
    """ Run all tests """

    def run(self):
        try:
            self.prepare()
        except RuntimeError as err:
            sublime.error_message(str(err))
            return
        self.run_tests()


class JuliaRunTestsPersistentCommand(JuliaRunTestsCommand):
    """ Commands that remember the last tests run """

    SETTINGS = "JuliaTestViewer.sublime-settings"

    @property
    def settings(self):
        return sublime.load_settings(type(self).SETTINGS)

    @property
    def last_choice(self):
        return self.settings.get("last_choice", "")

    @last_choice.setter
    def last_choice(self, value):
        self.settings.set("last_choice", value)
        sublime.save_settings(type(self).SETTINGS)


class JuliaRunChosenTestsCommand(JuliaRunTestsPersistentCommand):
    """ Let the user chose wich tests to run using ReTest selection feature """

    def run(self):
        try:
            self.prepare()
        except RuntimeError as err:
            sublime.error_message(str(err))
            return
        self.window.show_input_panel(caption="Select tests:", 
                                     initial_text='',
                                     on_done=self.on_chosen,
                                     on_change=None, on_cancel=None)

    rx = re.compile(r'^\s* (.+?) \s* (?: ; \s* verbose=(\d) )? $', re.X)
    def on_chosen(self, test_choice):
        if not (m := self.rx.search(test_choice)):
            sublime.error_message("Test choice must be e.g. 'what I want to see; verbose=2, '")
        args = []
        if m[1]:
            args.append(m[1])
        if m[2]:
            args.append(int(m[2]))
        self.last_choice = args
        self.run_tests(*args, **kwds)


class JuliaRunLastTestsCommand(JuliaRunTestsPersistentCommand):
    """ Run the last test chosen with `JuliaRunChosenTestsCommand` """

    def run(self):
        try:
            self.prepare()
        except RuntimeError as err:
            sublime.error_message(str(err))
            return
        args, kwds = self.last_choice
        self.run_tests(*args, **kwds)
