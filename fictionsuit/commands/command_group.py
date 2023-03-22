import traceback

from ..api_wrap.user_message import UserMessage

class CommandGroup():
    """ Extend this class to create a group of command handlers for the bot.
    A handler consists of: a function whose name starts with "cmd_" that accepts the arguments (self, message, args) 
    The rest of the function name is the command name.
    "message" is the UserMessage that contains the command
    "args" is everything in the message after the command prefix and command name
    A handler's name should not contain any upper-case characters. Usage will not be case-sensitive.

    Look at CommandGroup.cmd_help for an example of a command handler.
    Do not implement a cmd_help command on subclasses unless you enjoy breaking things.
    """

    async def handle(self, message: UserMessage, command: str, args: str) -> bool:
        """Attempt to handle the command.
        Returns True if this command group has a handler for the command*,
        False if the command group has no such handler.
        
        * - If the command is "help", then the handler will be invoked but might return False anyway.
        This is because every CommandGroup has a cmd_help implementation.
        """
        try:
            cmd_handler = f'cmd_{command}'.lower()
            if not hasattr(self, cmd_handler):
                # No handler
                return False

            handler = getattr(self, cmd_handler)
            handler_result = await handler(message, args)
            return handler_result if command == 'help' else True
        except Exception as e:
            print(f'\nError in {command} handler: {e}\n{traceback.format_exc()}\n')
            return True
    
    async def cmd_help(self, message: UserMessage, args: str) -> bool:
        """**__Help__**
        `prefix help {cmd}` - print the help for command `cmd`
        """

        if args == '':
            args = 'help'
        
        command = args.split(maxsplit=1)[0]

        response = None

        command_handler_name = f'cmd_{command}'.lower()

        if hasattr(self, command_handler_name):
            handler = getattr(self, command_handler_name)
            if handler.__doc__ is not None:
                response = handler.__doc__
            else:
                response = f'Sorry, the "{command}" command is missing documentation.'

        if response is None:
            return False # This command group has no documentation for this command, but another group might.

        await message.reply(response)
        return True

    def get_all_commands(self) -> list[str]:
        return [x[4:] for x in self.__class__.__dict__ if x.startswith('cmd_')]

# TODO: Unit testing
def command_split(content: str, prefix: str) -> tuple[str, str]:
    """given a string that starts with the command prefix,
    returns the command and its arguments as a tuple.

    If there is no command, the command will be None
    If there are no arguments, the arguments will be an empty string.
    
    **It is the caller's responsibility to ensure that the string starts with the prefix.**
    """
    after_prefix = content[len(prefix):].strip()

    if after_prefix == '':
        return (None, '') # No command

    split_content = after_prefix.split(maxsplit=1)

    cmd = split_content[0]

    if len(split_content) == 1: # No args
        args = ''
    else:
        args = split_content[1]

    return (cmd, args)
  
