from __future__ import annotations


class Scope:
    def __init__(
        self, name: str | None = None, parent: Scope = None, vars: dict | None = None
    ):
        self.parent = parent
        self.vars = vars if vars else {}
        if name is None:
            if parent is None:
                self.name = "| (base)"
            else:
                self.name = f"{parent.name} > anon"
        else:
            if parent is None:
                self.name = f"| {name}"
            else:
                self.name = f"{parent.name} > {name}"
        self._has_defaulting_args = False

    def recontextualize(self, new_name, new_parent):
        self.parent = new_parent
        if new_name is None:
            if new_parent is None:
                self.name = "| (base)"
            else:
                self.name = f"{new_parent.name} > anon"
        else:
            if new_parent is None:
                self.name = f"| {new_name}"
            else:
                self.name = f"{new_parent.name} > {new_name}"

    def inspect(self):
        if len(self.vars) == 0:
            return f"{self.name}\n```\nEmpty scope.\n```"
        longest = max([len(key) for key in self.vars])
        dump = [
            f"{' ' * (1 + longest - len(key))}{{{key}}} : {self.vars[key]}"
            for key in self.vars
        ]
        dump_split = []
        for line in dump:
            while len(line) > 80:
                dump_split.append(line[:80])
                line = f"{' ' * (5 + longest)} {line[80:]}"
            dump_split.append(line)
        result = "\n".join(dump_split)
        return f"Scope {self.name}\n```\n{result}\n```"

    def __str__(self):
        return f"[Scope] {self.name} >"

    def __repr__(self):
        return f"[Scope] {self.name} >"

    def move_up(self, k):
        self.parent[k] = self[k]

    def get_vars(self, with_children=True, visited=None) -> dict:
        if visited is None:
            visited = []
        if self in visited:
            return {}
        if with_children:
            vars = self.vars

            def get_child_vars(s: Scope, pfx: str, visited=None):
                if visited == None:
                    visited = []
                if s in visited:
                    return {}
                visited.append(s)
                nonscopes = {
                    f"{pfx} {var}": s.vars[var]
                    for var in s.vars
                    if type(s.vars[var]) is not Scope
                }
                scopes = {
                    f"{pfx} {var}": s.vars[var]
                    for var in s.vars
                    if type(s.vars[var]) is Scope
                }
                scope_vars = {}
                if nonscopes is not None:
                    scope_vars.update(nonscopes)
                if scopes is not None:
                    scope_vars.update(scopes)
                for scope_name in scopes:
                    scope_vars.update(
                        get_child_vars(scopes[scope_name], f"{scope_name} >", visited)
                    )
                return scope_vars

            vars = {**get_child_vars(self, f"|", visited), **self.vars}
        else:
            vars = self.vars

        # Pull in vars from outer scope, override any collisions
        if self.parent is not None:
            return {
                **self.parent.get_vars(with_children=False, visited=visited),
                **vars,
            }

        return vars

    def __setitem__(self, k, v):
        self.vars[k] = v

    def __contains__(self, k):
        return self.get_vars().__contains__(k)

    def __getitem__(self, k):
        return self.get_vars()[k]
