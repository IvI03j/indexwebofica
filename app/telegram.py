import math
import logging
import asyncio

from telethon import TelegramClient, utils
from telethon.sessions import StringSession

class Client(TelegramClient):

    def __init__(self, session_string, *args, **kwargs):
        super().__init__(StringSession(session_string), *args, **kwargs)
        self.log = logging.getLogger(__name__)
    

    async def download(self, file, file_size, offset, limit):
        part_size_kb = utils.get_appropriated_part_size(file_size)
        part_size = int(part_size_kb * 1024)
        first_part_cut = offset % part_size
        first_part = math.floor(offset / part_size)
        last_part = math.ceil(limit / part_size)
        # How many bytes to keep from the last chunk
        last_part_cut = limit % part_size or part_size
        part_count = math.ceil(file_size / part_size)
        part = first_part
        bytes_sent = 0
        bytes_needed = limit - offset
        try:
            async for chunk in self.iter_download(
                file,
                offset=first_part * part_size,
                request_size=part_size,
                limit=last_part - first_part,   # only fetch needed parts
            ):
                if part == first_part:
                    chunk = chunk[first_part_cut:]
                if part == last_part - 1:
                    # trim trailing bytes beyond the requested range
                    remaining = bytes_needed - bytes_sent
                    chunk = chunk[:remaining]
                if not chunk:
                    part += 1
                    continue
                yield chunk
                bytes_sent += len(chunk)
                self.log.debug(f"Part {part}/{last_part} (total {part_count}) served!")
                part += 1
                if bytes_sent >= bytes_needed:
                    break
            self.log.debug("serving finished")
        except (GeneratorExit, StopAsyncIteration, asyncio.CancelledError):
            self.log.debug("file serve interrupted")
            raise
        except Exception:
            self.log.debug("file serve errored", exc_info=True)
