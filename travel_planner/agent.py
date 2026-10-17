"""Entry point that ADK looks for: this module must expose `root_agent`."""
from .agents.root_agent import root_agent

__all__ = ["root_agent"]
