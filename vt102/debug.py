from vt102 import stream

class explainer(stream):
    def dispatch(self, event, *args):
        print("%s %r" % (event, args))
