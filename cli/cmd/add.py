# type: ignore
import sys

from rich.table import Table

from metrico import MetricoCore, models
from metrico.cli.utils import MetricoArgumentParser, console


def show_data(datas: list[dict]):
    table = Table("NO", "Platform", "Name", "Stats")
    for index, data in enumerate(datas):
        row, item = [str(index), data["platform"]], data["item"]
        match item:
            case models.Account() as account:
                row.append(account.info.name)
                if item.stats:
                    row.append(f"Medias:{account.stats.medias:<4} | Followers:{account.stats.followers}")
                else:
                    row.append("-")
                if account.info.bio:
                    row.append(account.info.bio.split("\n")[0][:100])
                else:
                    row.append("-")

            case models.Media() as media:
                if media.account.info:
                    row.append(f"{media.account.info.name} | {media.info.title}")
                else:
                    row.append(media.info.title)
                if media.stats:
                    row.append(f"Likes:{media.stats.likes:<6} | Comments:{media.stats.comments}")
                else:
                    row.append("-")

        table.add_row(*row)
    console.print(table)


def select_index(max_index: int):
    while True:
        raw_input = input("Select NO. default=0, exit with 'e': ") or 0
        if raw_input in ["E", "e"]:
            sys.exit(1)
        try:
            index = int(raw_input)
            if index in range(max_index):
                return index
        except:
            console.print("Please enter a number!")


def main(metrico: MetricoCore, *argv: str) -> int:
    """
    add account platform id
    """
    parser = MetricoArgumentParser("add")
    parser.add_argument("--full", action="store_true")
    parser.add_argument("value")
    args = parser.parse_args(*argv)

    datas = []
    for platform, hunter in metrico.hunter.items():
        if items := hunter.analyze(args.value, full=args.full):
            datas += [{"platform": platform, "item": item} for item in items]

    if not datas:
        console.print("No data!")
        sys.exit(1)

    show_data(datas)
    index = select_index(len(datas))

    item = metrico.db.create(datas[index]["platform"], datas[index]["item"])
    console.print("create", item)
    return 0


if __name__ == "__main__":
    main(MetricoCore.default())
