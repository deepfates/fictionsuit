import os


base_path = "./fictionsuit/.fic"


class FictionScript:
    def __init__(self, lines, source=None, name=None):
        self.lines = [l.rstrip("\n") for l in lines]
        self.source = source
        self.name = name  # TODO: the FictionScript type should be responsible for determining script names from filenames

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

    def sm_schematize(self):
        return {
            "schema": "script",
            "language": "fictionscript",
            "code": "\n".join(self.lines),
            "source_file": self.source if self.source else self.name,
        }

    async def sm_inspect(self, _):
        top_comments = []
        for line in self.lines:
            if line.startswith("#"):
                top_comments.append(line[1:])
            else:
                break
        doc = "\n".join(top_comments)
        return f"FictionScript **{self.name}**\n```\n{doc}\n```"

    async def sm_dump(self, _):
        return "\n".join(f"{i+1: >3} {line}" for i, line in enumerate(self.lines))

    async def sm_default(self, _):
        return f"TODO: make the default action run a script"

    async def sm_save(self, path):
        path = os.path.join(base_path, path)
        with open(path, "w") as f:
            f.write("\n".join(self.lines))
            f.write("\n")

    def __str__(self):
        return f"FictionScript {self.name}"

    def __repr__(self):
        return f"<FictionScript {self.name}>"

    def from_file(filename, script_name):
        with open(filename, "r") as file:
            lines = file.readlines()
            return FictionScript(lines, source=filename, name=script_name)
