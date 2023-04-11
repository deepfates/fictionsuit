from argparse import ArgumentParser

from fictionsuit.commands import Methods, Debug, Research, Text
from fictionsuit.core import BasicCommandSystem
from fictionsuit.api_wrap.bluesky import BlueskyClient


def main():
    parser = ArgumentParser(prog="FictionSuit API", description="LLM API")

    args = parser.parse_args()

    command_groups = [Debug(), Research(), Methods(), Text()]

    system = BasicCommandSystem(
        command_groups,
        respond_on_unrecognized=False,
        stats_ui=False,
        enable_scripting=True,
    )

    client = BlueskyClient(system)

    client.run()


if __name__ == "__main__":
    main()
