import re
from dataclasses import dataclass
from datetime import date, timedelta

from app.agent.tools import (
    draft_follow_up_impl,
    edit_interaction_impl,
    get_hcp_snapshot_impl,
    list_hcps_impl,
    log_interaction_impl,
    recommend_next_best_action_impl,
)


COMMAND_PATTERNS = [
    r"list all hcps available in the crm\.?",
    r"show me the snapshot for hcp \d+\.?",
    r"log an interaction for hcp \d+.*?(?=(?:list all hcps available in the crm|show me the snapshot for hcp|edit interaction|recommend the next best action for hcp|draft a follow-up note for hcp)\b|$)",
    r"edit interaction \d+.*?(?=(?:list all hcps available in the crm|show me the snapshot for hcp|log an interaction for hcp|recommend the next best action for hcp|draft a follow-up note for hcp)\b|$)",
    r"recommend the next best action for hcp \d+.*?(?=(?:list all hcps available in the crm|show me the snapshot for hcp|log an interaction for hcp|edit interaction|draft a follow-up note for hcp)\b|$)",
    r"draft a follow-up note for hcp \d+.*?(?=(?:list all hcps available in the crm|show me the snapshot for hcp|log an interaction for hcp|edit interaction|recommend the next best action for hcp)\b|$)",
]


@dataclass
class ParsedResponse:
    handled: bool
    reply: str
    tool_messages: list[str]


def try_handle_menu_commands(message: str) -> ParsedResponse:
    commands = _extract_commands(message)
    if not commands:
        return ParsedResponse(handled=False, reply="", tool_messages=[])

    outputs: list[str] = []
    summaries: list[str] = []
    for command in commands:
        summary, output = _execute_command(command)
        summaries.append(summary)
        outputs.append(output)

    return ParsedResponse(handled=True, reply="\n".join(summaries), tool_messages=outputs)


def _extract_commands(message: str) -> list[str]:
    lowered = " ".join(message.lower().split())
    matches: list[tuple[int, int]] = []
    for pattern in COMMAND_PATTERNS:
        for match in re.finditer(pattern, lowered, flags=re.IGNORECASE | re.DOTALL):
            matches.append((match.start(), match.end()))

    if not matches:
        return []

    matches.sort()
    commands: list[str] = []
    last_end = -1
    for start, end in matches:
        if start < last_end:
            continue
        commands.append(lowered[start:end].strip(" ."))
        last_end = end
    return commands


def _execute_command(command: str) -> tuple[str, str]:
    if command.startswith("list all hcps available in the crm"):
        return "Listed available HCPs.", list_hcps_impl()

    if command.startswith("show me the snapshot for hcp"):
        hcp_id = _extract_id(command, "hcp")
        return f"Loaded snapshot for HCP {hcp_id}.", get_hcp_snapshot_impl(hcp_id)

    if command.startswith("log an interaction for hcp"):
        hcp_id = _extract_id(command, "hcp")
        channel = _extract_channel(command)
        topic = _extract_phrase(command, "about", [", positive sentiment", ", neutral sentiment", ", negative sentiment", ", and a follow-up", " and a follow-up"])
        sentiment = _extract_sentiment(command)
        follow_up_date = _extract_follow_up_date(command)
        output = log_interaction_impl(
            hcp_id=hcp_id,
            channel=channel,
            title=_build_interaction_title(topic),
            objective=f"Discuss {topic}",
            summary=f"Shared {topic} with the HCP via {channel.lower()}.",
            sentiment=sentiment,
            follow_up_date=follow_up_date,
            next_action=_build_next_action(topic, follow_up_date),
        )
        return f"Logged interaction for HCP {hcp_id}.", output

    if command.startswith("edit interaction"):
        interaction_id = _extract_id(command, "interaction")
        next_action = _extract_phrase(command, "update the next action to", [])
        output = edit_interaction_impl(interaction_id=interaction_id, next_action=_cleanup_text(next_action))
        return f"Updated interaction {interaction_id}.", output

    if command.startswith("recommend the next best action for hcp"):
        hcp_id = _extract_id(command, "hcp")
        goal_match = re.search(r"to (.+)$", command)
        business_goal = (
            _cleanup_text(goal_match.group(1)) if goal_match else "improve engagement"
        )
        return (
            f"Recommended next best action for HCP {hcp_id}.",
            recommend_next_best_action_impl(hcp_id, business_goal),
        )

    if command.startswith("draft a follow-up note for hcp"):
        hcp_id = _extract_id(command, "hcp")
        purpose_match = re.search(r"about (.+)$", command)
        purpose = _cleanup_text(purpose_match.group(1)) if purpose_match else "the recent discussion"
        return f"Drafted a follow-up note for HCP {hcp_id}.", draft_follow_up_impl(hcp_id, purpose)

    raise ValueError(f"Unsupported command: {command}")


def _extract_id(command: str, noun: str) -> int:
    match = re.search(rf"{noun} (\d+)", command)
    if not match:
        raise ValueError(f"Missing {noun} id in command: {command}")
    return int(match.group(1))


def _extract_channel(command: str) -> str:
    channels = {
        "video call": "Video call",
        "in-person": "In-person",
        "whatsapp": "WhatsApp",
        "email": "Email",
        "phone call": "Phone call",
    }
    for raw, label in channels.items():
        if raw in command:
            return label
    return "Other"


def _extract_sentiment(command: str) -> str:
    for sentiment in ("positive", "neutral", "negative"):
        if f"{sentiment} sentiment" in command:
            return sentiment
    return "neutral"


def _extract_follow_up_date(command: str) -> str | None:
    if "next week" in command:
        return (date.today() + timedelta(days=7)).isoformat()
    return None


def _extract_phrase(command: str, start_marker: str, end_markers: list[str]) -> str:
    try:
        remainder = command.split(start_marker, 1)[1]
    except IndexError:
        return ""

    end_index = len(remainder)
    for marker in end_markers:
        marker_index = remainder.find(marker)
        if marker_index != -1:
            end_index = min(end_index, marker_index)
    return _cleanup_text(remainder[:end_index])


def _cleanup_text(value: str) -> str:
    cleaned = value.strip(" .,\n\t")
    cleaned = re.split(r"\bthese menus?\b|\bpls fix it\b|\bplease fix it\b", cleaned, maxsplit=1)[0]
    return cleaned.strip(" .,\n\t")


def _build_interaction_title(topic: str) -> str:
    if not topic:
        return "HCP interaction"
    trimmed = topic[0].upper() + topic[1:]
    if len(trimmed) <= 80:
        return trimmed
    return f"{trimmed[:77]}..."


def _build_next_action(topic: str, follow_up_date: str | None) -> str:
    if follow_up_date:
        return f"Follow up on {topic} on {follow_up_date}."
    return f"Follow up on {topic}."
