from ..core.fictionscript.fictionscript import FictionScript
from .failure import CommandFailure
from ..core.fictionscript.scope import Scope
from ..core.user_message import UserMessage
from .command_group import CommandGroup, slow_command
from .scripting import (
    COMMA_ESCAPE,
    COMMA_ESCAPE_B,
    Scripting,
    no_preprocessing_after,
)


class Methods(CommandGroup):
    """This group contains commands that expose python methods of objects for use in fictionscript."""

    def inspect_other_groups(self, groups: list[CommandGroup]):
        self.scripting_group = None
        for group in groups:
            if isinstance(group, Scripting):
                self.scripting_group = group
        if self.scripting_group is None:
            self._scope = Scope()

    async def intercept_content(self, content: str) -> str:
        """Convert `<method name @ scope name> and so on` to
        `_obj_method method name ``OBJ scope name` and so on."""
        content = content.strip()
        if not content.startswith("<"):
            return content
        split = [x.strip() for x in content[1:].split(">", maxsplit=1)]
        if len(split) == 2:
            message = split[1]
        else:
            message = None
        method_and_object = split[0]
        method_object_split = [
            x.strip() for x in method_and_object.split("@", maxsplit=1)
        ]
        if len(method_object_split) < 2:
            method = "default"
            object = method_object_split[0]
            if object.endswith("++"):
                object = object[:-2].rstrip()
                method = "increment"
            elif object.endswith("+"):
                object = object[:-1].rstrip()
                method = "add"
            elif object.endswith("--"):
                object = object[:-2].rstrip()
                method = "decrement"
            elif object.endswith("-"):
                object = object[:-1].rstrip()
                method = "subtract"
            elif object.endswith("??"):
                object = object[:-2].rstrip()
                method = "dump"
            elif object.endswith("?"):
                object = object[:-1].rstrip()
                method = "inspect"
        else:
            method = method_object_split[0]
            object = method_object_split[1]
        message = "" if message is None else f"``MSG {message}"
        return f"_obj_method {method} ``OBJ {object} {message}"

    def _get_scope(self) -> Scope:
        return (
            self.scripting_group.vars
            if self.scripting_group is not None
            else self._scope
        )

    def _get_var_formatter(self):
        return (
            self.scripting_group.var_formatter
            if self.scripting_group is not None
            else None
        )

    @slow_command
    @no_preprocessing_after("``MSG")
    async def cmd__obj_method(self, message: UserMessage, args: str):
        """Call a script method on an object, if it exists.
        For a high-level "how do I actually use this" sort of explanation, check the "methods" section of `fic/README.md`.
        Usage:
        If you don't have to, you should not use this command (or any other command that starts with an underscore) directly. There is a much more user-friendly syntax for calling methods, which gets automatically converted into an invocation of this command.
        `_obj_method {method name} ``OBJ {object name} ``MSG {message}`
        {object name} will first be interpreted as a variable in the current scope.
        If no such variable is found, it will be interpreted as a variable in the `fic` scope.
        If the object is a `FictionScript` object and the method is `default`, the script will be executed, with {message} as its arguments.
        If the object is a scope, the method will be interpreted as the name of a fictionscript within that scope, which will be executed, with {message} as its arguments.
        If the object is not a scope, then "sm_" will be prepended to the method name, and an async method with one argument (the message) will be called.
        """
        split = [x.strip() for x in args.split("``OBJ", maxsplit=1)]
        if len(split) < 2:
            return CommandFailure("A method and object must be specified.")
        method = split[0]
        object = split[1]
        split = [x.strip() for x in object.split("``MSG", maxsplit=1)]
        object = split[0]
        method_args = None
        if len(split) == 2:
            method_args = split[1].replace("\\n", "\n")
        scope = self._get_scope()

        specials = [
            "default",
            "inspect",
            "dump",
            "increment",
            "decrement",
            "add",
            "subtract",
        ]

        if object not in scope:
            if object == ".":
                obj = self._get_scope()
            elif method in specials and object in self.scripting_group.vars["fic"]:
                obj = self.scripting_group.vars["fic"][object]
            else:
                return CommandFailure(f"Object `{object}` not found.")
        else:
            obj = scope[object]

        fic_command = None
        execution_scope = scope

        if isinstance(obj, FictionScript):
            if method_args is None:
                method_args = ""
            if method == "default":
                fic_command = f"fic {object}: {method_args}"
        elif isinstance(obj, Scope):
            if method in obj:
                if isinstance(obj[method], FictionScript):
                    if self.scripting_group is None:
                        return CommandFailure(
                            "Cannot execute a script, as there is no scripting command group."
                        )
                    if method_args is None:
                        method_args = ""
                    fic_command = f"fic {method}: {method_args}"
                    execution_scope = obj
                else:
                    return CommandFailure(f"{object} . {method} is not a script.")
            else:
                return CommandFailure(f'No "{method}" found in scope "{object}".')

        if fic_command is not None:
            self.scripting_group.vars = execution_scope
            fic_command = await self.scripting_group.intercept_content(fic_command)
            result = await self.scripting_group._evaluate(
                message, fic_command, "scope method"
            )
            self.scripting_group._return_to_scope(scope)
            return result

        sm_method = f"sm_{method}"
        if not hasattr(obj, sm_method):
            return CommandFailure(
                f"Object `{object}` has no script method `{sm_method}`."
            )

        handler = getattr(obj, sm_method)

        if method_args is None:
            return await getattr(obj, sm_method)("")

        content = method_args
        unchanged = ""

        if hasattr(handler, "no_preprocessing_after"):
            after = handler.no_preprocessing_after
            unless = handler.unless
            if after == "":
                split = ["", content]
            else:
                split = None
                try:
                    unless_index = content.index(unless)
                except:
                    unless_index = -1
                if unless_index != -1:
                    try:
                        after_index = content.index(after)
                    except:
                        after_index = -1
                    if unless_index < after_index:
                        split = [content]
                if split is None:
                    split = content.split(after, maxsplit=1)
            if len(split) > 1:
                unchanged = f"{after} {split[1].lstrip()}".lstrip()
            content = split[0].rstrip()

        if hasattr(handler, "escape_commas"):
            content = content.replace("\\,", COMMA_ESCAPE)
            content = content.replace(",", COMMA_ESCAPE_B)
        try:
            formatter = self._get_var_formatter()
            content = formatter.format(content, **self._get_scope().get_vars())
        except KeyError as k:
            return CommandFailure(f"No such variable: {k}")
        if hasattr(handler, "escape_commas"):
            content = content.replace(",", COMMA_ESCAPE)
            content = content.replace(COMMA_ESCAPE_B, ",")

        method_args = f"{content} {unchanged}".strip()

        return await getattr(obj, sm_method)(method_args)
