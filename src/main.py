# main.py
#
# Copyright 2022 Lorenzo Paderi
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import sys
import gi
import logging
import os

from .lib.terminal import sh
from .lib.utils import log, get_gsettings
from .lib.costants import APP_ID, APP_NAME
from .providers.providers_list import appimage_provider
from .GearleverWindow import GearleverWindow
from  .WelcomeScreen import WelcomeScreen
from .preferences import Preferences

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')

from gi.repository import Gtk, Gio, Adw, Gdk, GLib, GObject # noqa

LOG_FILE_MAX_N_LINES = 5000
LOG_FOLDER = GLib.get_user_cache_dir() + '/logs'

class GearleverApplication(Adw.Application):
    """The main application singleton class."""

    def __init__(self, version):
        super().__init__(application_id=APP_ID, flags=Gio.ApplicationFlags.HANDLES_OPEN)
        self.create_action('about', self.on_about_action)
        self.create_action('preferences', self.on_preferences_action)
        self.create_action('open_log_file', self.on_open_log_file)
        self.win = None
        self.version = version

    def do_startup(self):
        log('\n\n---- Application startup')
        Adw.Application.do_startup(self)

        css_provider = Gtk.CssProvider()
        css_provider.load_from_resource(f'/it/mijorus/{APP_NAME}/assets/style.css')
        Gtk.StyleContext.add_provider_for_display(Gdk.Display.get_default(), css_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

    def do_activate(self, from_file=False):
        """Called when the application is activated.

        We raise the application's main window, creating it if
        necessary.
        """
        self.win = self.props.active_window

        if not self.win:
            self.win = GearleverWindow(application=self, from_file=from_file)

            # if True:
            if not get_gsettings().get_boolean('first-run'):
                get_gsettings().set_boolean('first-run', True)
                tutorial = WelcomeScreen()
                tutorial.present()

        self.win.present()

    def do_open(self, files: list[Gio.File], n_files: int, data):
        if files and appimage_provider.can_install_file(files[0]):
            self.do_activate(from_file=True)
            self.win.on_selected_local_file(files[0])

    def on_about_action(self, widget, data):
        about = Adw.AboutWindow(
            application_name='Gear lever',
            version=self.version,
            developers=['Lorenzo Paderi'],
            copyright='2023 Lorenzo Paderi',
            application_icon='it.mijorus.gearlever',
            issue_url='https://github.com/mijorus/gearlever',
        )

        about.present()

    def on_preferences_action(self, widget, _):
        """Callback for the app.preferences action."""
        pref = Preferences()
        pref.present()

    def create_action(self, name, callback, shortcuts=None):
        """Add an application action.

        Args:
            name: the name of the action
            callback: the function to be called when the action is
            activated
            shortcuts: an optional list of accelerators
        """
        action = Gio.SimpleAction.new(name, None)
        action.connect("activate", callback)
        self.add_action(action)
        if shortcuts:
            self.set_accels_for_action(f"app.{name}", shortcuts)

    def on_open_log_file(self, widget, event):
        if not self.win:
            return

        #!TODO: replace with a portal call
        sh(['xdg-open',  GLib.get_user_cache_dir() + '/logs'])

def main(version):
    """The application's entry point."""

    log_file = f'{LOG_FOLDER}/{APP_NAME}.log'

    if not os.path.exists(LOG_FOLDER):
         os.makedirs(LOG_FOLDER)

    print('Logging to file ' + log_file)

    # Clear log file if it's too big
    log_file_size = 0
    if os.path.exists(log_file): 
        with open(log_file, 'r') as f:
            log_file_size = len(f.readlines())
        
        if log_file_size > LOG_FILE_MAX_N_LINES:
            with open(log_file, 'w+') as f:
                f.write('')

    app = GearleverApplication(version)
    logging.basicConfig(
        filename=log_file,
        filemode='a',
        encoding='utf-8',
        level= logging.DEBUG if get_gsettings().get_boolean('debug-logs') else logging.INFO,
        force=True
    )

    return app.run(sys.argv)
