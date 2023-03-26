class FictionScript:
    def __init__(self, lines, source=None, name=None):
        self.lines = lines
        self.source = source
        self.name = name  # TODO: the FictionScript type should be responsible for determining script names from filenames...

        arg_lines = [
            line
            for line in lines
            if line.startswith("arg ") or line.startswith("args ")
        ]
        self.args = []
        for arg_line in arg_lines:
            if arg_line[3] == "s":  # args
                self.args.extend(x.strip() for x in arg_line[5:].split(","))
            else:  # arg
                if ":=" in arg_line:
                    self.args.append(arg_line[4:].split(":=", maxsplit=1)[0].strip())
                else:
                    self.args.append(arg_line[4:].split("=", maxsplit=1)[0].strip())

    def __str__(self):
        return f"FictionScript {self.name}"

    def __repr__(self):
        return f"<FictionScript {self.name}>"

    def from_file(filename, script_name):
        with open(filename, "r") as file:
            lines = file.readlines()
            return FictionScript(lines, source=filename, name=script_name)
