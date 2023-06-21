from argparse import ArgumentParser

from fictionsuit.commands import Methods, Debug, Research, Text, WebUi
from fictionsuit.commands.mpt import MPT
from fictionsuit.core import BasicCommandSystem, ApiClient
from fictionsuit.core.api_client import ApiClient


def main():
    parser = ArgumentParser(prog="FictionSuit API", description="LLM API")

    args = parser.parse_args()

    command_groups = [Debug(), Research(), Methods(), Text(), WebUi(), MPT()]

    system = BasicCommandSystem(
        command_groups,
        respond_on_unrecognized=False,
        stats_ui=False,
        enable_scripting=True,
    )

    client = ApiClient(system)

    client.run()


if __name__ == "__main__":
    main()
