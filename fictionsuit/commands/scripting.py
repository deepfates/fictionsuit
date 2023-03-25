from __future__ import annotations

import ntpath
import os

from .. import config
from ..api_wrap import UserMessage
from ..core import OpenAIChat
from ..core.fictionscript import FictionScript, ScriptMessage, VarScope
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
        self.vars = VarScope()  # TODO: load in var state from a file, optionally?
        # TODO: add a more general preprocessor outside of Scripting for parsing scripts
        # from a nicer syntax down into runnable commands

    async def intercept_content(self, content: str) -> str:
        if not content.startswith(config.COMMAND_PREFIX):
            return content
        (cmd, _) = command_split(content, config.COMMAND_PREFIX)
        if cmd == "def_script":
            return content
        content = content.replace("\\n", "\n")
        if cmd == "script":
            content = content.replace(",", "<_COMMA>")
        content = content.format(**self.vars.get_vars())
        if cmd == "script":
            content = content.replace(",", "<COMMA>")
            content = content.replace("<_COMMA>", ",")
        return content

    @slow_command
    @auto_reply
    async def cmd__preprocess(self, message: UserMessage, args: str) -> str:
        """Internal metacommand for debugging.
        Kinda hard to explain its purpose. Complain to John if you find this documentation lacking.
        """
        return await self.intercept_content(args)

    @auto_reply
    async def cmd__dump_vars(self, message: UserMessage, args: str) -> str:
        """Internal metacommand for debugging.
        Dump out all variables in the current scope, not including shadowed variables from outer scopes.
        """
        vars = str(self.vars.get_vars())
        return vars

    @auto_reply
    async def cmd__scope(self, message: UserMessage, args: str) -> str:
        """Internal metacommand for debugging.
        Returns the name of the current scope."""
        return self.vars.name

    @auto_reply
    async def cmd__dump_var(self, message: UserMessage, args: str) -> str:
        """Internal metacommand for debugging.
        Dumps the value of a variable."""
        var = self.vars[args]
        return str(var)

    async def cmd__enter_scope(self, message: UserMessage, args: str) -> None:
        """Internal metacommand.
        Enters a new scope, which is a child of the current scope."""
        name = None if args == "" else args
        vars = VarScope(parent=self.vars, name=name)
        self.vars = vars

    async def cmd__exit_scope(
        self, message: UserMessage, args: str
    ) -> None | CommandFailure:
        """Internal metacommand.
        Exits the current scope, returning to the parent scope."""
        if self.vars.parent is None:
            return CommandFailure("Cannot exit scope, as there is no parent scope.")
        self.vars = self.vars.parent

    def _return_to_scope(self, scope: VarScope) -> None:
        self.vars = scope

    # TODO: "args x, y, z" syntax, equivalent to "arg x\narg y\narg z"
    async def cmd_arg(self, message: UserMessage, args: str) -> None | CommandFailure:
        """Returns a failure if the argument has not been defined."""
        if args not in self.vars:
            return CommandFailure(f"Missing argument: {args}")

    @slow_command
    async def cmd_load_script(self, message: UserMessage, args: str) -> str:
        """Load a script from a file. Files use the .fic extension, but that convention might change. Idk."""
        split = [x.strip() for x in args.split("as", maxsplit=1)]
        if len(split) == 1:
            var_name = ntpath.basename(args)
        else:
            var_name = split[1]

        script = FictionScript.from_file(split[0])

        self.vars[var_name] = script

        return var_name

    @slow_command
    async def cmd_def_script(self, message: UserMessage, args: str) -> str:
        """Define a script. This is just a sequence of commands that will be run in their own scope.
        `return` can be used to elevate variables out to the parent scope.
        `arg {arg}` can be used to ensure that a variable the script relies on has been defined.
        """
        split = [x.strip() for x in args.split("\n")]
        var_name = split[0]
        if len(split) < 2:
            return CommandFailure("Script definition is empty.")
        self.vars[var_name] = FictionScript(split[1:])

    @slow_command
    @auto_reply
    async def cmd_script(
        self, message: UserMessage, args: str
    ) -> str | CommandHandled | CommandFailure:
        """Run a script. Scripts must first be loaded from a file with `load_script` or defined with `def_script`.
        If the script has only one returned variable, this command will return its value.
        """
        split = args.split(":", maxsplit=1)
        script_name = split[0].strip()
        if len(split) > 1:
            arg_values = [
                x.strip().replace("<COMMA>", ",") for x in split[1].split(",")
            ]
        else:
            arg_values = []

        pfx = config.COMMAND_PREFIX
        if pfx != "" and pfx[-1] != " ":
            pfx = f"{config.COMMAND_PREFIX} "

        if script_name in self.vars:
            script = self.vars[script_name]
        elif os.path.exists(script_name):
            script_name = await self.cmd_load_script(message, script_name)
            script = self.vars[script_name]
        else:
            return CommandFailure("No such script.")

        if type(script) is not FictionScript:
            return CommandFailure(f"{script_name} is not a script.")

        params = [
            x.split(maxsplit=1)[1].strip() for x in script.lines if x.startswith("arg")
        ]

        previous_dis_int_value = message.disable_interactions
        message.disable_interactions = True

        initial_scope = self.vars
        enter_scope = ScriptMessage(
            f"{pfx}_enter_scope {script_name}", script_name, message
        )

        async def enqueue(script_message):
            return await self.system.enqueue_message(
                script_message, return_failures=True
            )

        result = await enqueue(enter_scope)
        if result is not None:
            message.disable_interactions = previous_dis_int_value
            self._return_to_scope(initial_scope)
            return result  # Failure
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

    # TODO: "return x as y" syntax?
    async def cmd_return(
        self, message: UserMessage, args: str
    ) -> str | None | CommandFailure:
        """Copy a variable from the current scope to the parent scope."""
        if self.vars.parent is None:
            return CommandFailure("Cannot return values out of the base scope.")
        vars = [x.strip() for x in args.split(",")]
        for var in vars:
            self.vars.move_up(var)
        if len(vars) == 1:
            return self.vars[vars[0]]

    @slow_command
    async def cmd_var(self, message: UserMessage, args: str):
        """Attempts to store the result of another command as a variable."""

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
