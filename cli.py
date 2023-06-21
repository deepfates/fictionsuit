from argparse import ArgumentParser

from fictionsuit.commands import Methods, Debug, Research, Text
from fictionsuit.commands.mpt import MPT
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
        "-r",
        "--reactions",
        help="show a message when the system attempts to react to a user message.",
    )
    args = parser.parse_args()

    command_groups = [Debug(), Research(), Methods(), Text(), MPT()]

    system = BasicCommandSystem(
        command_groups,
        respond_on_unrecognized=False,
        stats_ui=False,
        enable_scripting=True,
    )

    client = TextIOClient(system, cli=not args.quiet, reactions=args.reactions)

    client.run()


if __name__ == "__main__":
    main()
