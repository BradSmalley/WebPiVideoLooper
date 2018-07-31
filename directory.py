# Copyright 2015 Adafruit Industries.
# Author: Tony DiCola
# License: GNU GPLv2, see LICENSE.txt
import os
import re


class DirectoryReader(object):

    def __init__(self, config):
        """Create an instance of a file reader that just reads a single
        directory on disk.
        """
        self._player_name = config.get('web_pi_video_looper', 'video_player')
        self._paths = config.get('directory', 'path').translate(str.maketrans('', '', ' \t\r\n.')).split(',')
        self._extensions = config.get(self._player_name, 'extensions').translate(str.maketrans('', '', ' \t\r\n.')).split(',')
        self._movies = self._get_movies()

    def search_paths(self):
        """Return a list of paths to search for files."""
        return self._paths

    def is_changed(self):
        """Return true if the file search paths have changed."""
        current = self._get_movies()
        if self._movies == current:
            # No new movies were found. Return False.
            return False
        else:
            # New movies were found.  Make the new list of movies the new standard to check against and return True
            self._movies = current
            return True

    def idle_message(self):
        """Return a message to display when idle and no files are found."""
        return 'No files found in {0}'.format(self.search_paths())

    def _get_movies(self):
        # Enumerate all movie files inside those paths.
        movies = []
        for ex in self._extensions:
            for path in self.search_paths():
                # Skip paths that don't exist or are files.
                if not os.path.exists(path) or not os.path.isdir(path):
                    continue
                # Ignore hidden files (useful when file loaded on usb
                # key from an OSX computer
                movies.extend(['{0}/{1}'.format(path.rstrip('/'), x)
                               for x in os.listdir(path)
                               if re.search('\.{0}$'.format(ex), x, flags=re.IGNORECASE) and x[0] is not '.'])
        return movies


def create_file_reader(config):
    """Create new file reader based on reading a directory on disk."""
    return DirectoryReader(config)
