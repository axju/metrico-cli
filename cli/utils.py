from argparse import ArgumentParser
from datetime import datetime

from rich.console import Console

from metrico.database.query import AccountOrder, MediaCommentOrder, MediaOrder
from metrico.models import ModelStatus

console = Console()


class MetricoArgumentParser(ArgumentParser):
    def __init__(self, prog):
        super().__init__(prog=f"metrico {prog}", epilog="build by axju")

    def parse_args(self, *argv: str):  # type: ignore
        return super().parse_args(args=argv)


def parser_add_argument_basic_filter(parser):
    parser.add_argument("--limit", type=int, default=20)
    parser.add_argument("--offset", type=int)
    parser.add_argument("--order_asc", action="store_true")
    parser.add_argument("--filter_status", type=lambda x: ModelStatus[x], choices=list(ModelStatus))
    parser.add_argument("--filter_datetime", nargs=2, type=lambda s: datetime.strptime(s, "%Y-%m-%d"))
    parser.add_argument("--filter_account", nargs="*", type=str)
    parser.add_argument("--filter_account_id", nargs="*", type=int)
    return parser


def parser_add_argument_account_filter(parser):
    parser = parser_add_argument_basic_filter(parser)
    parser.add_argument("--order_by", type=lambda x: AccountOrder[x], choices=list(AccountOrder))
    parser.add_argument("--filter_stats_null", action="store_true")
    parser.add_argument("--filter_stats_views_null", action="store_true")
    parser.add_argument("--filter_comment_media_id", nargs="*", type=int)
    parser.add_argument("--filter_comment_media_account_id", nargs="*", type=int)
    return parser


def parser_add_argument_media_filter(parser):
    parser = parser_add_argument_basic_filter(parser)
    parser.add_argument("--order_by", type=lambda x: MediaOrder[x], choices=list(MediaOrder))
    return parser


def parser_add_argument_media_comment_filter(parser):
    parser = parser_add_argument_basic_filter(parser)
    parser.add_argument(
        "--order_by",
        type=lambda x: MediaCommentOrder[x],
        choices=list(MediaCommentOrder),
    )
    parser.add_argument("--filter_media_account_id", nargs="*", type=int)
    return parser
