from argparse import ArgumentParser
import os

from fictionsuit.commands import Chat, Debug, Research
from fictionsuit.core import BasicCommandSystem, TextIOClient


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
    parser.add_argument(
        "-r",
        "--reactions",
        help="show a message when the system attempts to react to a user message.",
    )
    args = parser.parse_args()

    prefix = ""

    if args.prefix is not None:
        prefix = args.prefix

    command_groups = [Debug(), Research(), Chat()]

    system = BasicCommandSystem(
        command_groups,
        respond_on_unrecognized=False,
        stats_ui=False,
        enable_scripting=True,
        prefix=prefix,
    )

    client = TextIOClient(system, cli=not args.quiet, reactions=args.reactions)

    client.run()


if __name__ == "__main__":
    main()
