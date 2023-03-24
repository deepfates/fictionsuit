from fictionsuit.core.basic_command_system import BasicCommandSystem
from fictionsuit.core.cli import TextIOClient
from fictionsuit.commands.debug import Debug
from fictionsuit.commands.research import Research
from fictionsuit.commands.chat import Chat
from fictionsuit.commands.meta import Meta
from fictionsuit import config

from argparse import ArgumentParser


def main():
    parser = ArgumentParser(prog="FictionSuit", description="LLM Orchestrator")
    parser.add_argument(
        "-q",
        "--quiet",
        action="store_true",
        help='disables CLI prompt ("> "), welcome message, and exit message. ideal for piping files through cli.py.',
    )
    parser.add_argument(
        "-p",
        "--prefix",
        help="defines the command prefix, which is the empty string by default.",
    )
    args = parser.parse_args()

    command_groups = [Debug(), Research(), Chat()]

    config.COMMAND_PREFIX = ""

    if args.prefix is not None:
        config.COMMAND_PREFIX = args.prefix

    system = BasicCommandSystem(
        command_groups, respond_on_unrecognized=False, stats_ui=False
    )

    system.add_meta_group()

    client = TextIOClient(system, cli=not args.quiet)

    client.run()


if __name__ == "__main__":
    main()
