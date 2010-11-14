Scrap'in on my Scrapper Screen
==============================

In memory vt102 emulator that lacks every feature I don't personally need. This
project only exists to facilitate cheating more effectively at nethack via my
other recent project, [noobhack](https://github.com/samfoo/noobhack).

Usage
=====

Well, when this thing actually works, it should look something like this:

    >>> import vt102
    >>> stream = vt102.stream()
    >>> screen = vt102.screen((24,80))
    >>> screen.attach(stream)
    >>> stream.process(u"\u001b7\u001b[?47h\u001b)0\u001b[H\u001b[2J\u001b[H\u001b[2;1HNetHack, Copyright 1985-2003\r\u001b[3;1H         By Stichting Mathematisch Centrum and M. Stephenson.\r\u001b[4;1H         See license for details.\r\u001b[5;1H\u001b[6;1H\u001b[7;1HShall I pick a character's race, role, gender and alignment for you? [ynq] ")
    >>> print screen

        "NetHack, Copyright 1985-2003                                                    "
        "         By Stichting Mathematisch Centrum and M. Stephenson.                   "
        "         See license for details.                                               "
        "                                                                                "
        "                                                                                "
        "Shall I pick a character's race, role, gender and alignment for you? [ynq]      "
    >>> 
        
