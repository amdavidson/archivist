
import sys 

class Log():
    LOGLEVEL = 3
    DEST = "stdout"

    def __call__(self, logstring, loglevel=None):
        if loglevel == "error":
            loglevel = 3
        elif loglevel == "warning":
            loglevel = 2
        else:
            loglevel = 1
        if loglevel >= self.LOGLEVEL:
            if self.DEST == "stderr":
                print(logstring, file=sys.stderr)
            else:
                print(logstring)


