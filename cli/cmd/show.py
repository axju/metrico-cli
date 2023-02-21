# type: ignore
from typing import Any

from datetime import datetime
from time import sleep

from rich.live import Live
from rich.table import Column, Table
from sqlalchemy import func, select

from metrico import MetricoCore
from metrico import models
from metrico.cli.utils import (
    MetricoArgumentParser,
    parser_add_argument_account_filter,
    parser_add_argument_media_comment_filter,
    parser_add_argument_media_filter,
)
from metrico.database import alchemy
from metrico.database.query import AccountQuery, MediaCommentQuery, MediaQuery


def list_account(metrico: MetricoCore, args):
    headers = [
        Column(header="ID", justify="right"),
        "Status",
        "Platform",
        "Name",
        Column(header="Medias", justify="right"),
        Column(header="Views", justify="right"),
        Column(header="Followers", justify="right"),
        Column(header="Subscriptions", justify="right"),
    ]
    if args.show_rel:
        for name in ["Stats", "Info", "Comments", "Medias", "Followers", "Subscriptions"]:
            headers.append(Column(header=name, justify="right"))
    if args.show_dt:
        for name in ["First", "Last", "DT [h]", "Medias", "Views", "Followers", "Subscriptions"]:
            headers.append(Column(header=name, justify="right"))
    table = Table(
        *headers,
        expand=True,
        style="magenta",
        show_lines=True,
        # row_styles=["magenta", "white on magenta dim"],
    )
    with Live(table, refresh_per_second=4):
        account_query = AccountQuery.from_namespace(args)
        for account in metrico.db.iter_query(account_query):
            values = [
                f"{account.id}",
                f"{account.status}",
                f"{account.platform}",
                f"{account.info_name or '-'}",
                f"{account.stats_medias or '-'}",
                f"{account.stats_views or '-'}",
                f"{account.stats_followers or '-'}",
                f"{account.stats_subscriptions or '-'}",
            ]
            if args.show_rel:
                values += [
                    f"{account.stats.count():>3}",
                    f"{account.info.count():>3}",
                    f"{account.comments.count()}",
                    f"{account.medias.count()}",
                    f"{account.followers.count()}",
                    f"{account.subscriptions.count()}",
                ]
            if args.show_dt and account.stats.count():
                index_dt = account.stats.count() - 1
                if args.dt:
                    index_dt = find_index(account.stats, args.dt)
                values += [
                    f"{account.stats[index_dt].timestamp:%Y-%m-%d %H:%M}",
                    f"{account.stats[0].timestamp:%Y-%m-%d %H:%M}",
                    f"{(account.stats[0].timestamp - account.stats[index_dt].timestamp).total_seconds() / 3600:5.1f}",
                    f"{account.stats[0].medias - account.stats[index_dt].medias}",
                    f"{(account.stats[0].views or 0) - (account.stats[index_dt].views or 0)}",
                    f"{(account.stats[0].followers or 0) - (account.stats[index_dt].followers or 0)}",
                    f"{(account.stats[0].subscriptions or 0) - (account.stats[index_dt].subscriptions or 0)}",
                ]
            table.add_row(*values)


def find_index(stats, delta: int):
    if stats.count() < 2:
        return 0
    dt_index = 1
    dt_best = stats[0].timestamp - stats[dt_index].timestamp
    dt_error = abs((delta * 3600) - dt_best.total_seconds())
    for current_index in range(2, stats.count()):
        current_dt = stats[0].timestamp - stats[current_index].timestamp
        current_error = abs((delta * 3600) - current_dt.total_seconds())
        if current_error < dt_error:
            dt_index, dt_best, dt_error = current_index, current_dt, current_error
    return dt_index


def list_media(metrico: MetricoCore, args):
    headers = ["ID", "Created at", "Account", "Comments", "Likes", "Views", "Title"]
    if args.show_rel:
        headers += ["Comments", "Stats", "Info"]
    if args.show_dt:
        headers += ["First", "Last", "DT [h]", "Comments", "Likes", "Views"]

    table = Table(*headers)
    with Live(table, refresh_per_second=4):
        for media in metrico.db.iter_query(MediaQuery.from_namespace(args)):
            values = [
                f"{media.id}",
                f"{media.created_at}",
                f"[{media.account_id}] {media.account.info_name[:32]}",
                f"{media.stats_comments or '-':>8}",
                f"{media.stats_likes or '-':>8}",
                f"{media.stats_views or '-':>8}",
                f"{media.info_title[:32]}",
            ]
            if args.show_rel:
                values += [
                    f"{media.comments.count():>5}",
                    f"{media.stats.count():>3}",
                    f"{media.info.count():>3}",
                ]
            if args.show_dt:
                index_dt = media.stats.count() - 1
                if args.dt:
                    index_dt = find_index(media.stats, args.dt)
                values += [
                    f"{media.stats[index_dt].timestamp:%Y-%m-%d %H:%M}",
                    f"{media.stats[0].timestamp:%Y-%m-%d %H:%M}",
                    f"{(media.stats[0].timestamp - media.stats[index_dt].timestamp).total_seconds() / 3600:5.1f}",
                    f"{media.stats[0].comments - media.stats[index_dt].comments}",
                    f"{media.stats[0].likes - media.stats[index_dt].likes}",
                    f"{media.stats[0].views - media.stats[index_dt].views}",
                ]
            table.add_row(*values)


def list_media_comment(metrico: MetricoCore, args):
    table = Table("ID", "Account", "Media", "Media-Account", "Created", "Likes", "Text")
    with Live(table, refresh_per_second=4):
        for comment in metrico.db.iter_query(MediaCommentQuery.from_namespace(args)):
            table.add_row(
                f"{comment.id:>7}",
                f"[{comment.account_id}] {comment.account.info_name[:32]}",
                f"[{comment.media_id}] {comment.media.info_title[:32]}",
                f"[{comment.media.account_id}] {comment.media.account.info_name[:32]}",
                f"{comment.created_at}",
                f"{comment.likes}",
                f"{comment.text[:100]}",
            )


def account_info(metrico: MetricoCore, account: alchemy.Account):
    account_fields = {
        "Name": account.info_name,
        "Bio": account.info_bio.split("\n")[0][:200] if account.info_bio else "-",
        "Medias": account.stats_medias,
        "Views": account.stats_views,
        "Followers": account.stats_followers,
        "Subscriptions": account.stats_subscriptions,
        "Update-Info": account.info_last_update,
        "Update-Stats": account.stats_last_update,
    }
    account_relations = {
        "Medias": alchemy.Media,
        "Comments": alchemy.MediaComment,
        "Subscriptions": alchemy.AccountSubscription,
        "Info": alchemy.AccountInfo,
        "Stats": alchemy.AccountStats,
    }
    account_stats_map = {
        "Media-Comments [rel]": select(func.count(alchemy.MediaComment.id)).join(alchemy.Media).where(alchemy.Media.account_id == account.id),
        "Media-Comments-Likes [rel]": select(func.sum(alchemy.MediaComment.likes)).join(alchemy.Media).where(alchemy.Media.account_id == account.id),
        "Media-Comments-Accounts [rel]": select(alchemy.Account.id, func.count(alchemy.Account.id))
        .join(alchemy.MediaComment, alchemy.Account.id == alchemy.MediaComment.account_id)
        .join(alchemy.Media, alchemy.Media.id == alchemy.MediaComment.media_id)
        .where(alchemy.Media.account_id == account.id)
        .group_by(alchemy.Account.id),
        "Media-Comments": select(func.sum(alchemy.Media.stats_comments)).where(alchemy.Media.account_id == account.id),
        "Media-Likes": select(func.sum(alchemy.Media.stats_likes)).where(alchemy.Media.account_id == account.id),
        "Media-Views": select(func.sum(alchemy.Media.stats_views)).where(alchemy.Media.account_id == account.id),
    }

    print(f"ID: {account.id} - Identifier: {account.identifier} - Platform: {account.platform}")
    print("Account Values:")
    name_len = max(map(len, account_fields.keys())) + 1
    for name, value in account_fields.items():
        print(f"{name:>{name_len}}: {value}")

    print("\nAccount Relations:")
    name_len = max(map(len, account_relations.keys())) + 1
    with metrico.db.Session() as session:
        for name, model in account_relations.items():
            value = session.scalar(select(func.count(model.id)).where(model.account_id == account.id))
            print(f"{name:>{name_len}}: {value}")

    print("\nAccount Stats:")
    name_len = max(map(len, account_stats_map.keys())) + 1
    with metrico.db.Session() as session:
        for name, stmt in account_stats_map.items():
            value = session.scalar(stmt)
            print(f"{name:>{name_len}}: {value}")


def account_stats(metrico: MetricoCore, account: alchemy.Account, args):
    stmt = (
        select(alchemy.AccountStats)
        .where(alchemy.AccountStats.account_id == account.id)
        .order_by(alchemy.AccountStats.timestamp.desc())
        .limit(args.limit or 10)
    )
    table = Table("ID", "Timestamp", "Medias", "Views", "Followers", "Subscriptions")
    with metrico.db.Session() as session, Live(table, refresh_per_second=4):
        for stat in session.execute(stmt).scalars():
            table.add_row(
                f"{stat.id}",
                f"{stat.timestamp}",
                f"{stat.medias}",
                f"{stat.views}",
                f"{stat.followers}",
                f"{stat.subscriptions}",
            )


def account_subscriptions(metrico: MetricoCore, account: alchemy.Account, args):
    stmt = select(alchemy.AccountSubscription).where(alchemy.AccountSubscription.account_id == account.id).limit(args.limit or 10)
    table = Table("ID", "Account")
    with metrico.db.Session() as session, Live(table, refresh_per_second=4):
        for subscription in session.execute(stmt).scalars():
            table.add_row(
                f"{subscription.id:>5}",
                f"[{subscription.subscribed_account.id}] {subscription.subscribed_account.info_name}",
            )


def account_followers(metrico: MetricoCore, account: alchemy.Account, args):
    stmt = select(alchemy.AccountSubscription).where(alchemy.AccountSubscription.subscribed_account_id == account.id).limit(args.limit or 10)
    table = Table("ID", "Account")
    with metrico.db.Session() as session, Live(table, refresh_per_second=4):
        for follower in session.execute(stmt).scalars():
            table.add_row(
                f"{follower.id:>5}",
                f"[{follower.account.id}] {follower.account.info_name}",
            )


def account_comments(metrico: MetricoCore, account: alchemy.Account, args):
    stmt = (
        select(alchemy.Account, func.count(alchemy.MediaComment.id))
        .join(alchemy.MediaComment, alchemy.Account.id == alchemy.MediaComment.account_id)
        .join(alchemy.Media, alchemy.Media.id == alchemy.MediaComment.media_id)
        .where(alchemy.Media.account_id == account.id)
        .group_by(alchemy.Account.id)
        .order_by(func.count(alchemy.MediaComment.id).desc())
        .limit(args.limit or 10)
    )
    table = Table("Count", "Account")
    with metrico.db.Session() as session, Live(table, refresh_per_second=4):
        for value, comments in session.execute(stmt).all():
            table.add_row(f"{comments:>5}", f"[{value.id}] {value.info_name}")


def account_commented(metrico: MetricoCore, account: alchemy.Account, args):
    stmt = (
        select(alchemy.Media, func.count(alchemy.MediaComment.id))
        .join(alchemy.MediaComment, alchemy.MediaComment.media_id == alchemy.Media.id)
        .where(alchemy.MediaComment.account_id == account.id)
        .group_by(alchemy.Media.id)
        .order_by(func.count(alchemy.MediaComment.id).desc())
        .limit(args.limit or 10)
    )
    table = Table("Count", "Account", "Media", "Media-Created")
    with metrico.db.Session() as session, Live(table, refresh_per_second=4):
        for value, comments in session.execute(stmt).all():
            table.add_row(
                f"{comments:>5}",
                f"[{value.account.id}] {value.account.info_name}",
                f"[{value.id}] {value.info_title}",
                f"{value.created_at}",
            )


def info_media(media: alchemy.Media):
    print(f"ID: {media.id} - Identifier: {media.identifier} - Account: {media.account.info_name} [id={media.account.id}] - Platform: {media.account.platform}")
    print(
        f"  Update:\n    Info:     {media.info_last_update} [{media.info.count()}]\n    Data:     {media.stats_last_update} [{media.stats.count()}]\n    Comments: {media.comments_last_update} [{media.comments.count()}]"
    )

    print(
        f"  Info [{media.info.count()}]:\n    Title:         {media.info[0].title}\n    Caption:       {media.info[0].caption[:120]}\n    Dis. Comments: {media.info[0].disable_comments}"
    )
    print(f"  Stats [{media.stats.count()}]:\n    Comments: {media.stats_comments:>8}\n    Likes:    {media.stats_likes:>8}")


def list_triggers(metrico: MetricoCore, args):
    def update_data(data):
        table = Table("ID", "Status", "Name", "Accounts", "Medias", "Calls", "Last dt", "Success")
        for row in data:
            table.add_row(*row)
        return table

    stmt = select(alchemy.Trigger)
    if args.limit:
        stmt = stmt.limit(args.limit)

    with Live() as live:
        while True:
            with metrico.db.Session() as session:
                rows = []
                for trigger in session.execute(stmt).scalars():
                    values = [
                        f"{trigger.id}",
                        f"{trigger.status}",
                        f"{trigger.name}",
                        f"{trigger.accounts.count()}",
                        f"{trigger.medias.count()}",
                        f"{trigger.stats.count()}",
                    ]
                    if trigger.stats.count() and trigger.status != models.TriggerStatus.RUN:
                        values += [
                            f"{trigger.stats[0].finished - trigger.stats[0].started}",
                            f"{trigger.stats[0].success}",
                        ]
                    rows.append(values)

                live.update(update_data(rows))
                if not args.dynamic:
                    break
                sleep(args.dt)


def info_trigger(metrico: MetricoCore, trigger: alchemy.Trigger, args):

    with metrico.db.Session() as session:
        stmt = select(func.count()).where(alchemy.TriggerAccount.trigger == trigger)
        total = session.scalar(stmt)

    table = Table("ID", f"Account {args.limit} of {total}")
    with Live(table, refresh_per_second=4):
        query = trigger.accounts.order_by(alchemy.TriggerAccount.timestamp.asc())
        if args.limit:
            query = query.limit(args.limit)
        for item in query:
            table.add_row(f"{item.id}", f"[{item.account_id}] {item.account.info_name}")


def stats_all(metrico: MetricoCore, args):
    def update_data(data):
        table = Table("Timestamp", *alchemy_map.keys())
        for row in data:
            table.add_row(*row)
        return table

    alchemy_map = {
        "Account": alchemy.Account,
        "Account-Subscription": alchemy.AccountSubscription,
        "Account-Info": alchemy.AccountInfo,
        "Account-Data": alchemy.AccountStats,
        "Media": alchemy.Media,
        "Media-Info": alchemy.MediaInfo,
        "Media-Data": alchemy.MediaStats,
        "Media-Comment": alchemy.MediaComment,
    }

    rows: list[list[str]] = []
    values_last: list[Any] = []
    with Live() as live:
        while True:
            try:
                with metrico.db.Session() as session:
                    values = [datetime.now()] + [session.query(model).count() for name, model in alchemy_map.items()]
                    if values_last:
                        values_dt = [values[i] - values_last[i] for i in range(len(values))]
                        rows.append([f"{values[0]}"] + [f"{values[i]} [{values_dt[i]/values_dt[0].total_seconds():.2f}]" for i in range(1, len(values))])
                    else:
                        rows.append([str(value) for value in values])

                    live.update(update_data(rows))
                    if not args.dynamic:
                        break

                    if len(rows) > args.limit:
                        rows = rows[-args.limit :]

                    values_last = values
                    sleep(args.dt)
            except KeyboardInterrupt:
                break
            except Exception as exc:
                raise exc


def parse_args(*argv: str):
    parser = MetricoArgumentParser("show")
    subparsers = parser.add_subparsers(dest="action", help="sub-command help")

    sub_accounts = subparsers.add_parser("accounts")
    parser_add_argument_account_filter(sub_accounts)
    sub_accounts.add_argument("--show_rel", action="store_true", help="Show length of relationship alchemy")
    sub_accounts.add_argument("--show_dt", action="store_true", help="Show stats changing")
    sub_accounts.add_argument("--dt", type=int, default=0, help="Set dt [h] for the changing stats")

    sub_account = subparsers.add_parser("account")
    sub_account.add_argument("--limit", type=int, default=10)
    sub_account.add_argument("account", type=int)
    sub_account.add_argument(
        "mode",
        nargs="?",
        choices=[
            "info",
            "stats",
            "subscriptions",
            "followers",
            "commented",
            "comments",
        ],
        default="info",
        const="info",
    )

    sub_medias = subparsers.add_parser("medias")
    sub_medias = parser_add_argument_media_filter(sub_medias)
    sub_medias.add_argument("--show_rel", action="store_true", help="Show length of relationship models")
    sub_medias.add_argument("--show_dt", action="store_true", help="Show stats changing")
    sub_medias.add_argument("--dt", type=int, default=0, help="Set dt [h] for the changing stats")

    sub_media = subparsers.add_parser("media")
    sub_media.add_argument("--limit", type=int, default=10)
    sub_media.add_argument("media", type=int)
    sub_media.add_argument(
        "mode",
        nargs="?",
        choices=[
            "info",
        ],
        default="info",
        const="info",
    )

    sub_comments = subparsers.add_parser("comments")
    parser_add_argument_media_comment_filter(sub_comments)

    sub_triggers = subparsers.add_parser("triggers")
    sub_triggers.add_argument("--dynamic", action="store_true")
    sub_triggers.add_argument("--limit", type=int, default=10)
    sub_triggers.add_argument("--dt", type=int, default=2)

    sub_trigger = subparsers.add_parser("trigger")
    sub_trigger.add_argument("--limit", type=int, default=10)
    sub_trigger.add_argument("triggers", type=int)

    sub_stats = subparsers.add_parser("stats")
    sub_stats.add_argument("--dynamic", action="store_true")
    sub_stats.add_argument("--limit", type=int, default=10)
    sub_stats.add_argument("--dt", type=int, default=2)

    return parser, parser.parse_args(*argv)


def main(metrico: MetricoCore, *argv: str) -> int:
    parser, args = parse_args(*argv)
    match args.action:
        case "accounts":
            list_account(metrico, args)
        case "account":
            account = metrico.db.get_account(args.account)
            if account is None:
                return 1
            match args.mode:
                case "stats":
                    account_stats(metrico, account, args)
                case "subscriptions":
                    account_subscriptions(metrico, account, args)
                case "followers":
                    account_followers(metrico, account, args)
                case "comments":
                    account_comments(metrico, account, args)
                case "commented":
                    account_commented(metrico, account, args)
                case "info" | _:
                    account_info(metrico, account)
        case "medias":
            list_media(metrico, args)
        case "media":
            with metrico.db.Session() as session:
                media = metrico.db.get_media(args.media, session=session)
                if media:
                    info_media(media)
        case "comments":
            list_media_comment(metrico, args)
        case "triggers":
            list_triggers(metrico, args)
        case "triggers":
            with metrico.db.Session() as session:
                trigger = metrico.db.get_trigger(args.trigger, session=session)
                if trigger:
                    info_trigger(metrico, trigger, args)
        case "stats":
            stats_all(metrico, args)
        case _:
            parser.print_help()
            return 1
    return 0


if __name__ == "__main__":
    main(MetricoCore.default())
