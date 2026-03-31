import asyncio
import logging
import random
import io
from PIL import Image, ImageDraw

from aiohttp import web
import aiohttp_jinja2
from markupsafe import Markup
from .tmdb import enrich_entry
from telethon.tl import types
from telethon.tl.custom import Message
from telethon.tl.types import User, Chat, Channel

from .util import get_file_name, get_human_size
from .config import otg_settings, chat_ids, enable_otg, host

log = logging.getLogger(__name__)


def _has_media(m):
    if not m.media:
        return False
    if isinstance(m.media, types.MessageMediaWebPage):
        return False
    if not m.file:
        return False
    mime = m.file.mime_type or ""
    return mime.startswith("video/")


def _group_results(results):
    """Group episodes of the same series into one card entry."""
    grouped = []
    seen = {}  # tmdb_id -> index in grouped

    for entry in results:
        tmdb = entry.get('tmdb')
        parsed = entry.get('parsed')
        is_series = tmdb and tmdb.get('is_series') and tmdb.get('tmdb_id')

        if is_series:
            tid = tmdb['tmdb_id']
            if tid in seen:
                existing = grouped[seen[tid]]
                existing.setdefault('episodes', []).append({
                    'url': entry['url'],
                    'download': entry['download'],
                    'insight': entry['insight'],
                    'human_size': entry['human_size'],
                    'season': parsed.get('season') if parsed else None,
                    'episode': parsed.get('episode') if parsed else None,
                    'date': entry['date'],
                })
            else:
                entry['episodes'] = [{
                    'url': entry['url'],
                    'download': entry['download'],
                    'insight': entry['insight'],
                    'human_size': entry['human_size'],
                    'season': parsed.get('season') if parsed else None,
                    'episode': parsed.get('episode') if parsed else None,
                    'date': entry['date'],
                }]
                seen[tid] = len(grouped)
                grouped.append(entry)
        else:
            grouped.append(entry)

    return grouped


class Views:

    def __init__(self, client):
        self.client = client

    async def wildcard(self, req):
        raise web.HTTPFound('/')

    async def api_catalog(self, req):
        """Endpoint que devuelve el catálogo completo para el bot de Netflix."""
        from .routes import MOVIES_THREAD_ID, SERIES_THREAD_ID

        if not chat_ids:
            return web.json_response([])

        chat = chat_ids[0]
        chat_id = chat['chat_id']
        chat_id_short = str(chat_id).replace('-100', '')
        items = []

        try:
            batch = await self.client.get_messages(
                entity=chat_id,
                limit=500,
            )
            batch = batch or []
            msgs = [m for m in batch if _has_media(m)]

            for m in msgs:
                # Determinar a qué tema pertenece el mensaje
                reply_to = getattr(m, 'reply_to', None)
                top_id = getattr(reply_to, 'reply_to_top_id', None) or getattr(reply_to, 'reply_to_msg_id', None)

                if top_id == MOVIES_THREAD_ID:
                    media_type = 'movie'
                    thread_id = MOVIES_THREAD_ID
                elif top_id == SERIES_THREAD_ID:
                    media_type = 'tv'
                    thread_id = SERIES_THREAD_ID
                else:
                    # Si no tiene reply_to es el primer mensaje del tema (el propio topic)
                    continue

                entry = dict(
                    file_id=m.id,
                    media=True,
                    insight=get_file_name(m),
                    mime_type=m.file.mime_type,
                    date=str(m.date),
                    size=m.file.size,
                    human_size=get_human_size(m.file.size),
                    url=f"/{chat['alias_id']}/{m.id}/view",
                    download=f"/{chat['alias_id']}/{m.id}/download",
                    thumbnail=f"/{chat['alias_id']}/{m.id}/thumbnail",
                )
                enriched = await enrich_entry(entry)
                tmdb = enriched.get('tmdb')
                if tmdb and tmdb.get('tmdb_id'):
                    items.append({
                        'tmdb_id': tmdb['tmdb_id'],
                        'media_type': media_type,
                        'telegram_link': f"https://t.me/c/{chat_id_short}/{thread_id}/{m.id}",
                        'title': tmdb.get('title'),
                        'poster': tmdb.get('poster'),
                        'year': tmdb.get('year'),
                        'rating': tmdb.get('rating'),
                        'overview': tmdb.get('overview'),
                        'genres': tmdb.get('genres', []),
                    })
        except Exception:
            log.debug("Error en api_catalog", exc_info=True)

        return web.json_response(items)

    @aiohttp_jinja2.template('home.html')
    async def home(self, req):
        if len(chat_ids) == 1:
            raise web.HTTPFound(f"{chat_ids[0]['alias_id']}")
        chats = []
        for chat in chat_ids:
            chats.append({
                'page_id': chat['alias_id'],
                'name': chat['title'],
                'url': req.rel_url.path + f"/{chat['alias_id']}"
            })
        return {'chats': chats, 'otg': enable_otg}

    @aiohttp_jinja2.template('otg.html')
    async def otg_view(self, req):
        if not enable_otg:
            raise web.HTTPFound('/')
        return_data = {}
        error = req.query.get('e')
        if error:
            return_data.update({'error': error})
        return return_data

    @aiohttp_jinja2.template('playlistCreator.html')
    async def playlist_creator(self, req):
        return_data = {}
        error = req.query.get('e')
        if error:
            return_data.update({'error': error})
        return return_data

    async def dynamic_view(self, req):
        if not enable_otg:
            raise web.HTTPFound('/')
        rel_url = req.rel_url
        include_private = otg_settings['include_private']
        include_group = otg_settings['include_group']
        include_channel = otg_settings['include_channel']
        post_data = await req.post()
        raw_id = post_data.get('id')
        if not raw_id:
            raise web.HTTPFound('/')
        raw_id.replace('@', '')
        try:
            chat = await self.client.get_entity(raw_id)
        except Exception as e:
            log.debug(e, exc_info=True)
            raise web.HTTPFound(rel_url.with_query({'e': f"No chat found with username {raw_id}"}))
        if isinstance(chat, User) and not include_private:
            raise web.HTTPFound(rel_url.with_query({'e': "Indexing private chats is not supported!!"}))
        elif isinstance(chat, Channel) and not include_channel:
            raise web.HTTPFound(rel_url.with_query({'e': "Indexing channels is not supported!!"}))
        elif isinstance(chat, Chat) and not include_group:
            raise web.HTTPFound(rel_url.with_query({'e': "Indexing group chats is not supported!!"}))
        log.debug(f"chat {chat} accessed!!")
        raise web.HTTPFound(f'/{chat.id}')

    @aiohttp_jinja2.template('index.html')
    async def index(self, req):
        # Ignorar peticiones de prefetch del navegador
        purpose = req.headers.get('Purpose', '') or req.headers.get('Sec-Purpose', '')
        if 'prefetch' in purpose.lower():
            raise web.HTTPNoContent()
        alias_id = req.match_info['chat']
        chat = [i for i in chat_ids if i['alias_id'] == alias_id]
        if not chat:
            if not enable_otg:
                raise web.HTTPFound('/')
            try:
                chat_id = int(alias_id)
                chat_ = await self.client.get_entity(chat_id)
                chat_name = chat_.title
            except:
                raise web.HTTPFound('/')
        else:
            chat = chat[0]
            chat_id = chat['chat_id']
            chat_name = chat['title']

        try:
            page = max(1, int(req.query.get('page', '1')))
        except:
            page = 1

        try:
            search_query = req.query.get('search', '')
        except:
            search_query = ''

        PAGE_SIZE = 20
        messages = []

        # Solo mostrar mensajes de los temas de películas y series
        from .routes import MOVIES_THREAD_ID, SERIES_THREAD_ID
        ALLOWED_THREADS = {MOVIES_THREAD_ID, SERIES_THREAD_ID}

        def _in_allowed_thread(m):
            reply_to = getattr(m, 'reply_to', None)
            if reply_to is None:
                return False
            top_id = getattr(reply_to, 'reply_to_top_id', None) or getattr(reply_to, 'reply_to_msg_id', None)
            return top_id in ALLOWED_THREADS

        try:
            if search_query:
                all_msgs = await self.client.get_messages(
                    entity=chat_id,
                    limit=500,
                    search=search_query,
                )
                all_msgs = all_msgs or []
                media_msgs = [m for m in all_msgs if _has_media(m) and _in_allowed_thread(m)]
                start = PAGE_SIZE * (page - 1)
                messages = media_msgs[start: start + PAGE_SIZE]
            else:
                batch = await self.client.get_messages(
                    entity=chat_id,
                    limit=PAGE_SIZE * 10,
                    add_offset=PAGE_SIZE * (page - 1),
                )
                batch = batch or []
                messages = [m for m in batch if _has_media(m) and _in_allowed_thread(m)][:PAGE_SIZE]
        except Exception:
            log.debug("failed to get messages", exc_info=True)
            messages = []

        log.debug(f"page={page} search='{search_query}' found={len(messages)} messages")
        log.error(f"REQUEST {req.method} {req.path} from={req.remote} ua={req.headers.get('User-Agent','?')[:80]} total={len(messages)}")
        for m in messages:
            reply_to = getattr(m, 'reply_to', None)
            top_id = getattr(reply_to, 'reply_to_top_id', None) or getattr(reply_to, 'reply_to_msg_id', None)
            log.error(f"MSG id={m.id} top_id={top_id}")

        raw_results = []
        for m in messages:
            raw_results.append(dict(
                file_id=m.id,
                media=True,
                thumbnail=f"/{alias_id}/{m.id}/thumbnail",
                mime_type=m.file.mime_type,
                insight=get_file_name(m),
                date=str(m.date),
                size=m.file.size,
                human_size=get_human_size(m.file.size),
                url=req.rel_url.path + f"/{m.id}/view",
                download=req.rel_url.path + f"/{m.id}/download",
            ))

        enriched = list(await asyncio.gather(*[enrich_entry(e) for e in raw_results]))

        # Deduplicar por file_id para evitar que el mismo vídeo aparezca varias veces
        seen_ids = set()
        deduped = []
        for e in enriched:
            fid = e.get('file_id')
            if fid not in seen_ids:
                seen_ids.add(fid)
                deduped.append(e)

        results = _group_results(deduped)

        all_genres = []
        for r in results:
            tmdb = r.get('tmdb')
            if tmdb:
                for g in tmdb.get('genres', []):
                    if g and g not in all_genres:
                        all_genres.append(g)
        all_genres.sort()

        prev_page = False
        next_page = False
        if page > 1:
            query = {'page': page - 1}
            if search_query:
                query['search'] = search_query
            prev_page = {'url': str(req.rel_url.with_query(query)), 'no': page - 1}

        if len(messages) == PAGE_SIZE:
            query = {'page': page + 1}
            if search_query:
                query['search'] = search_query
            next_page = {'url': str(req.rel_url.with_query(query)), 'no': page + 1}

        return {
            'item_list': results,
            'prev_page': prev_page,
            'cur_page': page,
            'next_page': next_page,
            'search': search_query,
            'name': chat_name,
            'logo': f"/{alias_id}/logo",
            'title': "Index of " + chat_name,
            'all_genres': all_genres,
        }

    @aiohttp_jinja2.template('info.html')
    async def info(self, req):
        file_id = int(req.match_info["id"])
        try:
            alias_id = req.match_info['chat']
        except:
            alias_id = chat_ids[0]['alias_id']
        chat = [i for i in chat_ids if i['alias_id'] == alias_id]
        if not chat:
            if not enable_otg:
                raise web.HTTPFound('/')
            try:
                chat_id = int(alias_id)
            except:
                raise web.HTTPFound('/')
        else:
            chat = chat[0]
            chat_id = chat['chat_id']
        try:
            message = await self.client.get_messages(entity=chat_id, ids=file_id)
        except:
            log.debug(f"Error in getting message {file_id} in {chat_id}", exc_info=True)
            message = None
        if not message or not isinstance(message, Message):
            return {'found': False, 'reason': "Entry you are looking for cannot be retrived!"}
        return_val = {}
        reply_btns = []
        if message.reply_markup:
            if isinstance(message.reply_markup, types.ReplyInlineMarkup):
                for button_row in message.reply_markup.rows:
                    btns = []
                    for button in button_row.buttons:
                        if isinstance(button, types.KeyboardButtonUrl):
                            btns.append({'url': button.url, 'text': button.text})
                    reply_btns.append(btns)
        if message.file and not isinstance(message.media, types.MessageMediaWebPage):
            file_name = get_file_name(message)
            file_size = message.file.size
            human_file_size = get_human_size(file_size)
            media = {'type': message.file.mime_type}
            if 'video/' in message.file.mime_type:
                media['video'] = True
            elif 'audio/' in message.file.mime_type:
                media['audio'] = True
            elif 'image/' in message.file.mime_type:
                media['image'] = True
            caption = message.raw_text if message.text else ''
            caption_html = Markup.escape(caption).__str__().replace('\n', '<br>')
            return_val = {
                'found': True,
                'name': file_name,
                'file_id': file_id,
                'size': file_size,
                'human_size': human_file_size,
                'media': media,
                'caption_html': caption_html,
                'caption': caption,
                'title': f"Download | {file_name} | {human_file_size}",
                'reply_btns': reply_btns,
                'thumbnail': f"/{alias_id}/{file_id}/thumbnail",
                'download_url': f"/{alias_id}/{file_id}/download",
                'page_id': alias_id,
            }
        elif message.message:
            text = message.raw_text
            text_html = Markup.escape(text).__str__().replace('\n', '<br>')
            return_val = {
                'found': True,
                'media': False,
                'text': text,
                'text_html': text_html,
                'reply_btns': reply_btns,
                'page_id': alias_id,
            }
        else:
            return_val = {'found': False, 'reason': "Some kind of entry that I cannot display"}
        return return_val

    async def logo(self, req):
        alias_id = req.match_info['chat']
        chat = [i for i in chat_ids if i['alias_id'] == alias_id]
        if not chat:
            if not enable_otg:
                return web.Response(status=403, text="403: Forbiden")
            try:
                chat_id = int(alias_id)
            except:
                return web.Response(status=403, text="403: Forbiden")
        else:
            chat = chat[0]
            chat_id = chat['chat_id']
        chat_name = "Image not available"
        try:
            photo = await self.client.get_profile_photos(chat_id)
        except:
            log.debug(f"Error in getting profile picture in {chat_id}", exc_info=True)
            photo = None
        if not photo:
            W, H = (160, 160)
            c = lambda: random.randint(0, 255)
            color = tuple([c() for i in range(3)])
            im = Image.new("RGB", (W, H), color)
            draw = ImageDraw.Draw(im)
            bbox = draw.textbbox((0, 0), chat_name)
            w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
            draw.text(((W - w) / 2, (H - h) / 2), chat_name, fill="white")
            temp = io.BytesIO()
            im.save(temp, "PNG")
            body = temp.getvalue()
        else:
            photo = photo[0]
            pos = -1 if req.query.get('big', None) else int(len(photo.sizes) / 2)
            size = self.client._get_thumb(photo.sizes, pos)
            if isinstance(size, (types.PhotoCachedSize, types.PhotoStrippedSize)):
                body = self.client._download_cached_photo_size(size, bytes)
            else:
                media = types.InputPhotoFileLocation(
                    id=photo.id,
                    access_hash=photo.access_hash,
                    file_reference=photo.file_reference,
                    thumb_size=size.type
                )
                body = self.client.iter_download(media)
        return web.Response(
            status=200, body=body,
            headers={"Content-Type": "image/jpeg", "Content-Disposition": 'inline; filename="logo.jpg"'}
        )

    async def download_get(self, req):
        return await self.handle_request(req)

    async def download_head(self, req):
        return await self.handle_request(req, head=True)

    async def thumbnail_get(self, req):
        file_id = int(req.match_info["id"])
        alias_id = req.match_info['chat']
        chat = [i for i in chat_ids if i['alias_id'] == alias_id]
        if not chat:
            if not enable_otg:
                return web.Response(status=403, text="403: Forbiden")
            try:
                chat_id = int(alias_id)
            except:
                return web.Response(status=403, text="403: Forbiden")
        else:
            chat = chat[0]
            chat_id = chat['chat_id']
        try:
            message = await self.client.get_messages(entity=chat_id, ids=file_id)
        except:
            message = None
        if not message or not message.file:
            return web.Response(status=410, text="410: Gone.")
        if message.document:
            media = message.document
            thumbnails = media.thumbs
            location = types.InputDocumentFileLocation
        else:
            media = message.photo
            thumbnails = media.sizes
            location = types.InputPhotoFileLocation
        if not thumbnails:
            c = lambda: random.randint(0, 255)
            color = tuple([c() for i in range(3)])
            im = Image.new("RGB", (160, 90), color)
            temp = io.BytesIO()
            im.save(temp, "PNG")
            body = temp.getvalue()
        else:
            thumb_pos = int(len(thumbnails) / 2)
            thumbnail = self.client._get_thumb(thumbnails, thumb_pos)
            if not thumbnail or isinstance(thumbnail, types.PhotoSizeEmpty):
                return web.Response(status=410, text="410: Gone.")
            if isinstance(thumbnail, (types.PhotoCachedSize, types.PhotoStrippedSize)):
                body = self.client._download_cached_photo_size(thumbnail, bytes)
            else:
                actual_file = location(
                    id=media.id, access_hash=media.access_hash,
                    file_reference=media.file_reference, thumb_size=thumbnail.type
                )
                body = self.client.iter_download(actual_file)
        return web.Response(
            status=200, body=body,
            headers={"Content-Type": "image/jpeg", "Content-Disposition": 'inline; filename="thumbnail.jpg"'}
        )

    async def handle_request(self, req, head=False):
        file_id = int(req.match_info["id"])
        try:
            alias_id = req.match_info['chat']
        except:
            alias_id = chat_ids[0]['alias_id']
        chat = [i for i in chat_ids if i['alias_id'] == alias_id]
        if not chat:
            if not enable_otg:
                return web.Response(status=403, text="403: Forbiden")
            try:
                chat_id = int(alias_id)
            except:
                return web.Response(status=403, text="403: Forbiden")
        else:
            chat = chat[0]
            chat_id = chat['chat_id']
        try:
            message = await self.client.get_messages(entity=chat_id, ids=file_id)
        except:
            message = None
        if not message or not message.file:
            return web.Response(status=410, text="410: Gone.")
        media = message.media
        size = message.file.size
        file_name = get_file_name(message)
        mime_type = message.file.mime_type
        try:
            offset = req.http_range.start or 0
            limit = req.http_range.stop if req.http_range.stop is not None else size
            limit = min(limit, size)
            if offset < 0 or limit < offset or offset >= size:
                raise ValueError("range not in acceptable format")
        except ValueError:
            return web.Response(status=416, text="416: Range Not Satisfiable",
                                headers={"Content-Range": f"bytes */{size}"})
        headers = {
            "Content-Type": mime_type,
            "Content-Range": f"bytes {offset}-{limit - 1}/{size}",
            "Content-Length": str(limit - offset),
            "Accept-Ranges": "bytes",
            "Content-Disposition": f'inline; filename="{file_name}"',
            "Access-Control-Allow-Origin": "*",
            "Cache-Control": "no-store",
        }
        if head:
            return web.Response(status=200, headers=headers)
        log.info(f"Serving file in {message.id} (chat {chat_id}) ; Range: {offset} - {limit}")
        response = web.StreamResponse(
            status=206 if req.http_range.start is not None else 200,
            headers=headers
        )
        await response.prepare(req)
        try:
            async for chunk in self.client.download(media, size, offset, limit):
                await response.write(chunk)
        except (ConnectionResetError, asyncio.CancelledError):
            log.debug(f"Connection closed while serving {file_id}")
        return response
