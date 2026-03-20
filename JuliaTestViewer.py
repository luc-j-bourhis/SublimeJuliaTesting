from pathlib import Path
import shutil
import re
import subprocess
from datetime import datetime
import tempfile

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
            "file_regex": r"^\s*@.*?([~.]?/.+):(\d+)",
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
            sublime.error_message(
                "You need at least one folder in your window to run Julia tests!")
        packages = [p for p in [plugincore.JuliaPackage(f) for f in folders] if p.is_valid]
        if len(packages) > 1:
            sublime.error_message("You have more than one Project.toml in your window!")
        self.test_runner = plugincore.ReTestRunner(packages[0])
        show_julia_console(self.window)
        
    def run_tests(self, *args, **kwds):
        sublime.set_timeout_async(
            lambda args=args, kwds=kwds: self.test_runner.run(*args, **kwds))
        

class JuliaRunAllTestsCommand(JuliaRunTestsCommand):
    """ Run all tests """

    def run(self):
        self.prepare()
        self.run_tests()


class JuliaRunTestsPersistentCommand(JuliaRunTestsCommand):
    """ Commands that remember the last tests run """

    SETTINGS = "JuliaTestViewer.sublime-settings"

    retest_kwds = dict(verbose=5)

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
        self.prepare()
        self.window.show_input_panel(caption="Select tests:", 
                                     initial_text='',
                                     on_done=self.on_chosen,
                                     on_change=None, on_cancel=None)

    def on_chosen(self, test_choice):
        self.last_choice = test_choice
        self.run_tests(test_choice, **self.retest_kwds)


class JuliaRunLastTestsCommand(JuliaRunTestsPersistentCommand):
    """ Run the last test chosen with `JuliaRunChosenTestsCommand` """

    def run(self):
        self.prepare()
        self.run_tests(self.last_choice, **self.retest_kwds)
