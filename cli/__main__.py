import sys
from argparse import REMAINDER, SUPPRESS, ArgumentParser
from logging import Formatter, StreamHandler, getLogger

from metrico import MetricoCore, __version__
from metrico.cli.cmd import MAIN_CMDS
from metrico.const import DEFAULT_FILENAME

logger = getLogger("metrico")


def main():
    parser = ArgumentParser(prog="metrico", description="Just some metrics stuff", epilog="build by axju")
    parser.add_argument("-V", "--version", action="version", version=__version__)
    parser.add_argument(
        "-v",
        "--verbose",
        action="count",
        help="verbose level... repeat up to three times",
    )
    parser.add_argument("-c", "--config", help="set the config file, default=metrico.toml")
    parser.add_argument(
        "cmd",
        nargs="?",
        choices=list(MAIN_CMDS) + [name[0] for name in MAIN_CMDS],
        help="select one command",
    )
    parser.add_argument("args", help=SUPPRESS, nargs=REMAINDER)
    args = parser.parse_args()

    if args.verbose:
        level = 40 - args.verbose * 10 if args.verbose <= 3 else 30
        logger.setLevel(level)
        handler = StreamHandler()
        handler.setLevel(level)
        formatter = Formatter("%(asctime)s - %(name)20s - %(levelname)6s - %(message)s")
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    # metrico.config.load(filenames=DEFAULT_FILENAMES, log_except=False)
    metrico = MetricoCore(filename=args.config or DEFAULT_FILENAME)

    if args.cmd:
        try:
            func = None
            for name, item in MAIN_CMDS.items():
                if args.cmd in [name, name[0]]:
                    func = item
                    break
            if func is None:
                sys.exit(1)
            sys.exit(func(metrico, *args.args))
        except Exception as exc:
            if args.verbose:
                raise
            logger.error('Oh no, a error :(\nError: "%s"', exc)
            logger.error("Run with --verbose for more information.")
            sys.exit(1)

    parser.print_help()
    sys.exit(0)


if __name__ == "__main__":
    main()
