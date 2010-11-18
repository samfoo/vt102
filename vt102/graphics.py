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
