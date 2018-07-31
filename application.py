from flask import Flask
from flask import render_template
from configparser import ConfigParser

import socket
import pygame
import time
import threading
import os
import re

from omxplayer import OMXPlayer
from directory import DirectoryReader
from playlist import Playlist

_config = ConfigParser()  # TODO:  Give command line option
_config.read('WebPiVideoLooper.ini')
app = Flask("__name__")
hostname = socket.gethostname()
ip = socket.gethostbyname(hostname)

pygame.display.init()
pygame.font.init()
pygame.mouse.set_visible(False)
size = (pygame.display.Info().current_w, pygame.display.Info().current_h)
_screen = pygame.display.set_mode(size, pygame.FULLSCREEN)

_stop = False
_player = OMXPlayer(_config)
_interrupt_on_new = True  # TODO: Get from config
_reader = DirectoryReader(_config)
_is_random = False
_small_font = pygame.font.Font(None, 50)
_big_font = pygame.font.Font(None, 250)
_fgcolor = (255, 255, 255)
_bgcolor = (0, 0, 0)

print("Your Computer Name is:" + hostname)
print("Your Computer IP Address is:" + ip)


@app.route("/looper/")
def looper():
    return render_template("index.html", addr=ip)


@app.route("/looper/start/")
def start_looper():
    t = threading.Thread(target=run)
    t.start()

    # TODO:  Start the videos
    return render_template("index.html", addr=ip)


@app.route("/looper/stop/")
def stop_looper():
    # TODO:  Stop the videos
    return render_template("index.html", addr=ip)


def _blank_screen():

    _screen.fill((0, 0, 0))  # TODO: Allow this to be set in ini file
    pygame.display.update()
    # time.sleep(5)
    # pygame.quit()


def run():
    """Main program loop. """
    # Main loop to play videos in the playlist and listen for file changes.
    _running = True
    while _running:
        if _stop:
            print('stop_file found.  Exiting...')
            _player.stop(3)
            return
        # Load and play a new movie if nothing is playing.
        # if not _player.is_playing():
            # if _waiting_to_build_playlist:
            #    playlist = _build_playlist()
            #    _prepare_to_run_playlist(playlist);
            #   _waiting_to_build_playlist = False
            # movie = playlist.get_next()
            # if movie is not None:
            #    # Start playing the first available movie.
            #    print('Playing movie: {0}'.format(movie))
            #   _player.play(movie, loop=False, vol=0)
        # Check for changes in the file search path (like USB drives added)
        # and rebuild the playlist.
        if _reader.is_changed():
            if _interrupt_on_new:
                _player.stop(3)  # Up to 3 second delay waiting for old
                playlist = _build_playlist()
                _prepare_to_run_playlist(playlist)
            else:
                _waiting_to_build_playlist = True
        # Give the CPU some time to do other tasks.
        time.sleep(0.002)


def _build_playlist():
    """Search all the file reader paths for movie files with the provided
    extensions.
    """
    # Get list of paths to search from the file reader.
    paths = _reader.search_paths()
    # Enumerate all movie files inside those paths.
    movies = []
    for ex in _player.supported_extensions():
        for path in paths:
            # Skip paths that don't exist or are files.
            if not os.path.exists(path) or not os.path.isdir(path):
                continue
            # Ignore hidden files (useful when file loaded on usb
            # key from an OSX computer
            movies.extend(['{0}/{1}'.format(path.rstrip('/'), x)
                           for x in os.listdir(path)
                           if re.search('\.{0}$'.format(ex), x,
                                        flags=re.IGNORECASE) and
                           x[0] is not '.'])
            # Get the video volume from the file in the usb key
            # sound_vol_file_path = '{0}/{1}'.format(path.rstrip('/'), self._sound_vol_file)
            # if os.path.exists(sound_vol_file_path):
            #    with open(sound_vol_file_path, 'r') as sound_file:
            #        sound_vol_string = sound_file.readline()
            #        if _is_number(sound_vol_string):
            #            _sound_vol = int(float(sound_vol_string))
    # Create a playlist with the sorted list of movies.
    return Playlist(sorted(movies), _is_random)


def _render_text(message, font=None):
    """Draw the provided message and return as pygame surface of it rendered
    with the configured foreground and background color.
    """
    # Default to small font if not provided.
    if font is None:
        font = _small_font
    return font.render(message, True, _fgcolor, _bgcolor)


def _animate_countdown(playlist):
    """Print text with the number of loaded movies and a quick countdown
    message if the on screen display is enabled.
    """
    # Print message to console with number of movies in playlist.
    message = 'Found {0} movie{1}.'.format(playlist.length(),
                                           's' if playlist.length() >= 2 else '')

    # Read delay time form config - Minimum value is 0, Maximum value is 60
    config_delay = _config.get('web_pi_video_looper', 'delay_seconds')
    seconds = 5
    if _is_number(config_delay):
        seconds = int(float(config_delay))

    if seconds < 0:
        seconds = 0
    elif seconds > 60:
        seconds = 60

    print(message)

    # Draw message with number of movies loaded and animate countdown.
    # First render text that doesn't change and get static dimensions.
    label1 = _render_text(message + ' Starting playback in:')
    label3 = _render_text('Brad Rocks!')
    l3w, l3h = label3.get_size()
    l1w, l1h = label1.get_size()
    sw, sh = _screen.get_size()
    for i in range(seconds, 0, -1):
        # Each iteration of the countdown rendering changing text.
        label2 = _render_text(str(i), _big_font)
        l2w, l2h = label2.get_size()
        # Clear screen and draw text with line1 above line2 and all
        # centered horizontally and vertically.
        _screen.fill(_bgcolor)
        _screen.blit(label1, (sw / 2 - l1w / 2, sh / 2 - l2h / 2 - l1h))
        _screen.blit(label2, (sw / 2 - l2w / 2, sh / 2 - l2h / 2))
        _screen.blit(label3, (sw / 2 - l3w / 2, sh - (l3h + 10)))
        pygame.display.update()
        # Pause for a second between each frame.
        time.sleep(1)


def _idle_message():
    """Print idle message from file reader."""
    # Print message to console.
    message = _reader.idle_message()

    print(message)
    # Display idle message in center of screen.
    label2 = _render_text(ip)
    label = _render_text(message)
    lw, lh = label.get_size()
    l2w, l2h = label2.get_size()
    sw, sh = _screen.get_size()
    _screen.fill(_bgcolor)
    _screen.blit(label, (sw / 2 - lw / 2, sh / 2 - lh / 2))
    _screen.blit(label2, (sw / 2 - l2w / 2, sh - (l2h + 10)))
    pygame.display.update()


def _prepare_to_run_playlist(playlist):
    """Display messages when a new playlist is loaded."""
    # If there are movies to play show a countdown first (if OSD enabled),
    # or if no movies are available show the idle message.
    if playlist.length() > 0:
        _animate_countdown(playlist)
        _blank_screen()
    else:
        _idle_message()


def _is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        return False
