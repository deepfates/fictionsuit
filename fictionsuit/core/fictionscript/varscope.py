from __future__ import annotations


class VarScope:
    def __init__(
        self, name: str | None = None, parent: VarScope = None, vars: dict | None = None
    ):
        self.parent = parent
        self.vars = vars if vars else {}
        if name is None:
            if parent is None:
                self.name = "base"
            else:
                self.name = f"{parent.name}_anon"
        else:
            self.name = f"{parent.name}_{name}"

    def move_up(self, k):
        self.parent[k] = self[k]

    def get_vars(self) -> dict:
        if self.parent is not None:
            # Pull in vars from outer scope, override any collisions
            return {**self.parent.get_vars(), **self.vars}
        return self.vars

    def __setitem__(self, k, v):
        self.vars[k] = v

    def __contains__(self, k):
        return self.get_vars().__contains__(k)

    def __getitem__(self, k):
        return self.get_vars()[k]
