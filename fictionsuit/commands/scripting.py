from __future__ import annotations

import ntpath
import os
import glob

from .. import config
from ..core.user_message import UserMessage
from ..core.fictionscript import FictionScript, ScriptMessage, Scope
from ..core.system import System
from .command_group import (
    CommandFailure,
    CommandGroup,
    CommandHandled,
    CommandNotFound,
    CommandReply,
    auto_reply,
    command_split,
    slow_command,
)


class Scripting(CommandGroup):
    def __init__(self, system: System, command_groups: list[CommandGroup]):
        self.command_groups = command_groups
        self.system = system
        self.prefix = system.prefix if hasattr(system, 'prefix') else ''
        self.vars = Scope()  # TODO: save and load scopes?
        # TODO: Concurrency & scopes might be a mess
        # TODO: add a more general preprocessor outside of Scripting for parsing scripts
        # from a nicer syntax down into runnable commands
        # TODO: maybe add config options for folders instead of just hard-coding things...
        self.load_scripts("fictionsuit/fic")
        self.load_scripts("fictionsuit/.fic")

    async def intercept_content(self, content: str, prefix: str | None = None) -> str:
        if prefix is None:
            prefix = self.prefix
        if not content.startswith(prefix):
            return content
        (cmd, args) = command_split(content, prefix)
        if cmd == "def_fic":
            return content
        content = content.replace("\\n", "\n")
        cmd_inner = None
        if cmd == "var":
            split = args.split('=', maxsplit=1)
            if len(split) > 1:
                (cmd_inner, _) = command_split(split[1], "")
        if cmd == "fic" or cmd_inner == "fic":
            content = content.replace("\\,", "<COMMA>")
            content = content.replace(",", "<_COMMA>")
        content = content.format(**self.vars.get_vars())
        if cmd == "fic" or cmd_inner == "fic":
            content = content.replace(",", "<COMMA>")
            content = content.replace("<_COMMA>", ",")
        return content

    def load_scripts(self, directory_name):
        for file in glob.glob(os.path.join(directory_name, "*.fic")):
            script = FictionScript.from_file(file)
            var_name = ntpath.basename(file)
            if var_name.endswith(".fic"):
                var_name = var_name[:-4].replace("_", " ").lower()
            self.vars[var_name] = script

    @slow_command
    @auto_reply
    async def cmd__preprocess(self, message: UserMessage, args: str) -> str:
        """Internal metacommand for debugging.
        Usage:
        `preprocess {text}` runs pre-processing to fill in variables and escape certain characters
        """
        return await self.intercept_content(args)

    @auto_reply
    async def cmd__dump_vars(self, message: UserMessage, args: str) -> str:
        """Internal metacommand for debugging.
        Dump out all variables in the current scope, not including shadowed variables from outer scopes.
        Usage:
        `_dump_vars`
        """
        vars = str(self.vars.get_vars())
        return vars

    @auto_reply
    async def cmd__scope(self, message: UserMessage, args: str) -> str:
        """Internal metacommand for debugging.
        Returns the name of the current scope.
        Usage:
        `_scope`"""
        return self.vars.name

    @auto_reply
    async def cmd__dump_var(self, message: UserMessage, args: str) -> str:
        """Internal metacommand for debugging.
        Returns the value of a variable, as a string.
        Usage:
        `_dump_var {name of variable}`"""
        var = self.vars[args]
        return str(var)

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
        self.vars = self.vars.parent

    @auto_reply
    async def cmd_outer(self, message: UserMessage, args: str):
        """Returns the value of a variable from the parent scope."""
        return self.vars.parent[args]

    def _return_to_scope(self, scope: Scope) -> None:
        self.vars = scope

    async def cmd_str(self, message: UserMessage, args: str):
        """Stores a string in a variable.
        Shorthand for `var {name} = echo {string}`
        Usage:
        `str {name of string} = {string to be stored}`"""
        await self.cmd_var(message, args.replace("=", "= echo ", 1))

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
        arg_name = args.split('=', maxsplit=1)[0].strip()
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
        args = args.replace('$FIC', './fictionsuit/fic')
        args = args.replace('$.FIC', './fictionsuit/.fic')

        split = [x.strip() for x in args.split(" as ", maxsplit=1)]
        if len(split) == 1:
            var_name = ntpath.basename(args)
            if var_name.endswith(".fic"):
                var_name = var_name[:-4].replace("_", " ").lower()
        else:
            var_name = split[1]

        script = FictionScript.from_file(split[0])

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
        self.vars[var_name] = FictionScript(split[1:])

    async def _fic(self, message: UserMessage, args: str) -> str | CommandHandled | CommandFailure:
        """See docs for cmd_fic"""
        split = args.split(":", maxsplit=1)
        script_name = split[0].strip()
        if len(split) > 1:
            arg_values = [
                x.strip().replace("<COMMA>", ",") for x in split[1].split(",")
            ]
        else:
            arg_values = []

        pfx = self.command_prefix
        if pfx != "" and pfx[-1] != " ":
            pfx = f"{self.command_prefix} "

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
        enter_scope = ScriptMessage(
            f"{pfx}_enter_scope {script_name}", script_name, message
        )

        async def enqueue(script_message):
            script_message.content = await self.intercept_content(script_message.content)
            return await self.system.enqueue_message(
                script_message, return_failures=True
            )

        result = await enqueue(enter_scope)
        if result is not None:
            message.disable_interactions = previous_dis_int_value
            self._return_to_scope(initial_scope)
            return result  # Failure

        if len(arg_values) > len(params):
            message.disable_interactions = previous_dis_int_value
            self._return_to_scope(initial_scope)
            return CommandFailure(
                f"Too many arguments! Remember, an argument that contains a comma has to be passed as a variable.\nFor example:\n```str this is fine = this is not fine, because it has a comma\nfic name of script: {{this is fine}}```\n\nExtra arguments:\n{arg_values[len(params):]}"
            )

        for i in range(len(arg_values)):
            result = await enqueue(
                ScriptMessage(
                    f"{pfx}var {params[i]} = echo {arg_values[i]}", script_name, message
                )
            )
            if result is not None:
                message.disable_interactions = previous_dis_int_value
                self._return_to_scope(initial_scope)
                return result  # Failure
        for line in script.lines:
            if line.strip() != "":
                result = await enqueue(
                    ScriptMessage(f"{pfx}{line}", script_name, message)
                )
                if result is not None:
                    message.disable_interactions = previous_dis_int_value
                    self._return_to_scope(initial_scope)
                    return result  # Failure

        exit_scope = ScriptMessage(f"{pfx}_exit_scope", script_name, message)
        result = await enqueue(exit_scope)
        if result is not None:
            message.disable_interactions = previous_dis_int_value
            self._return_to_scope(initial_scope)
            return result  # Failure

        returns = [x for x in script.lines if x.startswith("return")]

        # If exactly one value is returned by the script, its value is
        # returned by the cmd_script command.
        if len(returns) == 1:
            rcommand = returns[0]
            r_args = rcommand.split(" ", maxsplit=1)[1]
            r_args_split = r_args.split(",")
            if len(r_args_split) == 1:
                result = self.vars[r_args_split[0].strip()]
                message.disable_interactions = previous_dis_int_value
                return result  # str

        message.disable_interactions = previous_dis_int_value
        await message.reply(f"Script ran successfully. Return statments: [{returns}]")
        return CommandHandled()

    @slow_command
    @auto_reply
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

        

    # TODO: "return x as y / return x as _" syntax
    async def cmd_return(
        self, message: UserMessage, args: str
    ) -> str | None | CommandFailure:
        """Copy a variable from the current scope into the parent scope.
        Usage:
        `return {name of variable}`"""
        if self.vars.parent is None:
            return CommandFailure("Cannot return values out of the base scope.")
        vars = [x.strip() for x in args.split(",")]
        for var in vars:
            self.vars.move_up(var)
        if len(vars) == 1:
            return self.vars[vars[0]]

    @slow_command
    async def cmd_var(self, message: UserMessage, args: str):
        """Attempts to store the result of another command as a variable.
        Usage:
        `var {name of variable} = {command and its arguments}`"""
        arg_split = [x.strip() for x in args.split("=", maxsplit=1)]
        arg_split = [x for x in arg_split if x != ""]

        if len(arg_split) != 2:
            return CommandFailure("Failed to store variable: Invalid syntax.")

        var_name = arg_split[0]

        (cmd, args) = command_split(arg_split[1], "")

        if cmd is None:
            return CommandFailure(f"Failed to store variable: No command.")

        previous_dis_int_value = message.disable_interactions
        message.disable_interactions = True

        for group in self.command_groups:
            # TODO: get multi_commands properly working here...
            # probably best to unify the implementation between this and the method in basic_command_system
            result = await group.handle(message, cmd, args)
            if type(result) is not CommandNotFound:
                if type(result) is CommandFailure:
                    message.disable_interactions = previous_dis_int_value
                    return CommandFailure(
                        f'Failed to store variable: Command "{cmd}" failed.\n{result}'
                    )
                if type(result) is CommandHandled:
                    message.disable_interactions = previous_dis_int_value
                    return CommandFailure(
                        f'Failed to store variable: Command "{cmd}" returns no value.'
                    )
                if type(result) is CommandReply:
                    result = str(
                        result
                    )  # Unwrap; value is captured by the var instead of being sent out.
                self.vars[var_name] = result
                message.disable_interactions = previous_dis_int_value
                return CommandHandled()

        message.disable_interactions = previous_dis_int_value

        if cmd == "help":
            self.vars[var_name] = f'Sorry, there\'s no command called "{args}"'
            return

        return CommandFailure(f'Failed to store variable: No command called "{cmd}"')
