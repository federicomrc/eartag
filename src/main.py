# main.py
#
# Copyright 2022 knuxify
#
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE X CONSORTIUM BE LIABLE FOR ANY
# CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
# TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
# SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#
# Except as contained in this notice, the name(s) of the above copyright
# holders shall not be used in advertising or otherwise to promote the sale,
# use or other dealings in this Software without prior written
# authorization.

import sys
import gi
import os.path

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')

from gi.repository import Adw, Gtk, Gio

from .common import is_valid_music_file
from .window import EartagWindow
from .file import EartagFileManager

class Application(Adw.Application):
    def __init__(self, version='dev'):
        super().__init__(application_id='app.drey.EarTag',
                         resource_base_path='/app/drey/EarTag',
                         flags=Gio.ApplicationFlags.HANDLES_OPEN)
        self.version = version
        self.paths = []
        self.connect('open', self.on_open)

    def on_open(self, window, files, *args):
        for file in files:
            path = file.get_path()
            if path:
                if not os.path.exists(path) or not is_valid_music_file(path):
                    continue
                self.paths.append(path)
        self.do_activate()

    def do_activate(self):
        win = self.props.active_window
        if not win:
            win = EartagWindow(application=self, paths=self.paths)
        self.create_action('about', self.on_about_action)
        self.create_action('open_file', self.on_open_file_action)
        self.set_accels_for_action('app.open_file', ('<Ctrl>o', None))
        self.create_action('save', self.on_save_action)
        self.set_accels_for_action('app.save', ('<Ctrl>s', None))
        win.present()
        self._ = _

    def on_save_action(self, widget, _):
        self.get_active_window().file_view.save()

    def on_about_action(self, widget, _):
        about = Adw.AboutWindow(
            application_name="Ear Tag",
            application_icon="app.drey.EarTag",
            developers=["knuxify"],
            artists=["Igor Dyatlov"],
            license_type=Gtk.License.MIT_X11,
            issue_url="https://github.com/knuxify/eartag/issues",
            version=self.version,
            website="https://github.com/knuxify/eartag"
        )

        if self._('translator-credits') != 'translator-credits':
            # TRANSLATORS: Add your name/nickname here
            about.props.translator_credits = self._('translator-credits')

        lib_versions = []

        lib_versions.append(f"gtk4: {Gtk.get_major_version()}.{Gtk.get_minor_version()}.{Gtk.get_micro_version()}")
        lib_versions.append(f"libadwaita: {Adw.get_major_version()}.{Adw.get_minor_version()}.{Adw.get_micro_version()}")

        import taglib
        lib_versions.append(f"pytaglib: {taglib.version}")
        import eyed3
        lib_versions.append(f"eyed3: {eyed3.version}")
        import magic
        try:
            lib_versions.append(f"libmagic: {magic.version()}")
        except NotImplementedError:
            lib_versions.append(f"libmagic: version data N/A")
        try:
            import mutagen
        except ImportError:
            lib_versions.append("mutagen: not available")
        else:
            lib_versions.append(f"mutagen: {mutagen.version_string}")
        try:
            import PIL
        except ImportError:
            lib_versions.append("pillow: not available")
        else:
            lib_versions.append(f"pillow: {PIL.__version__}")

        lib_version_str = '\n - '.join(lib_versions)

        opened_file_list = []
        for file in self.props.active_window.file_manager.files:
            opened_file_list.append(f'{os.path.split(file.path)[-1]}, {magic.Magic(mime=True).from_file(file.path)}, {file.__gtype_name__}')

        opened_file_list_str = '\n - '.join(opened_file_list) or 'None'

        about.set_debug_info(f'''Ear Tag {self.version}

Running in Flatpak: {os.path.exists('/.flatpak-info') and 'YES' or 'NO'}

Dependency versions:
 - {lib_version_str}

Opened files:
 - {opened_file_list_str}''')

        about.set_modal(True)
        about.set_transient_for(self.props.active_window)

        about.present()

    def on_open_file_action(self, widget, _):
        window = self.get_active_window()
        window.open_mode = EartagFileManager.LOAD_OVERWRITE
        window.show_file_chooser()

    def create_action(self, name, callback):
        """ Add an Action and connect to a callback """
        action = Gio.SimpleAction.new(name, None)
        action.connect("activate", callback)
        self.add_action(action)


def main(version):
    app = Application(version)
    return app.run(sys.argv)
