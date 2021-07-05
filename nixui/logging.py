import os
import threading
import logging


logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.WARNING)
logger = logging.getLogger('nix-gui')


# modified version of from https://github.com/bluec0re/python-helperlib/
class LogPipe(threading.Thread):
    def __init__(self, level):
        """Setup the object with a logger and a loglevel
        and start the thread
        """
        super(LogPipe, self).__init__(name='LogPipe')
        self.daemon = False
        self.level = logging._checkLevel(level)
        self.fdRead, self.fdWrite = os.pipe()
        self.pipeReader = os.fdopen(self.fdRead)
        self._finished = threading.Event()
        self.start()

    def fileno(self):
        """Return the write file descriptor of the pipe
        """
        return self.fdWrite

    def run(self):
        """Run the thread, logging everything.
        """
        self._finished.clear()
        for line in iter(self.pipeReader.readline, ''):
            logger.log(self.level, line.strip('\n'))

        self.pipeReader.close()
        self._finished.set()

    def close(self):
        """Close the write end of the pipe.
        """
        os.close(self.fdWrite)
        self._finished.wait()

    def __enter__(self):
        return self

    def __exit__(self, *args, **kwargs):
        self.close()
