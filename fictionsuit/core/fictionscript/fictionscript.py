class FictionScript:
    def __init__(self, lines, source=None):
        self.lines = lines
        self.source = source

        arg_lines = [line for line in lines if line.startswith('arg ') or line.startswith('args ')]
        self.args = []
        for arg_line in arg_lines:
            if arg_line[3] == 's': # args 
                self.args.extend(x.strip() for x in arg_line[5:].split(','))
            else: # arg
                self.args.append(arg_line[4:].split('=', maxsplit=1)[0].strip())

    def from_file(filename):
        with open(filename, "r") as file:
            lines = file.readlines()
            return FictionScript(lines, source=filename)
        
