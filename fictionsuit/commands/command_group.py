import config
class CommandGroup():
    async def handle(self, message):
        if not message.content.startswith(config.COMMAND_PREFIX):
            return
        cmd_split = message.content.split(' ', 1)
        cmd = cmd_split[1]

        if len(cmd_split) < 2:
            args = ''
        else:
            args = cmd_split[1]

        try:
            cmd_handler = f'cmd_{cmd}'
            if not hasattr(self, cmd_handler):
                # No handler
                print(f'No handler for command: {cmd}')
                return False

            handler = getattr(self, cmd_handler)
            await handler(message, args)
            return True
        except Exception as e:
            print(f'TODO: handle this error: {e}')
            return True

