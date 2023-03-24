from __future__ import annotations

from .. import config

from ..core.system import System
from .command_group import (
    CommandGroup,
    CommandFailure,
    CommandHandled,
    CommandNotFound,
    command_split,
)
from ..api_wrap.user_message import UserMessage

from ..core.core import openai_chat


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
        return self.vars[k]


class ScriptMessage(UserMessage):
    def __init__(self, content: str, filename: str, invoker: UserMessage):
        super().__init__(content, f"script: {filename}")
        self.invoker = invoker

    async def _send(self, message_content: str) -> bool:
        return await self.invoker._send(message_content)

    async def _reply(self, reply_content: str) -> bool:
        return await self.invoker._reply(reply_content)

    async def _react(self, reaction: str | None) -> bool:
        return await self.invoker._react(reaction)

    async def _undo_react(self, reaction: str | None) -> bool:
        return await self.invoker._undo_react(reaction)

    async def _get_timestamp(self) -> float:
        return await self.invoker._get_timestamp()

    async def _retrieve_history(self) -> openai_chat:
        return await self.invoker._retrieve_history()


class Meta(CommandGroup):
    def __init__(self, system: System, command_groups: list[CommandGroup]):
        self.command_groups = command_groups
        self.system = system
        self.vars = VarScope()  # TODO: load in var state from a file, optionally?
        # TODO: add a more general preprocessor outside of Meta for parsing scripts
        # from a nicer syntax down into runnable commands

    async def intercept_content(self, content: str) -> str:
        content = content.replace("\\n", "\n")
        (cmd, args) = command_split(content, config.COMMAND_PREFIX)
        if cmd == "script":
            content = content.replace(",", "<_COMMA>")
        content = content.format(**self.vars.get_vars())
        if cmd == "script":
            content = content.replace(",", "<COMMA>")
            content = content.replace("<_COMMA>", ",")
        return content

    async def cmd_dump_vars(self, message: UserMessage, args: str) -> str:
        vars = str(self.vars.get_vars())
        await message.reply(vars)
        return vars

    async def cmd_scope(self, message: UserMessage, args: str) -> str:
        await message.reply(self.vars.name)
        return self.vars.name

    async def cmd_dump_var(self, message: UserMessage, args: str) -> str:
        var = self.vars[args]
        await message.reply(str(var))
        return str(var)

    async def cmd_enter_scope(self, message: UserMessage, args: str) -> None:
        name = None if args == "" else args
        vars = VarScope(parent=self.vars, name=name)
        self.vars = vars

    async def cmd_exit_scope(
        self, message: UserMessage, args: str
    ) -> None | CommandFailure:
        if self.vars.parent is None:
            return CommandFailure("Cannot exit scope, as there is no parent scope.")
        self.vars = self.vars.parent

    async def cmd_arg(self, message: UserMessage, args: str) -> None | CommandFailure:
        if args not in self.vars:
            return CommandFailure(f"Missing argument: {args}")

    async def cmd_script(self, message: UserMessage, args: str):
        split = args.split(":", maxsplit=1)
        filename = split[0].strip()
        arg_values = [x.strip().replace("<COMMA>", ",") for x in split[1].split(",")]

        with open(filename, "r") as file:
            lines = file.readlines()
        params = [x.split(maxsplit=1)[1].strip() for x in lines if x.startswith("arg")]

        enter_scope = ScriptMessage(f"enter_scope {filename}", filename, message)

        async def enqueue(script_message):
            return await self.system.enqueue_message(
                script_message, return_failures=True
            )

        result = await enqueue(enter_scope)
        if result is not None:
            return result
        for i in range(len(arg_values)):
            result = await enqueue(
                ScriptMessage(
                    f"var {params[i]} = echo {arg_values[i]}", filename, message
                )
            )
            if result is not None:
                return result
        for line in lines:
            if line.strip() != "":
                result = await enqueue(ScriptMessage(line, filename, message))
                if result is not None:
                    return result

        exit_scope = ScriptMessage(f"exit_scope", filename, message)
        result = await enqueue(exit_scope)
        if result is not None:
            return result

        returns = [x for x in lines if x.startswith("return")]

        # If exactly one value is returned by the script, its value is
        # returned by the cmd_script command.
        if len(returns) == 1:
            rcommand = returns[0]
            r_args = rcommand.split(" ", maxsplit=1)[1]
            r_args_split = r_args.split(",")
            if len(r_args_split) == 1:
                result = self.vars[r_args_split[0].strip()]
                await message.reply(result)
                return result

        await message.reply(f"Script ran successfully. Return statments: {returns}")

    async def cmd_return(self, message: UserMessage, args: str):
        vars = [x.strip() for x in args.split(",")]
        for var in vars:
            self.vars.move_up(var)
        if len(vars) == 1:
            return self.vars[vars[0]]

    async def cmd_var(
        self, message: UserMessage, args: str
    ) -> CommandFailure | CommandHandled:
        """Attempts to store the result of another command as a variable. Returns True on success or False on failure.
        TODO: there's probably a better way to arrange the return type here."""

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
            result = await group.handle(message, cmd, args)
            if type(result) is not CommandNotFound:
                if type(result) is CommandFailure:
                    return CommandFailure(
                        f'Failed to store variable: Command "{cmd}" failed.\n{result.message}'
                    )
                if type(result) is CommandHandled:
                    return CommandFailure(
                        f'Failed to store variable: Command "{cmd}" returns no value.'
                    )
                self.vars[var_name] = result
                return CommandHandled()

        message.disable_interactions = previous_dis_int_value

        if cmd == "help":
            self.vars[var_name] = f'Sorry, there\'s no command called "{args}"'
            return CommandHandled()

        return CommandFailure(f'Failed to store variable: No command called "{cmd}"')
