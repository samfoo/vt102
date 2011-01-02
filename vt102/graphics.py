dsg = dict(
    zip(
        [ord(c) for c in "\x60\x61\x66\x67\x6a\x6b\x6c\x6d\x6e\x6f\x70\x71\x72\x73\x74\x75\x76\x77\x78\x7b\x7e"],
        u"\u25c6\u2592\u25cb\u00b1\u2518\u2510\u250c\u2514\u253c\u2500\u2500\u2500\u2500\u2500\u251c\u2524\u2534\u252c\u2502\u03c0\xb7"
    )
)

text = {
    0: "reset",
    24: "underline-off",
    25: "blink-off",
    27: "reverse-off",
    1: "bold" ,
    2: "dim" ,
    4: "underline",
    5: "blink",
    7: "reverse",
}

colors = {
    "foreground": {
        39: "default",
        # This is technically "default with underscore", but I don't understand
        # the utility of mixing the text styling with the colors. Instead I'm 
        # going to just leave it as "default" until I see something buggy or 
        # someone complains.
        38: "default",
        30: "black",
        31: "red",
        32: "green",
        33: "brown",
        34: "blue",
        35: "magenta",
        36: "cyan",
        37: "white",
    },
    "background": {
        49: "default",
        40: "black",
        41: "red",
        42: "green",
        43: "brown",
        44: "blue",
        45: "magenta",
        46: "cyan",
        47: "white",
    }
}
