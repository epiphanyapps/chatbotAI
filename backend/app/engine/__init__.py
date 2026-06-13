"""Conversation engine: the single source of truth for generating Sophia's replies.

Web chat (WebSocket/REST) and the Telegram bot both flow through this package so
voice, memory, and model selection stay identical across channels.
"""
