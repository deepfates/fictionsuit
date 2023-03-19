import prompts
import traceback

class CommandGroup():
    """ Extend this class to create a group of command handlers for the bot.
    A handler consists of: a function whose name starts with "cmd_" that accepts the arguments (self, message, args) 
    The rest of the function name is the command name.
    "message" is the discord message that contains the command
    "args" is everything in the message after the command prefix and command name
    
    Look at CommandGroup.cmd_help for an example of a command handler.
    Do not implement a cmd_help command on subclasses unless you enjoy breaking things.
    """

    async def handle(self, message, command, args):
        """Attempt to handle the command.
        Returns True if this command group has a handler for the command*,
        False if the command group has no such handler.
        
        * - If the command is "help", then the handler will be invoked but might return False anyway.
        This is because every CommandGroup has a cmd_help implementation.
        """
        try:
            cmd_handler = f'cmd_{command}'
            if not hasattr(self, cmd_handler):
                # No handler
                return False

            handler = getattr(self, cmd_handler)
            handler_result = await handler(message, args)
            return handler_result if command == 'help' else True
        except Exception as e:
            print(f'\nError in {command} handler: {e}\n{traceback.format_exc()}\n')
            return True
    
    async def cmd_help(self, message, args):
        """**__Help__**
        `prefix help {cmd}` - print the help for command `cmd`
        """

        if args == '':
            args = 'help'
        
        command = args.split(maxsplit=1)[0]

        response = None

        command_handler_name = f'cmd_{command}'

        if hasattr(self, command_handler_name):
            handler = getattr(self, command_handler_name)
            if handler.__doc__ is not None:
                response = handler.__doc__

        if response is None:
            return False # This command group has no documentation for this command, but another group might.

        await message.channel.send(response)
        return True

    def get_all_commands(self):
        return [x[4:] for x in self.__class__.__dict__ if x.startswith('cmd_')]

def command_split(content):
    """given a string that starts with the command prefix,
    returns the command and its arguments as a tuple.

    If there is no command, the command will be None
    If there are no arguments, the arguments will be an empty string.
    """

    # "cmd_prefix cmd args..."
    #            ^
    #            | this space might not exist
    if prompts.COMMAND_PREFIX.endswith(' '):
        # If it does exist, we need to split at the first 2 spaces
        split_content = content.split(maxsplit=2)
        # prefix = content_split[0] (we can throw this away)
        if len(split_content) < 2:
            return (None, '') # just the prefix, with no command
        cmd = split_content[1]
        if len(split_content) > 2:
            args = split_content[2]
        else:
            args = ''
    else:
        # If it doesn't exist, we only need to split on one space
        # but, the first section will contain the prefix
        split_content = content.split(maxsplit=1)
        cmd = split_content[0]
        cmd = cmd[len(prompts.COMMAND_PREFIX):] # strip off prefix
        if cmd == '':
            return (None, '') # just the prefix, with no command
        if len(split_content) > 1:
            args = split_content[1]
        else:
            args = ''

    return (cmd, args)

