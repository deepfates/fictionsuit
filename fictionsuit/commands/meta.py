from .command_group import (
    CommandGroup,
    CommandFailure,
    CommandHandled,
    CommandNotFound,
    command_split,
)
from ..api_wrap.user_message import UserMessage


class Meta(CommandGroup):
    def __init__(self, command_groups: list[CommandGroup]):
        self.command_groups = command_groups
        self.vars = {"\\n": "\n"}  # TODO: load in var state from a file, optionally?
        # TODO: add a more general preprocessor outside of Meta for parsing scripts
        # from a nicer syntax down into runnable commands

    async def intercept_content(self, content: str) -> str:
        return content.format(**self.vars)

    async def cmd_dump_vars(self, message: UserMessage, args: str) -> str:
        await message.reply(str(self.vars))
        return str(self.vars)

    async def cmd_dump_var(self, message: UserMessage, args: str) -> str:
        var = self.vars[args]
        await message.reply(str(var))
        return str(var)

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
