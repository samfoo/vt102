"""Moves cursor down one line in same column. If cursor is at bottom margin, 
screen performs a scroll-up."""
IND = 0x44

"""Moves cursor up one line in same column. If cursor is at top margin, screen 
performs a scroll-down."""
RI = 0x4d

"""Moves cursor to first position on next line. If cursor is at bottom margin, 
screen performs a scroll-up."""
NEL = 0x45

"""Saves cursor position, character attribute (graphic rendition), character 
set, and origin mode selection. (See restore cursor)."""
DECSC = 0x37

"""Restores previously saved cursor position, character attribute (graphic 
rendition), character set, and origin mode selection. If none were saved, the c
ursor moves to home position."""
DECRC = 0x38
