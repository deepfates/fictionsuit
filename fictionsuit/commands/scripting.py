from __future__ import annotations

import gc
import glob
import ntpath
import os

from ..api_wrap.openai import ChatInstance
from ..core.fictionscript import (
    ExpressionMessage,
    FictionScript,
    Scope,
    ScriptLineMessage,
)
from ..core.user_message import UserMessage
from .command_group import (
    CommandFailure,
    CommandGroup,
    CommandHandled,
    command_split,
    slow_command,
)


class Scripting(CommandGroup):
    def __init__(self, command_groups: list[CommandGroup]):
        self.command_groups = command_groups
        self.vars = Scope()  # TODO: save and load scopes?
        # TODO: Concurrency & scopes might be a mess
        # TODO: add a more general preprocessor outside of Scripting for parsing scripts
        # from a nicer syntax down into runnable commands
        # TODO: maybe add config options for folders instead of just hard-coding things...
        self.load_scripts("fictionsuit/fic")
        self.load_scripts("fictionsuit/.fic")

    async def intercept_content(self, content: str) -> str | CommandFailure:
        """TODO: make this method less of a horrifying mess"""
        (cmd, args) = command_split(content)

        if cmd is None:
            return content

        if cmd[0] == "#":
            return ""  # Comment

        def handle_vertbar(content: str, cmd: str, args: str) -> str:
            if cmd is None:
                return content
            if cmd[0] != "|":
                return content
            if "=" in content:
                if ">" not in content[: content.index("=")]:
                    expansion = "var"
                else:
                    expansion = "insert"
            else:
                if content.strip() == f"|":
                    expansion = "where"
                else:
                    expansion = "retrieve"
            x = f"{expansion} {cmd[1:]}{args}"
            return x

        content = handle_vertbar(content, cmd, args)

        if cmd == "def_fic":
            return content

        (cmd, args) = command_split(content)

        content = content.replace("\\n", "\n")
        cmd_inner = None
        if cmd in ["var", "insert"]:
            split = args.split("=", maxsplit=1)
            if len(split) > 1:
                (cmd_inner, args_inner) = command_split(split[1])
                inner_content = handle_vertbar(split[1], cmd_inner, args_inner)
                (cmd_inner, args_inner) = command_split(inner_content)
                content = f"{cmd} {split[0]}={inner_content}"

        if cmd == "fic" or cmd_inner == "fic":
            content = content.replace("\\,", "<COMMA>")
            content = content.replace(",", "<_COMMA>")
        try:
            content = content.format(**self.vars.get_vars())
        except KeyError as k:
            return CommandFailure(f"No such variable: {k}")
        if cmd == "fic" or cmd_inner == "fic":
            content = content.replace(",", "<COMMA>")
            content = content.replace("<_COMMA>", ",")

        return content

    def load_scripts(self, directory_name):
        for file in glob.glob(os.path.join(directory_name, "*.fic")):
            var_name = ntpath.basename(file)
            script = FictionScript.from_file(file, var_name)
            if var_name.endswith(".fic"):
                var_name = var_name[:-4].replace("_", " ").lower()
            self.vars[var_name] = script

    @slow_command
    async def cmd__preprocess(self, message: UserMessage, args: str) -> str:
        """Internal metacommand for debugging.
        Usage:
        `preprocess {text}` runs pre-processing to fill in variables and escape certain characters
        """
        return await self.intercept_content(args, "")

    async def cmd__dump_vars(self, message: UserMessage, args: str) -> str:
        """Internal metacommand for debugging.
        Dump out all variables in the current scope, not including shadowed variables from outer scopes.
        Usage:
        `_dump_vars`
        """
        vars = self.vars.get_vars()
        dump = [f"{{{key}}} ~> {vars[key]}" for key in vars]
        return "\n".join(dump)

    async def cmd_inspect_fic(self, message: UserMessage, args: str) -> str:
        if args not in self.vars:
            return CommandFailure("No such script.")
        script = self.vars[args]
        if type(script) is not FictionScript:
            return CommandFailure(f'"{args}" is not a script.')
        content = f"\n>".join(
            f" {i+1: >3}  {line.strip()}" for i, line in enumerate(script.lines)
        )
        return f"**__{args}__**```\n>{content}\n```"

    async def cmd_where(self, message: UserMessage, args: str) -> str:
        """Internal metacommand for debugging.
        Returns the name of the current scope.
        Usage:
        `_scope`"""
        return self.vars

    async def cmd_scope(self, message: UserMessage, args: str) -> Scope:
        if args != "":
            self.vars[args] = Scope(parent=self.vars, name=args)
            return
        return Scope(parent=self.vars)

    async def cmd__dump_var(self, message: UserMessage, args: str) -> str:
        """Internal metacommand for debugging.
        Returns the value of a variable, as a string.
        Usage:
        `_dump_var {name of variable}`"""
        var = self.vars[args]
        return repr(var)

    async def cmd__enter_scope(self, message: UserMessage, args: str) -> None:
        """Internal metacommand.
        Enters a new scope, which is a child of the current scope.
        If no name is provided, the scope will be called "anon".
        Usage:
        `_enter_scope`
        `_enter_scope {name of scope}`"""
        name = None if args == "" else args
        vars = Scope(parent=self.vars, name=name)
        self.vars = vars

    async def cmd__exit_scope(
        self, message: UserMessage, args: str
    ) -> None | CommandFailure:
        """Internal metacommand.
        Exits the current scope, returning to the parent scope.
        Usage:
        `_exit_scope`"""
        if self.vars.parent is None:
            return CommandFailure("Cannot exit scope, as there is no parent scope.")
        self._return_to_scope(self.vars.parent)

    async def cmd_outer(self, message: UserMessage, args: str):
        """Returns the value of a variable from the parent scope."""
        if args == "":
            if self.vars.parent is None:
                return CommandFailure(
                    "There is no outer scope -- this is the base scope."
                )
            return self.vars.parent
        return self.vars.parent[args]

    async def cmd_inspect(self, message: UserMessage, args: str):
        result = self._evaluate(message, args, "inspection")
        if hasattr(result, "inspect"):
            return result.inspect()
        if type(result) is str:
            return f'str("{result}")'
        return CommandFailure(f"Cannot inspect {result}")

    async def cmd_if(self, message: UserMessage, args: str):
        """if {condition} then {y} (optional:) else {z}"""
        cond_then_split = [x.strip() for x in args.split(" then ", maxsplit=1)]
        if len(cond_then_split) < 2:
            return CommandFailure("An `if` needs a `then`!")
        cond = cond_then_split[0]
        then_else_split = [
            x.strip() for x in cond_then_split[1].split(" else ", maxsplit=1)
        ]
        then = then_else_split[0]
        if len(then_else_split) < 2:
            _else = None
        else:
            _else = then_else_split[1]

        cond_result = await self._evaluate(message, cond, "if condition")

        if type(cond_result) is CommandFailure:
            return CommandFailure(f"Failed while evaluating condition:\n{cond_result}")

        if type(cond_result) is not bool:
            return CommandFailure(
                f"If condition should be a bool, but was {cond_result}."
            )

        if cond_result:
            return await self._evaluate(message, then, '"then" clause of if statement')
        elif _else is not None:
            return await self._evaluate(message, _else, '"else" clause of if statement')

    async def cmd_fail(self, message: UserMessage, args: str):
        if args == "":
            args = "No explanation."
        return CommandFailure(args)

    async def cmd_silently(self, message: UserMessage, args: str):
        """Attempt to evaluate a command. Returns nothing, even if the command fails."""
        await self._evaluate(message, args, "silenced evaluation")

    async def cmd_retrieve(self, message: UserMessage, args: str):
        """Retrieve a value from within a scope, or from scopes within scopes.
        You can just write | as a stand-in for this command."""
        index = None
        index_split = [x.strip() for x in args.split("@", maxsplit=1)]
        if len(index_split) == 2:
            try:
                index = int(index_split[0])
                args = index_split[1]
            except ValueError:
                pass  # Not an index.

        inspect = args.endswith("?")
        if inspect:
            args = args[:-1].rstrip()

        split = [x.strip() for x in args.split(">") if x != ""]

        result = self.vars
        for name in split:
            if name in result:
                result = result[name]
            else:
                return CommandFailure(f'"{name}" not found.')

        if index is not None:
            try:
                if inspect:
                    if hasattr(result[index], "inspect"):
                        return result.inspect()
                    if type(result[index]) is str:
                        return f'str("{result[index]}")'
                    return CommandFailure(f"Cannot inspect {result}")
                return result[index]
            except TypeError as err:
                return CommandFailure(f'Cannot index into "{result}":\n{err}')
            except IndexError as err:
                return CommandFailure(f"Failed to access index {index}:\n{err}")

        if inspect:
            if hasattr(result, "inspect"):
                return result.inspect()
            if type(result) is str:
                return f'str("{result}")'
        return result

    async def cmd_insert(self, message: UserMessage, args: str):
        """Assign a value from within a scope, or from scopes within scopes.
        You can just write | as a stand-in for this command."""
        echo = False
        if ":=" in args:
            split = [x.strip() for x in args.split(":=", maxsplit=1)]
            echo = True
        else:
            split = [x.strip() for x in args.split("=", maxsplit=1)]

        retrieval = split[0]
        if len(split) < 2:
            return CommandFailure("No expression to insert.")
        insertion = split[1]
        retrieval_split = [x.strip() for x in retrieval.split(">")]
        if len(retrieval_split) == 1:
            if retrieval_split[0] == "":
                return CommandFailure("No insert destination.")

        scope = self.vars
        for name in retrieval_split[:-1]:
            if name in scope:
                scope = scope[name]
            else:
                return CommandFailure(f'"{name}" not found.')

        original_scope = self.vars
        self.vars = scope
        try:
            if echo:
                result = await self.cmd_var(
                    message, f"{retrieval_split[-1]} := {insertion}"
                )
            else:
                result = await self.cmd_var(
                    message, f"{retrieval_split[-1]} = {insertion}"
                )
            return result
        finally:
            self._return_to_scope(original_scope)

    def _return_to_scope(self, scope: Scope) -> None:
        self.vars = scope
        gc.collect()

    async def cmd_str(self, message: UserMessage, args: str):
        """Stores a string in a variable.
        Shorthand for `var {name} = echo {string}`
        Usage:
        `str {name of string} = {string to be stored}`"""
        await self.cmd_var(message, args.replace("=", "= echo ", 1))

    async def cmd_fails(self, message: UserMessage, args: str):
        result = await self._evaluate(message, args, "failure check")
        return type(result) is CommandFailure

    @slow_command
    async def cmd_arg(self, message: UserMessage, args: str) -> None | CommandFailure:
        """Returns a failure if the variable has not been defined.
        Alternatively, you can provide a default value.
        Arguments with no default values cannot follow an argument with a default value.
        Does nothing otherwise.
        If used within a ficscript document, this defines a required input for the script.
        Usage:
        `arg {name of argument}`
        `arg {name of argument} = {default value}`"""
        defaulting = "=" in args
        if defaulting:
            self.vars._has_defaulting_args = True
        if not defaulting and self.vars._has_defaulting_args:
            return CommandFailure(
                "Arguments without defaults must precede arguments with defaults."
            )
        echo = ":=" in args
        if echo:
            arg_name = args.split(":=", maxsplit=1)[0].strip()
        else:
            arg_name = args.split("=", maxsplit=1)[0].strip()
        if arg_name not in self.vars:
            if not defaulting:
                return CommandFailure(f"Missing argument: {arg_name}")
            return await self.cmd_var(message, args)

    async def cmd_args(self, message: UserMessage, args: str) -> None | CommandFailure:
        """Returns a failure if any of the arguments have not been defined.
        Does nothing otherwise.
        This is typically used at the start of a script file, to ensure that every script input is defined.
        Names of arguments cannot contain commas, since commas are the separator.
        Usage:
        `args {name of argument}, {name of another argument}, {and another}, {and so on any number of times...} ...`
        """
        if self.vars._has_defaulting_args:
            return CommandFailure(
                "Arguments without defaults must precede arguments with defaults."
            )
        args_split = [arg.strip() for arg in args.split(",")]
        for arg in args_split:
            if arg not in self.vars:
                return CommandFailure(f"Missing argument: {args}")

    @slow_command
    async def cmd_load_fic(self, message: UserMessage, args: str) -> str:
        """Load a fictionscript from a file. Files typically use the .fic extension. When this is the case, the
        name of the variable referring to the script will be the filename before the .fic extension, with
        underscores replaced by spaces, in all lower case.
        Usage:
        `load_fic fic/compose_poem.fic` by default, this will load the script as "compose poem"
        `load_fic fic/query.fic as {custom name}`"""
        args = args.replace("$FIC", "./fictionsuit/fic")
        args = args.replace("$.FIC", "./fictionsuit/.fic")

        split = [x.strip() for x in args.split(" as ", maxsplit=1)]
        if len(split) == 1:
            var_name = ntpath.basename(args)
            if var_name.endswith(".fic"):
                var_name = var_name[:-4].replace("_", " ").lower()
        else:
            var_name = split[1]

        script = FictionScript.from_file(split[0], var_name)

        self.vars[var_name] = script

        return var_name

    @slow_command
    async def cmd_def_fic(self, message: UserMessage, args: str) -> str:
        """Define a fictionscript. You should probably look at some examples in the `fic/` folder, and
        familiarize yourself with the documentation of the commands from the `Scripting` command group.
        Usage:
        `def_fic {name}\\n{script}`"""
        split = [x.strip() for x in args.split("\n")]
        var_name = split[0]
        if len(split) < 2:
            return CommandFailure("Script definition is empty.")
        self.vars[var_name] = FictionScript(split[1:], var_name)

    async def _fic(
        self, message: UserMessage, args: str
    ) -> str | CommandHandled | CommandFailure:
        """See docs for cmd_fic"""
        split = args.split(":", maxsplit=1)
        script_name = split[0].strip()
        if len(split) > 1:
            arg_values = [
                x.strip().replace("<COMMA>", ",") for x in split[1].split(",")
            ]
        else:
            arg_values = []

        if script_name in self.vars:
            script = self.vars[script_name]
        elif os.path.exists(script_name):
            script_name = await self.cmd_load_fic(message, script_name)
            script = self.vars[script_name]
        else:
            if ":" not in args:
                return CommandFailure(
                    "No such script.\nMaybe you forgot to put a colon (:) after the script name?"
                )
            return CommandFailure("No such script.")

        if type(script) is not FictionScript:
            return CommandFailure(f"{script_name} is not a script.")

        params = script.args

        previous_dis_int_value = message.disable_interactions
        message.disable_interactions = True

        initial_scope = self.vars
        enter_scope = ScriptLineMessage(
            f"_enter_scope {script_name}", script_name, message
        )

        async def enqueue(script_message):
            return await self.system.enqueue_message(
                script_message, return_failures=True, return_returns=True
            )

        result = await enqueue(enter_scope)
        if result is not None:
            message.disable_interactions = previous_dis_int_value
            self._return_to_scope(initial_scope)
            return CommandFailure(f"Failed to enter scope:\n{result}")

        if len(arg_values) > len(params):
            message.disable_interactions = previous_dis_int_value
            self._return_to_scope(initial_scope)
            return CommandFailure(
                f"Too many arguments! Remember, an argument that contains a comma has to be passed as a variable.\nFor example:\n```str this is fine = this is not fine, because it has a comma\nfic name of script: {{this is fine}}```\n\nExtra arguments:\n{arg_values[len(params):]}"
            )

        for i in range(len(arg_values)):
            result = await enqueue(
                ScriptLineMessage(
                    f"var {params[i]} := {arg_values[i]}", script_name, message
                )
            )
            if result is not None:
                message.disable_interactions = previous_dis_int_value
                self._return_to_scope(initial_scope)
                return CommandFailure(f"Failed to set argument:\n{result}")
        for index, line in enumerate(script.lines):
            if line.strip() != "":
                result = await enqueue(
                    ScriptLineMessage(f"{line}", script_name, message)
                )
                if type(result) is CommandFailure:
                    message.disable_interactions = previous_dis_int_value
                    self._return_to_scope(initial_scope)
                    return CommandFailure(
                        f"Script `{script_name}` failed at line {index + 1}:\n{result}"
                    )
                if result is not None:
                    message.disable_interactions = previous_dis_int_value
                    self._return_to_scope(initial_scope)
                    return result

        exit_scope = ScriptLineMessage(f"_exit_scope", script_name, message)
        result = await enqueue(exit_scope)
        if result is not None:
            message.disable_interactions = previous_dis_int_value
            self._return_to_scope(initial_scope)
            return CommandFailure(f"Failed to exit:\n{result}")

        message.disable_interactions = previous_dis_int_value
        return CommandHandled()

    @slow_command
    async def cmd_fic(
        self, message: UserMessage, args: str
    ) -> str | CommandHandled | CommandFailure:
        """Run a fictionscript. Scripts must first be loaded from a file with `load_fic` or defined with `def_fic`.
        If the script has only one returned variable, this command will return its value.
        Usage:
        `fic {name of script}`"""
        scope_before = self.vars
        disabled_before = message.disable_interactions
        try:
            return await self._fic(message, args)
        finally:
            self._return_to_scope(scope_before)
            message.disable_interactions = disabled_before

    async def cmd_pack(self, message: UserMessage, args: str):
        """Pack several variables into a scope, and return it."""
        vars = [x.strip() for x in args.split(",")]
        scope = Scope(parent=self.vars, name="pack")

        for var in vars:
            if var in self.vars:
                scope[var] = self.vars[var]
                if type(scope[var]) is Scope:
                    scope[var].parent = scope
            else:
                return CommandFailure(f'No variable "{var}" in scope.')
        return scope

    async def cmd_return(self, message: UserMessage, args: str):
        """Evaluate and return an expression."""
        return await self._evaluate(message, args, "return")

    async def _evaluate(self, message: UserMessage, expression: str, context: str):
        previous_dis_int_value = message.disable_interactions
        message.disable_interactions = True
        scope = self.vars
        expression_message = ExpressionMessage(expression, context, message)
        result = await self.system.enqueue_message(
            expression_message, return_whatever=True
        )
        message.disable_interactions = previous_dis_int_value
        self._return_to_scope(scope)
        return result

    @slow_command
    async def cmd_var(self, message: UserMessage, args: str):
        """Attempts to store the result of another command as a variable.
        Usage:
        `var {name of variable} = {command and its arguments}`"""
        # TODO: don't intercept args, intercept the inner command portion only
        # for group in self.command_groups:
        #     args = await group.intercept_content(args)
        #     if type(args) is CommandFailure:
        #         return CommandFailure(f'Command interceptor failed: {args}')

        echo = ":=" in args
        if echo:
            arg_split = [x.strip() for x in args.split(":=", maxsplit=1)]
        else:
            arg_split = [x.strip() for x in args.split("=", maxsplit=1)]

        arg_split = [x for x in arg_split if x != ""]

        if len(arg_split) != 2:
            return CommandFailure("Failed to store variable: Invalid syntax.")

        var_name = arg_split[0]

        if echo:
            self.vars[var_name] = arg_split[1]
            return

        result = await self._evaluate(message, arg_split[1], "var")

        if type(result) is CommandFailure:
            return CommandFailure(f'Expression after "=" failed:\n{result}')

        if result is None:
            return CommandFailure(f'Expression after "=" returned no value.')

        self.vars[var_name] = result

        if type(result) is Scope:
            result.recontextualize(var_name, self.vars)

        if type(result) is ChatInstance:
            result.name = var_name
