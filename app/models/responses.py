from typing import Dict, List, Any
from dataclasses import dataclass


@dataclass
class APIResponse:
    status: str
    message: str
    data: Dict[str, Any] = None


@dataclass
class ErrorResponse:
    error: str
    message: str
    details: Dict[str, Any] = None


@dataclass
class ChannelStatsResponse:
    channel_id: str
    total_interactions: int


@dataclass
class UserStatsResponse:
    user_id: str
    total_interactions: int
    per_channel: List[Dict[str, int]]