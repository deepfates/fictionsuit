from __future__ import annotations


class Scope:
    def __init__(
        self, name: str | None = None, parent: Scope = None, vars: dict | None = None
    ):
        self.parent = parent
        self.vars = vars if vars else {}
        if name is None:
            if parent is None:
                self.name = "| base"
            else:
                self.name = f"{parent.name} > anon"
        else:
            if parent is None:
                self.name = f"| {name}"
            else:
                self.name = f"{parent.name} > {name}"
        self._has_defaulting_args = False

    def __str__(self):
        return f"Scope {self.name} >"

    def __repr__(self):
        return f"<Scope {self.name}>"

    def move_up(self, k):
        self.parent[k] = self[k]

    def get_vars(self, with_children=True) -> dict:
        if with_children:
            vars = self.vars

            def get_child_vars(s: Scope, pfx: str):
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
                        get_child_vars(scopes[scope_name], f"{scope_name} >")
                    )
                return scope_vars

            vars = {**get_child_vars(self, f"|"), **self.vars}
        else:
            vars = self.vars

        # Pull in vars from outer scope, override any collisions
        if self.parent is not None:
            return {**self.parent.get_vars(with_children=False), **vars}

        return vars

    def __setitem__(self, k, v):
        self.vars[k] = v

    def __contains__(self, k):
        return self.get_vars().__contains__(k)

    def __getitem__(self, k):
        return self.get_vars()[k]
