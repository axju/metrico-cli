from . import add, hunt, show, tools

__all__ = ["MAIN_CMDS", "add", "hunt", "show", "tools"]


MAIN_CMDS = {
    "add": add.main,  # type: ignore
    "hunt": hunt.main,
    "show": show.main,  # type: ignore
    "tools": tools.main,
}
