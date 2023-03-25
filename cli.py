from argparse import ArgumentParser

from fictionsuit import config
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
    args = parser.parse_args()

    command_groups = [Debug(), Research(), Chat()]

    config.COMMAND_PREFIX = ""

    if args.prefix is not None:
        config.COMMAND_PREFIX = args.prefix

    system = BasicCommandSystem(
        command_groups,
        respond_on_unrecognized=False,
        stats_ui=False,
        enable_scripting=True,
    )

    client = TextIOClient(system, cli=not args.quiet)

    client.run()


if __name__ == "__main__":
    main()
