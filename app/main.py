import asyncio
import pathlib
import logging

import aiohttp_jinja2
import jinja2
from aiohttp import web
from telethon.errors import AuthKeyDuplicatedError

from .telegram import Client
from .routes import register_routes, initialize_chats
from .views import Views
from .config import host, port, session_string, api_id, api_hash, debug


log = logging.getLogger(__name__)

_tg_ready = asyncio.Event()


class Indexer:
    TEMPLATES_ROOT = pathlib.Path(__file__).parent / "templates"

    def __init__(self):
        self.server = web.Application()
        self.tg_client = Client(session_string, api_id, api_hash)

    async def _connect_telegram(self):
        """Connect to Telegram in background with retries."""
        max_retries = 10
        for attempt in range(1, max_retries + 1):
            try:
                await self.tg_client.connect()
                log.info("Telegram client connected!")
                _tg_ready.set()
                return
            except AuthKeyDuplicatedError:
                wait = min(30 * attempt, 180)
                log.warning(
                    f"Session in use by another instance (attempt {attempt}/{max_retries}). "
                    f"Retrying in {wait}s — stop the deployed app to free the session."
                )
                try:
                    await self.tg_client.disconnect()
                except Exception:
                    pass
                self.tg_client = Client(session_string, api_id, api_hash)
                await asyncio.sleep(wait)
            except Exception as e:
                log.error(f"Telegram connection error: {e}")
                await asyncio.sleep(30)
        log.error("Could not connect to Telegram after all retries.")

    async def cleanup(self, *args):
        try:
            await self.tg_client.disconnect()
        except Exception:
            pass
        log.debug("Telegram client disconnected.")

    async def _run(self):
        views = Views(self.tg_client)
        register_routes(self.server, views)

        loader = jinja2.FileSystemLoader(str(self.TEMPLATES_ROOT))
        aiohttp_jinja2.setup(self.server, loader=loader)
        self.server.on_cleanup.append(self.cleanup)

        runner = web.AppRunner(self.server)
        await runner.setup()
        site = web.TCPSite(runner, host=host, port=port)
        await site.start()
        log.info(f"======== Running on http://{host}:{port} ========")

        # Connect Telegram in background and initialize chats after
        from .routes import initialize_chats

        async def _connect_then_init():
            await self._connect_telegram()
            await initialize_chats(self.tg_client)

        asyncio.ensure_future(_connect_then_init())

        try:
            await asyncio.Event().wait()
        except (KeyboardInterrupt, SystemExit):
            pass
        finally:
            await runner.cleanup()

    def run(self):
        asyncio.run(self._run())
