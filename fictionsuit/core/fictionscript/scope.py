from __future__ import annotations

from uuid import uuid4
from .schematize import schematize


class Scope:
    def __init__(
        self, name: str | None = None, parent: Scope = None, vars: dict | None = None
    ):
        self.parent = parent
        self.vars = vars if vars else {}
        self.name = name
        self.id = uuid4()
        self._has_defaulting_args = False

    def sm_schematize(self):
        vars = {k: schematize(self.vars[k]) for k in self.vars}

        return {
            "schema": "scope",
            "name": self.name,
            "content": vars,
            "parent_id": self.parent.id if self.parent else None,
            "id": self.id,
        }

    def full_name(self):
        if self.name is None:
            if self.parent is None:
                return "(base)"
            else:
                return f"{self.parent.name} > anon"
        else:
            if self.parent is None:
                return f"{self.name}"
            else:
                return f"{self.parent.name} > {self.name}"

    def recontextualize(self, new_name, new_parent):
        self.parent = new_parent
        self.name = new_name

    async def sm_dump(self, _):
        if len(self.vars) == 0:
            return f"{self.full_name()}\n```\nEmpty scope.\n```"
        longest = max([len(key) for key in self.vars])
        keys = self.vars
        if longest > 25:
            longest = 25
            keys_l = {f"{k[:22]}...": keys[k] for k in keys if len(k) > 25}
            keys_s = {k: keys[k] for k in keys if len(k) <= 25}
            keys = {**keys_l, **keys_s}
        dump = [
            f"{' ' * (1 + longest - len(key))}{{{key}}} : {keys[key]}" for key in keys
        ]
        dump_split = []
        for line in dump:
            while len(line) > 80:
                if "\n" in line:
                    index = line.index("\n")
                    if index < 80:
                        dump_split.append(line[:index])
                        after = line[index + 1 :]
                        line = f"{' ' * (5 + longest)} {after}"
                        continue
                dump_split.append(line[:80])
                line = f"{' ' * (5 + longest)} {line[80:]}"
            dump_split.append(line)
        result = "\n".join(dump_split)
        return f"Scope {self.full_name()}\n```\n{result}\n```"

    async def sm_inspect(self, _):
        if len(self.vars) == 0:
            return f"{self.full_name()}\n```\nEmpty scope.\n```"
        vars = "\n".join(f"  {k}" for k in self.vars)
        return f"{self.full_name()}\n```\n{vars}\n```"

    async def sm_default(self, _):
        return f"TODO: make the default action run a script"

    def __str__(self):
        return f"[Scope] {self.full_name()} >"

    def __repr__(self):
        return f"[Scope] {self.full_name()} >"

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
                    f"{pfx} {var}".lstrip(): s.vars[var]
                    for var in s.vars
                    if not isinstance(s.vars[var], Scope)
                }
                scopes = {
                    f"{pfx} {var}".lstrip(): s.vars[var]
                    for var in s.vars
                    if isinstance(s.vars[var], Scope)
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

            vars = {**get_child_vars(self, "", visited), **self.vars}
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
