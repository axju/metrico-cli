import random
import string
import time
from pathlib import Path

from rich import print as rich_print
from rich.table import Table

from metrico import MetricoCore
from metrico import models
from metrico.cli.utils import MetricoArgumentParser, console


def get_random_string(length: int = 32) -> str:
    return "".join(random.choice(string.ascii_lowercase) for _ in range(length))


def config(metrico: MetricoCore, args) -> int:
    match args.key:
        case None:
            rich_print(metrico.config)

        case str() as key:
            rich_print(f"{key} - {getattr(metrico.config, key)}")

        case _:
            print("WTF?")
            return 1
    return 0


def benchmark(metrico: MetricoCore, args) -> int:
    platform = "test"

    metrico.config.db.url = "sqlite://"
    if args.sqlite:
        Path("testing.db").unlink(missing_ok=True)
        metrico.config.db.url = "sqlite:///testing.db"
    metrico.db.reload_config()

    metrico.db.setup()
    metrico.hunter[platform].config["max_medias"] = args.medias
    metrico.hunter[platform].config["max_comments"] = args.comments
    metrico.hunter[platform].config["change_account_stats"] = 1
    metrico.hunter[platform].config["change_media_stats"] = 1

    # metrico.hunter[platform].config["random_medias"] = False
    # metrico.hunter[platform].config["random_comments"] = False
    #
    # metrico.hunter[platform].config["medias_add"] = 1
    # metrico.hunter[platform].config["change_account_name"] = 0
    # metrico.hunter[platform].config["change_account_bio"] = 0
    # metrico.hunter[platform].config["change_account_stats"] = 1
    # metrico.hunter[platform].config["change_account_medias"] = 0
    #
    # metrico.hunter[platform].config["comments_add"] = 5
    # metrico.hunter[platform].config["change_media_title"] = 0
    # metrico.hunter[platform].config["change_media_caption"] = 1
    # metrico.hunter[platform].config["change_media_stats"] = 1
    # metrico.hunter[platform].config["change_media_comments"] = 0

    console.log("Loops:", args.loops, "Accounts:", args.accounts, "Medias:", args.medias, "Comments:", args.comments)
    console.log("Database:", metrico.config.db.url)

    start = time.time()
    account_ids = []
    for data in metrico.hunter[platform].analyze("foo", amount=args.accounts):
        if isinstance(data, models.Account):
            account = metrico.db.create_account(platform, data)
            account_ids.append(account.id)

    for loop in range(args.loops):
        console.log(f"Running loop {loop}")
        for account_id in account_ids:
            metrico.update_account(account_id, media_count=args.media_count, comment_count=args.comment_count, subscription_count=args.subscription_count)

    end = time.time()

    stats = metrico.db.stats()
    results: dict[str, int] = {
        "Account": args.medias * args.comments + args.accounts,
        "Account-Info": args.medias * args.comments + args.accounts,
        "Account-Data": args.medias * args.comments + args.accounts + (args.loops * args.accounts),
        "Media": args.accounts * args.medias,
        "Media-Info": args.accounts * args.medias,
        "Media-Data": args.accounts * args.medias * args.loops,
        "Media-Comment": args.accounts * args.medias * args.comments,
        "Account-Subscription": 0
    }
    error = any((stats[key] != results[key] for key in stats))

    table = Table("", *stats.keys())
    table.add_row("DB", *[str(value) for value in stats.values()])
    table.add_row("Ref", *[str(results.get(key, "")) for key in stats.keys()])

    console.print(table)
    console.print(f"Result: {end - start:.2f} sec")
    console.print(f"Error:  {error}")
    return 0


def make_migrations(metrico: MetricoCore, args) -> int:
    metrico.db.make_migrations(message=args.comment)
    return 0


def migrate(metrico: MetricoCore) -> int:
    metrico.db.migrate()
    return 0


def main(metrico: MetricoCore, *argv: str) -> int:
    parser = MetricoArgumentParser("utils")
    subparsers = parser.add_subparsers(dest="action", help="sub-command help")

    subparsers.add_parser("setup")

    sub_config = subparsers.add_parser("config")
    sub_config.add_argument("key", nargs="?")

    sub_benchmark = subparsers.add_parser("benchmark")
    sub_benchmark.add_argument("loops", nargs="?", type=int, default=10)
    sub_benchmark.add_argument("accounts", nargs="?", type=int, default=2)
    sub_benchmark.add_argument("medias", nargs="?", type=int, default=5)
    sub_benchmark.add_argument("comments", nargs="?", type=int, default=5)
    sub_benchmark.add_argument("--media_count", type=int, default=0)
    sub_benchmark.add_argument("--comment_count", type=int, default=0)
    sub_benchmark.add_argument("--subscription_count", type=int, default=0)
    sub_benchmark.add_argument("--sqlite", action="store_true")

    sub_make_migrations = subparsers.add_parser("make_migrations")
    sub_make_migrations.add_argument("comment", type=str, help="Comment of migration")
    subparsers.add_parser("migrate")

    args = parser.parse_args(*argv)
    match args.action:
        case "setup":
            return metrico.setup()
        case "config":
            return config(metrico, args)
        case "benchmark":
            return benchmark(metrico, args)
        case "make_migrations":
            return make_migrations(metrico, args)
        case "migrate":
            return migrate(metrico)
        case _:
            parser.print_help()
            return 1


if __name__ == "__main__":
    main(MetricoCore.default())
