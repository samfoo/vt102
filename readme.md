![https://travis-ci.org/samfoo/vt102](https://travis-ci.org/samfoo/vt102.svg)

# vt102

[vt102](http://github.com/samfoo/vt102) is an in memory vt1xx terminal
emulator. It supports all the most common terminal escape sequences, including
text attributes and color. 

It's an in memory vt1XX-compatible terminal emulator. The *XX* stands for a
series video terminals, developed by
[DEC](http://en.wikipedia.org/wiki/Digital_Equipment_Corporation) between 1970
and 1995. The first, and most famous one, was VT100 terminal, which is now a
de-facto standard for all virtual terminal emulators.
[vt102](http://github.com/samfoo/vt102) is one such emulator.

Why would you want to use a terminal emulator?

* Screen scraping some terminal or curses app.
* Writing your own graphical terminal emulator.
* ... seriously, that's about it.

## Installation

Installation from pypi:

    pip install vt102

Installation from source:

    git clone https://github.com/samfoo/vt102.git
    cd vt102 && python setup.py install

## Usage

There are two important classes in vt102: screen and stream. The screen is the
terminal screen emulator. It maintains an in-memory buffer of text and 
text-attributes to display on screen.

The stream is the stream processor. It manages the state of the input and
dispatches events to anything that's listening about things that are going on.
Events are things like 'linefeed', 'print "a"', or 'cursor-position 10,10'. See
the API for more details.

In general, if you just want to know what's being displayed on screen you can
do something like the following:

    >>> import vt102
    >>> stream = vt102.stream()
    >>> screen = vt102.screen((24,80))
    >>> screen.attach(stream)
    >>> stream.process(u"\u001b7\u001b[?47h\u001b)0\u001b[H\u001b[2J\u001b[H" +
    ...                u"\u001b[2;1HNetHack, Copyright 1985-2003\r\u001b[3;1" +
    ...                u"H         By Stichting Mathematisch Centrum and M. " +
    ...                u"Stephenson.\r\u001b[4;1H         See license for de" +
    ...                u"tails.\r\u001b[5;1H\u001b[6;1H\u001b[7;1HShall I pi" +
    ...                u"ck a character's race, role, gender and alignment f" +
    ...                u"or you? [ynq] ")
    >>> print(screen)
    ["                                                                                ",
     "NetHack, Copyright 1985-2003                                                    ",
     "         By Stichting Mathematisch Centrum and M. Stephenson.                   ",
     "         See license for details.                                               ",
     "                                                                                ",
     "                                                                                ",
     "Shall I pick a character's race, role, gender and alignment for you? [ynq]      ",
     "                                                                                ",
     "                                                                                ",
     "                                                                                ",
     "                                                                                ",
     "                                                                                ",
     "                                                                                ",
     "                                                                                ",
     "                                                                                ",
     "                                                                                ",
     "                                                                                ",
     "                                                                                ",
     "                                                                                ",
     "                                                                                ",
     "                                                                                ",
     "                                                                                ",
     "                                                                                ",
     "                                                                                "]
