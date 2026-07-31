# Source - https://stackoverflow.com/a/39215961
# Posted by shellcat_zero, modified by community. See post 'Timeline' for change history
# Retrieved 2026-07-31, License - CC BY-SA 4.0

class StreamToLogger(object):
    """
    Fake file-like stream object that redirects writes to a logger instance.
    """
    def __init__(self, logger, level):
       self.logger = logger
       self.level = level
       self.linebuf = ''

    def write(self, buf):
       for line in buf.rstrip().splitlines():
          self.logger.log(self.level, line.rstrip())

    def flush(self):
        pass
