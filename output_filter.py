import sys
import re
from contextlib import contextmanager

class FilteredStream:
    def __init__(self, original_stream):
        self.original_stream = original_stream
        self.buffer = ''
        # Pattern to match messages we want to suppress
        self.pattern = re.compile(r"Model .* already exists at .*")

    def write(self, message):
        # Append the message to the buffer
        self.buffer += message
        # Check for newlines to process complete lines
        while '\n' in self.buffer:
            line, self.buffer = self.buffer.split('\n', 1)
            self.process_line(line + '\n')
        # If progress bar uses carriage return, process those lines as well
        if '\r' in self.buffer:
            line, self.buffer = self.buffer.split('\r', 1)
            self.process_line(line + '\r')

    def flush(self):
        if self.buffer:
            self.process_line(self.buffer)
            self.buffer = ''
        self.original_stream.flush()

    def process_line(self, line):
        if self.pattern.match(line.strip()):
            # Suppress this line
            return
        else:
            self.original_stream.write(line)
            self.original_stream.flush()

@contextmanager
def filter_specific_output():
    """A context manager that filters out specific output during model initialization."""
    original_stdout = sys.stdout
    original_stderr = sys.stderr
    sys.stdout = FilteredStream(original_stdout)
    sys.stderr = FilteredStream(original_stderr)
    try:
        yield
    finally:
        sys.stdout = original_stdout
        sys.stderr = original_stderr
