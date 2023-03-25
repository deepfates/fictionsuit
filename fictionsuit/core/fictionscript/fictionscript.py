class FictionScript:
    def __init__(self, lines, source=None):
        self.lines = lines
        self.source = source

    def from_file(filename):
        with open(filename, "r") as file:
            lines = file.readlines()
            return FictionScript(lines, source=filename)
