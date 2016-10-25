#!/usr/bin/python3

from gi import require_version

require_version('Gtk', '3.0')
require_version('Vte', '2.91')

import sys, os
from gi.repository import Gtk, Vte, GLib
import tarfile
from shutil import copyfile
# import platform
import subprocess

dvd_mount = '/media/' + sys.argv[1] + '/tealinuxos'
print(dvd_mount)
module_temp = '/tmp/.module-manager-temp'


class ModuleManager(Gtk.Window):
    def __init__(self, arguments):
        Gtk.Window.__init__(self)
        self.set_title('Installing Modules')
        print(arguments)
        box = Gtk.Box(spacing=6, orientation=Gtk.Orientation.VERTICAL)
        self.add(box)

        self.progress_bar = Gtk.ProgressBar()
        self.progress_bar.set_show_text(False)
        box.add(self.progress_bar)

        self.terminal = Vte.Terminal()
        self.terminal.set_size(60, 20)
        self.terminal.connect('contents-changed', self.trigger_pulse)
        box.add(self.terminal)

        # arguments = ['module-manager', 'mnirfan', 'geany.tea,gimp.tea,pycharm.tgz,netbeans.x,qt.x']
        apps = arguments[2].split(',')
        for item in apps:
            if item == "null" or item == "":
                apps.remove(item)
        print(apps)
        self.tea = []
        self.tgz = []
        self.x = []
        for item in apps:
            if item.endswith('.tea'):
                self.tea.append(item)
            elif item.endswith('.tar.gz'):
                self.tgz.append(item)
            elif item.endswith('.sh') or item.endswith('.bin') or item.endswith('.run'):
                self.x.append(item)
        print('teaaaa: ')
        print(self.tea)
        if self.tea != []:
            self.process_tea(self.tea)
        elif self.tgz != []:
            self.process_tgz()
        elif self.x != []:
            self.process_executables()

        self.connect('destroy', Gtk.main_quit)
        self.show_all()

    def trigger_pulse(self, *args):
        self.progress_bar.pulse()

    def process_tea(self, tea_list):
        print('entering process_tea()')
        window_extract = Gtk.Window(title='')
        spinner = Gtk.Spinner()
        spinner.set_margin_top(15)
        spinner.set_margin_bottom(15)
        spinner.set_margin_left(20)
        spinner.set_margin_right(20)
        spinner.start()
        window_extract.add(spinner)
        # window_extract.show_all()
        if self.tgz != []:
            self.terminal.connect('child-exited', self.process_tgz)
            print('connected to process_tgz')
        elif self.x != []:
            print('connected to process_x')
            self.terminal.connect('child-exited', self.process_executables)
        else:
            print('connected to finish')
            self.terminal.connect('child-exited', self.show_finish_message)

        for item in tea_list:
            print(dvd_mount + '/idepack/' + item)
            open_tar = tarfile.open(dvd_mount + '/idepack/' + item, 'r:gz')
            # self.progress_bar.set_text('Extracting ' + item)
            self.trigger_pulse()
            open_tar.extractall(module_temp)
            open_tar.close()
            # while Gtk.events_pending:
            #     Gtk.main_iteration()
        # window_extract.hide()
        packages = []
        for deb in os.listdir(module_temp):
            if deb.endswith('.deb'):
                packages.append(deb)
        # self.show_all()
        self.terminal.spawn_sync(
            Vte.PtyFlags.DEFAULT,
            module_temp,
            ['/usr/bin/sudo', 'dpkg', '-i', '-G'] + packages,
            [],
            GLib.SpawnFlags.DO_NOT_REAP_CHILD,
            None,
            None
        )

    def process_tgz(self, *args):
        # for item in self.tgz:
        if self.tea != []:
            self.terminal.disconnect_by_func(self.process_tgz)
        if self.x != []:
            print('x is not None')
            self.terminal.connect('child-exited', self.process_executables)
        else:
            print('x is None')
            self.terminal.connect('child-exited', self.show_finish_message)
        self.terminal.spawn_sync(
            Vte.PtyFlags.DEFAULT,
            dvd_mount + '/idepack/',
            # http://www.cyberciti.biz/faq/linux-unix-bsd-extract-targz-file/
            # http://hsblog.mexchip.com/en/2010/10/how-to-show-a-progress-bar-when-extracting-a-file/
            ['/usr/bin/file-roller', '-e', '/'] + self.tgz,
            [],
            GLib.SpawnFlags.DO_NOT_REAP_CHILD,
            None,
            None
        )

    def process_executables(self, *args):
        try:
            self.terminal.disconnect_by_func(self.process_tgz)
        except TypeError:
            pass
        try:
            self.terminal.disconnect_by_func(self.process_executables)
        except TypeError:
            pass
        self.terminal.spawn_sync(
            Vte.PtyFlags.DEFAULT,
            module_temp,
            ['/bin/echo', 'please', 'wait...'],
            [],
            GLib.SpawnFlags.DO_NOT_REAP_CHILD,
            None,
            None
        )
        for item in self.x:
            # ========\
            #self.terminal.spawn_sync(
            #   Vte.PtyFlags.DEFAULT,
            #    module_temp,
            #   # ['/usr/bin/rsync', '--progress', dvd_mount + '/idepack/' + item, '/tmp/' + item],
            #   ['/usr/bin/pv', dvd_mount + '/idepack/' + item, '>' ,'/tmp/' + item],
            #   [],
            #   GLib.SpawnFlags.DO_NOT_REAP_CHILD,
            #   None,
            #   None
            #)
            subprocess.Popen('notify-send -t 20000 -i /opt/module-manager.ign/icons/app.png "Module Installer" "Coying files, please wait..."',
                             shell=True, stdout=subprocess.PIPE)
            copyfile(dvd_mount + '/idepack/' + item, '/tmp/'+item)
            command = "chmod +x /tmp/" + item + "; /tmp/" + item
            # ========/
            # command = '"'+dvd_mount+'"' + '/idepack/' + item
            print('command : ' + command)
            process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE)
            process.wait()
        self.show_finish_message()

    def show_finish_message(self, *args):

        message = Gtk.MessageDialog(
            self,
            Gtk.DialogFlags.MODAL,
            Gtk.MessageType.INFO,
            Gtk.ButtonsType.CLOSE, "Modul selesai dipasang"
        )
        message.run()
        message.destroy()
        GLib.idle_add(self.quit)

    @staticmethod
    def quit(*args):
        print('exit triggered')
        Gtk.main_quit()


if __name__ == "__main__":
    ModuleManager(sys.argv)
    Gtk.main()
