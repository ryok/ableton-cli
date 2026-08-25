"""Static checks on the Remote Script's command dispatch.

The dispatch has two chains with different assignment conventions, and mixing
them up fails silently: the command reports success and returns an empty result.
That is worse than an error, so it is worth pinning without needing Live.

  outer chain  (12 spaces)  ->  response["result"] = ...
  inner chain  (24 spaces)  ->  result = ...        # returned via the queue
"""
import re
from pathlib import Path

SCRIPT = (Path(__file__).parent.parent / "remote_scripts"
          / "AbletonMCP_Remote_Script" / "__init__.py")
SOURCE = SCRIPT.read_text(encoding="utf-8")
LINES = SOURCE.splitlines()

BRANCH = re.compile(r'^(?P<indent> *)(?:el)?if command_type == "(?P<name>[a-z_]+)":')


def _strip_comments(lines):
    """Drop comment lines before checking for assignments.

    Without this the checks are satisfied by prose: the comment warning about
    the response["result"] convention contains that very string, which is
    exactly how the first version of this test passed against a broken branch.
    """
    return [ln for ln in lines if not ln.strip().startswith("#")]


def _branches(indent_width):
    """Yield (name, body_lines) for command branches at the given indent."""
    out = []
    for i, line in enumerate(LINES):
        m = BRANCH.match(line)
        if not m or len(m.group("indent")) != indent_width:
            continue
        body = []
        for nxt in LINES[i + 1:]:
            if nxt.strip() and len(nxt) - len(nxt.lstrip()) <= indent_width:
                break
            body.append(nxt)
        out.append((m.group("name"), _strip_comments(body)))
    return out


OUTER = _branches(12)
INNER = _branches(24)


def test_both_chains_were_found():
    """Guard the guard: if the indentation shifts, these tests must not go quiet."""
    assert len(OUTER) >= 5, f"outer chain not located (found {len(OUTER)})"
    assert len(INNER) >= 10, f"inner chain not located (found {len(INNER)})"


def test_outer_branches_assign_response_result():
    """A local `result` here is dropped, and the caller sees an empty success."""
    bad = [name for name, body in OUTER
           if not any(re.search(r'response\["result"\]\s*=', ln) for ln in body)]
    assert not bad, f"outer branches not assigning response['result']: {bad}"


def test_inner_branches_assign_local_result():
    """The inner chain's value travels back through the queue as `result`."""
    bad = [name for name, body in INNER
           if not any(re.search(r"^\s+result = ", ln) for ln in body)]
    assert not bad, f"inner branches not assigning result: {bad}"


def test_every_main_thread_command_is_in_the_inner_chain():
    """A command declared main-thread but dispatched outside it loses its guarantee."""
    import test_volume  # loads the module with _Framework stubbed
    declared = test_volume.mcp.MAIN_THREAD_COMMANDS
    dispatched = {name for name, _ in INNER}
    missing = declared - dispatched
    assert not missing, f"declared main-thread but not in the inner chain: {sorted(missing)}"


def test_no_command_is_dispatched_in_both_chains():
    overlap = {n for n, _ in OUTER} & {n for n, _ in INNER}
    assert not overlap, f"dispatched twice: {sorted(overlap)}"
