import sublime
import sublime_plugin
import os
import datetime
from shutil import copy2


def plugin_loaded():
    """
    Function triggered when reloading plugins
    """

    global autoBackupSettings
    global autoBackuper

    platform = sublime.platform().title()
    if (platform == "Osx"):
        platform = "OSX"
    autoBackupSettings = sublime.load_settings('AutoBackup ('+platform+').sublime-settings')

    autoBackuper = AutoBackupCore()

    AutoBackupLogger.console('Plugin Initialized')


class AutoBackup(sublime_plugin.EventListener):

    def on_load(self, view):
        """
        Backup when opening file
        """

        if not autoBackupSettings.get('backup_on_post_save'):
            return

        autoBackuper.backup(view)

    def on_pre_save(self, view):
        """
        Backup before saving file (only if changed)
        """

        if not autoBackupSettings.get('backup_on_pre_save'):
            return

        if view.is_dirty():
            autoBackuper.backup(view)

    def on_post_save(self, view):
        """
        Backup after saving file
        """

        if not autoBackupSettings.get('backup_on_post_save'):
            return

        autoBackuper.backup(view)


class AutoBackupCore:

    def checks(self, view):
        """
        Pre backup checks
        """

        # If view is readonly
        if (view.is_read_only()):
            AutoBackupLogger.console('Backup not saved, file is readonly.')
            return False

        # If view is empty (or unavailable)
        view_size = view.size()
        if (view_size is None):
            AutoBackupLogger.console('File size not available')
            return False

        # If file size unavailable
        max_backup_file_size = autoBackupSettings.get('max_backup_file_size_bytes')
        if (max_backup_file_size is None):
            AutoBackupLogger.console('Max allowed size from config not available')
            return False

        # If file size exceeded
        if view_size > max_backup_file_size:
            AutoBackupLogger.console('Backup not saved, file too large (%d bytes)' % view.size())
            return False

        # If there is a filename
        if len(view.file_name()) <= 0:
            AutoBackupLogger.console('Invalid filename')
            return False

        # All good
        return True

    def backup(self, view):
        """
        Do the actual backup
        """

        # Check stuff
        if not self.checks(view):
            return

        # File path
        file_path = view.file_name()

        # Keep filename only
        file_name = file_path.rsplit("/", 1)[1]

        # Get current time/date
        now = datetime.datetime.now()

        # Get the preferences backup directory
        bakDir = os.path.expanduser( autoBackupSettings.get('backup_dir') )

        # Add date directory if needed
        if autoBackupSettings.get('backup_path_dir_date'):
            bakDir = os.path.join( bakDir, now.strftime("%Y-%m-%d") )

        # Add filename directory if needed
        if autoBackupSettings.get('backup_path_dir_filename'):
            bakDir = os.path.join( bakDir, file_name )

        # Create folder structure
        if not os.path.isdir(bakDir):
            os.makedirs(bakDir)

        # Build backup file name
        bakFileName = file_name + ".[" + now.strftime("%Y-%m-%d_%H.%M.%S") + "].bak"

        # Build the entire path of the backup file
        bakDir = os.path.join( bakDir,  bakFileName )

        # Copy the file to the backup location
        copy2(file_path, bakDir)

        # Show appropriate message
        if os.path.isfile(bakDir):
            AutoBackupLogger.console('Backup saved @ ' + bakDir)
        else:
            AutoBackupLogger.console('Backup FAILED @ ' + bakDir)


class AutoBackupLogger:

    @staticmethod
    def console(message):
        """
        Print message
        """

        print('AutoBackup:', message)


class AutoBackupCommand(sublime_plugin.TextCommand):

    def run(self, edit):
        """
        Sublime command for manually triggering the backup
        """
        print("bak")
        autoBackuper.backup(view = self.view)