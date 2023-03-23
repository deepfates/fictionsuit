from fictionsuit.core.basic_command_system import BasicCommandSystem
from fictionsuit.core.cli import TextIOClient
from fictionsuit.commands.debug import Debug
from fictionsuit.commands.research import Research
from fictionsuit import config

from argparse import ArgumentParser

def main():
    parser = ArgumentParser(prog='FictionSuit', description='LLM Orchestrator')
    parser.add_argument('-nc', '--no_cli', action='store_true',
                        help='disables CLI prompt ("> ") and welcome message; sets command prefix to the empty string unless --prefix is specified.')
    parser.add_argument('-p', '--prefix',
                        help='defines the command prefix, which would otherwise be loaded from the environment.')
    args = parser.parse_args()
    
    command_groups = [
        Debug(),
        Research()
        ]

    if args.no_cli:
        config.COMMAND_PREFIX = ''

    if args.prefix is not None:
        config.COMMAND_PREFIX = args.prefix

    system = BasicCommandSystem(command_groups, respond_on_unrecognized=True, stats_ui=False)

    client = TextIOClient(system, cli=not args.no_cli)

    client.run()

if __name__ == '__main__':
    main()
