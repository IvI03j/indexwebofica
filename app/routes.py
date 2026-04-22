import random
import string
import logging
from aiohttp import web
from .config import index_settings, alias_ids, chat_ids

log = logging.getLogger(__name__)

MOVIES_THREAD_ID = 5
SERIES_THREAD_ID = 11


def generate_alias_id(chat):
    chat_id = chat.id
    title = chat.title
    while True:
        alias_id = "".join(
            [
                random.choice(string.ascii_letters + string.digits)
                for _ in range(len(str(chat_id)))
            ]
        )
        if alias_id in alias_ids:
            continue
        alias_ids.append(alias_id)
        chat_ids.append({"chat_id": chat_id, "alias_id": alias_id, "title": title})
        return alias_id


def register_routes(app, handler):
    h = handler
    p = r"/{chat:[^/]+}"
    routes = [
        web.get("/", h.home),
        web.get("/auth", h.web_auth),
        web.get("/auth/telegram-webapp", h.telegram_webapp_auth),
        web.get("/blocked", h.blocked_view),
        web.get("/plans", h.plans_view),
        web.post("/activate-pass", h.activate_pass),
        web.get("/devices", h.devices_view),
        web.get("/logout", h.logout),
        web.post("/otg", h.dynamic_view),
        web.get("/otg", h.otg_view),
        web.get("/pc", h.playlist_creator),
        web.get("/_api/catalog", h.api_catalog),
        web.get("/playlist.m3u", h.playlist_m3u),
        web.get(p + r"/playlist.m3u", h.playlist_m3u),
        web.get(p, h.index),
        web.get(p + r"/logo", h.logo),
        web.get(p + r"/{id:\d+}/view", h.info),
        web.get(p + r"/{id:\d+}/play", h.player_view),
        web.get(p + r"/{id:\d+}/download", h.download_get),
        web.get(p + r"/{id:\d+}/thumbnail", h.thumbnail_get),
        web.get(r"/{id:\d+}/view", h.info),
        web.get(r"/{id:\d+}/play", h.player_view),
        web.get(r"/{id:\d+}/download", h.download_get),
        web.view(r"/{wildcard:.*}", h.wildcard),
    ]
    app.add_routes(routes)


async def setup_routes(app, handler):
    register_routes(app, handler)


async def initialize_chats(client):
    index_all = index_settings["index_all"]
    index_private = index_settings["index_private"]
    index_group = index_settings["index_group"]
    index_channel = index_settings["index_channel"]
    _exclude = index_settings.get("exclude_chats")
    _include = index_settings.get("include_chats")
    exclude_chats = [int(x) for x in _exclude] if isinstance(_exclude, list) else []
    include_chats = [int(x) for x in _include] if isinstance(_include, list) else []

    if index_all:
        async for chat in client.iter_dialogs():
            if chat.id in exclude_chats:
                continue
            alias_id = None
            if chat.is_user:
                if index_private:
                    alias_id = generate_alias_id(chat)
            elif chat.is_channel:
                if index_channel:
                    alias_id = generate_alias_id(chat)
            else:
                if index_group:
                    alias_id = generate_alias_id(chat)
            if alias_id:
                log.debug(f"Index added for {chat.id} :: {chat.title} at /{alias_id}")
    else:
        for chat_id in include_chats:
            chat = await client.get_entity(chat_id)
            alias_id = generate_alias_id(chat)
            log.debug(f"Index added for {chat.id} :: {chat.title} at /{alias_id}")
