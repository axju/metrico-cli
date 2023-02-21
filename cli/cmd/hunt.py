from typing import Any, Callable

import logging

from metrico import MetricoCore
from metrico.cli.utils import MetricoArgumentParser, parser_add_argument_account_filter, parser_add_argument_media_filter
from metrico.database.query import AccountQuery, MediaQuery
from metrico.utils import update_list

logger = logging.getLogger(__name__)


def get_args(*argv: str):
    parser = MetricoArgumentParser("hunt")

    subparsers = parser.add_subparsers(dest="action", help="sub-command help")
    parser.add_argument("--threads", type=int, default=8)

    sub_accounts = subparsers.add_parser("accounts")
    sub_accounts = parser_add_argument_account_filter(sub_accounts)
    sub_accounts.add_argument("--media_count", type=int, default=-1)
    sub_accounts.add_argument("--comment_count", type=int, default=-1)
    sub_accounts.add_argument("--subscription_count", type=int, default=-1)

    sub_account = subparsers.add_parser("account")
    sub_account.add_argument("--media_count", type=int, default=-2)
    sub_account.add_argument("--comment_count", type=int, default=-1)
    sub_account.add_argument("--subscription_count", type=int, default=-2)
    sub_account.add_argument("account_id", type=int)

    sub_medias = subparsers.add_parser("medias")
    sub_medias = parser_add_argument_media_filter(sub_medias)
    sub_medias.add_argument("--comment_count", type=int, default=-1)

    sub_media = subparsers.add_parser("media")
    sub_media.add_argument("--comment_count", type=int, default=-2)
    sub_media.add_argument("media_id", type=int)

    sub_trigger = subparsers.add_parser("trigger")
    sub_trigger.add_argument("trigger", type=str)
    sub_trigger.add_argument("--limit", type=int)

    return parser.parse_args(*argv)


def get_thread_data(metrico: MetricoCore, args) -> tuple[list[int], Callable[[int, Any], None], dict]:
    obj_ids: list[int] = []
    update_func: Callable[[int, Any], None] = metrico.update_media
    kwargs = {"comment_count": args.comment_count}

    if args.action in ["account", "accounts"]:
        update_func = metrico.update_account
        kwargs = {
            "media_count": args.media_count,
            "comment_count": args.comment_count,
            "subscription_count": args.subscription_count,
        }

    match args.action:
        case "accounts":
            obj_ids = [obj.id for obj in metrico.db.iter_query(AccountQuery.from_namespace(args))]
        case "account":
            account = metrico.db.get_account(args.account_id)
            if account:
                obj_ids = [account.id]
        case "medias":
            obj_ids = [obj.id for obj in metrico.db.iter_query(MediaQuery.from_namespace(args))]
        case "media":
            media = metrico.db.get_media(args.media_id)
            if media:
                obj_ids = [media.id]
        case "trigger":
            trigger = metrico.db.get_trigger(args.trigger)
            if trigger:
                obj_ids = [trigger.id]
            else:
                print(f"No triggers with name '{args.trigger}'")
        case _:
            ...
    return obj_ids, update_func, kwargs


def main(metrico: MetricoCore, *argv: str) -> int:
    args = get_args(*argv)
    if args.action == "trigger":
        return metrico.run_trigger(args.trigger, threads=args.threads, limit=args.limit or 100)

    obj_ids, update_func, kwargs = get_thread_data(metrico, args)
    update_list(obj_ids, update_func, args.threads, **kwargs)
    return 0


if __name__ == "__main__":
    main(MetricoCore.default())
