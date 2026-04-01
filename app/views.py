<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{{ title }}</title>
  <link href="https://fonts.googleapis.com/css2?family=Bebas+Neue&family=DM+Sans:wght@300;400;500;700&display=swap" rel="stylesheet">
  <style>
    :root {
      --red: #e50914; --red2: #b2070f; --dark: #080808;
      --sb-w: 70px; --sb-expanded: 220px;
      --card-w: 160px; --card-h: 240px;
      --radius: 8px; --gap: 8px;
    }
    * { margin:0; padding:0; box-sizing:border-box; }
    html { scroll-behavior:smooth; }
    body { background:var(--dark); color:#e5e5e5; font-family:'DM Sans',sans-serif; min-height:100vh; overflow-x:hidden; display:flex; }
    a { text-decoration:none; color:inherit; }

    /* ── SIDEBAR ── */
    .sidebar {
      position:fixed; top:0; left:0; bottom:0;
      width:var(--sb-w); z-index:500;
      background:#0d0d0d; border-right:1px solid #111;
      display:flex; flex-direction:column; overflow:hidden;
      transition:width .35s cubic-bezier(.4,0,.2,1);
      box-shadow:4px 0 24px rgba(0,0,0,.6);
    }
    .sidebar:hover { width:var(--sb-expanded); }

    .sb-logo {
      display:flex; align-items:center; gap:12px;
      padding:22px 18px 20px; border-bottom:1px solid #161616;
      flex-shrink:0; overflow:hidden; white-space:nowrap;
    }
    .sb-logo-mark {
      width:34px; height:34px; flex-shrink:0;
      background:var(--red); border-radius:8px;
      display:flex; align-items:center; justify-content:center;
      font-size:1.1rem; font-weight:900; color:#fff;
      font-family:'Bebas Neue',sans-serif; letter-spacing:-1px;
    }
    .sb-logo-text {
      font-family:'Bebas Neue',sans-serif; font-size:1.5rem;
      color:#fff; letter-spacing:2px; opacity:0; transition:opacity .2s .1s;
    }
    .sidebar:hover .sb-logo-text { opacity:1; }

    .sb-group { padding:10px 0; border-bottom:1px solid #111; }
    .sb-group-label {
      font-size:0.58rem; font-weight:700; color:#444; letter-spacing:2px;
      text-transform:uppercase; padding:4px 18px 6px;
      opacity:0; transition:opacity .2s; white-space:nowrap;
    }
    .sidebar:hover .sb-group-label { opacity:1; }

    .sb-item {
      display:flex; align-items:center; gap:14px;
      height:46px; padding:0 18px; cursor:pointer; color:#666;
      transition:color .2s, background .2s;
      white-space:nowrap; overflow:hidden;
      border-left:3px solid transparent; text-decoration:none;
    }
    .sb-item:hover { color:#fff; background:rgba(255,255,255,.05); }
    .sb-item.active { color:#fff; border-left-color:var(--red); background:rgba(229,9,20,.1); }

    .sb-icon { width:22px; flex-shrink:0; display:flex; align-items:center; justify-content:center; font-size:1.15rem; }
    .sb-icon svg { width:18px; height:18px; stroke:currentColor; fill:none; stroke-width:2; stroke-linecap:round; stroke-linejoin:round; }
    .sb-label { font-size:0.88rem; font-weight:500; opacity:0; transition:opacity .15s; }
    .sidebar:hover .sb-label { opacity:1; }

    .sb-genres { padding:8px 0; flex:1; overflow-y:auto; overflow-x:hidden; scrollbar-width:none; }
    .sb-genres::-webkit-scrollbar { display:none; }

    .sb-bottom {
      padding:14px 18px; border-top:1px solid #111; flex-shrink:0;
      display:flex; align-items:center; gap:12px; overflow:hidden; white-space:nowrap;
    }
    .sb-avatar {
      width:32px; height:32px; flex-shrink:0;
      background:linear-gradient(135deg,var(--red),#ff6b6b);
      border-radius:50%; display:flex; align-items:center; justify-content:center;
      font-size:0.85rem; font-weight:700; color:#fff;
    }
    .sb-user-info { opacity:0; transition:opacity .2s; }
    .sidebar:hover .sb-user-info { opacity:1; }
    .sb-user-name { font-size:0.82rem; font-weight:600; color:#ddd; }
    .sb-user-sub { font-size:0.7rem; color:#555; }

    /* ── CONTENT ── */
    .content { margin-left:var(--sb-w); flex:1; min-width:0; }

    .topbar {
      position:fixed; top:0; left:var(--sb-w); right:0; z-index:300; height:64px;
      display:flex; align-items:center; gap:16px; padding:0 32px;
      background:linear-gradient(180deg,rgba(8,8,8,.98) 60%,transparent 100%);
      backdrop-filter:blur(6px);
    }
    .topbar-name { color:#555; font-size:0.85rem; font-style:italic; }
    .spacer { flex:1; }
    .search-wrap { position:relative; }
    .search-wrap svg { position:absolute; left:11px; top:50%; transform:translateY(-50%); pointer-events:none; color:#555; width:14px; height:14px; stroke:currentColor; fill:none; stroke-width:2.5; stroke-linecap:round; }
    .search-input {
      background:rgba(255,255,255,.07); border:1px solid rgba(255,255,255,.1);
      border-radius:24px; padding:9px 16px 9px 36px;
      color:#fff; font-size:0.85rem; width:210px; outline:none;
      transition:all .3s; font-family:'DM Sans',sans-serif;
    }
    .search-input:focus { background:rgba(255,255,255,.13); border-color:rgba(255,255,255,.28); width:260px; }
    .search-input::placeholder { color:#444; }

    /* ── HERO ── */
    .hero {
      position:relative; width:100%; height:88vh; min-height:500px;
      display:flex; align-items:flex-end; overflow:hidden;
    }
    .hero-bg {
      position:absolute; inset:0; background-size:cover; background-position:center top;
      transform:scale(1.04); transition:transform 9s ease;
    }
    .hero:hover .hero-bg { transform:scale(1); }
    .hero-vignette {
      position:absolute; inset:0;
      background:linear-gradient(0deg,rgba(8,8,8,1) 0%,rgba(8,8,8,.72) 28%,rgba(8,8,8,.1) 55%,transparent 100%),
                linear-gradient(90deg,rgba(8,8,8,.9) 0%,rgba(8,8,8,.3) 55%,transparent 100%);
    }
    .hero-content { position:relative; z-index:2; padding:0 52px 60px; max-width:560px; }
    .hero-badge {
      display:inline-block; background:var(--red); color:#fff;
      font-size:0.6rem; font-weight:800; padding:3px 10px; border-radius:3px;
      letter-spacing:1.5px; text-transform:uppercase; margin-bottom:12px;
    }
    .hero-title {
      font-family:'Bebas Neue',sans-serif;
      font-size:clamp(2.8rem,5.5vw,5rem); line-height:.95;
      letter-spacing:1px; margin-bottom:14px;
      text-shadow:0 2px 40px rgba(0,0,0,.9);
    }
    .hero-meta { display:flex; gap:14px; align-items:center; font-size:0.87rem; color:#bbb; margin-bottom:12px; flex-wrap:wrap; }
    .hero-rating { color:#f5c518; font-weight:800; }
    .hero-overview { font-size:0.92rem; color:#ccc; line-height:1.65; margin-bottom:14px; display:-webkit-box; -webkit-line-clamp:3; -webkit-box-orient:vertical; overflow:hidden; }
    .hero-genres { display:flex; gap:6px; flex-wrap:wrap; margin-bottom:22px; }
    .hero-genre { background:rgba(255,255,255,.09); border:1px solid rgba(255,255,255,.18); color:#ccc; font-size:0.72rem; padding:4px 12px; border-radius:4px; }
    .hero-actions { display:flex; gap:12px; flex-wrap:wrap; }
    .btn-play { display:inline-flex; align-items:center; gap:8px; background:#fff; color:#000; padding:13px 34px; border-radius:6px; font-size:1rem; font-weight:800; transition:background .2s; }
    .btn-play:hover { background:#e0e0e0; }
    .btn-info { display:inline-flex; align-items:center; gap:8px; background:rgba(120,120,120,.5); color:#fff; padding:13px 26px; border-radius:6px; font-size:1rem; font-weight:700; transition:background .2s; backdrop-filter:blur(4px); }
    .btn-info:hover { background:rgba(120,120,120,.8); }

    /* ── MAIN ── */
    .main { padding-top:24px; }

    /* ── ROW SECTION ── */
    .row-section { padding:0 0 40px; }
    .row-header { display:flex; align-items:center; gap:10px; padding:0 32px 14px; flex-wrap:wrap; }
    .row-title { font-family:'Bebas Neue',sans-serif; font-size:1.45rem; letter-spacing:1px; color:#fff; }
    .row-count { background:rgba(229,9,20,.2); border:1px solid rgba(229,9,20,.4); color:#ff6b6b; font-size:0.65rem; font-weight:800; padding:2px 8px; border-radius:10px; }
    .row-line { flex:1; height:1px; background:linear-gradient(90deg,#2a2a2a,transparent); }
    .btn-ver-mas {
      display:inline-flex; align-items:center; gap:6px;
      background:transparent; border:1px solid #333; color:#999;
      padding:6px 16px; border-radius:20px; font-size:0.78rem; font-weight:600;
      cursor:pointer; transition:all .2s; white-space:nowrap;
      font-family:'DM Sans',sans-serif;
    }
    .btn-ver-mas:hover { border-color:var(--red); color:#fff; background:rgba(229,9,20,.12); }

    .cards-grid {
      display:flex; flex-wrap:wrap; gap:var(--gap);
      padding:0 32px;
    }

    /* ── CARD ── */
    .card {
      flex:0 0 var(--card-w); width:var(--card-w); height:var(--card-h);
      position:relative; border-radius:var(--radius);
      cursor:pointer; overflow:visible;
      transition:transform .32s cubic-bezier(.4,0,.2,1), z-index 0s .32s;
      z-index:1;
    }
    .card:hover {
      transform:scale(1.12) translateY(-6px); z-index:50;
      transition:transform .32s cubic-bezier(.4,0,.2,1), z-index 0s;
    }
    .card-inner {
      width:var(--card-w); height:var(--card-h);
      border-radius:var(--radius); overflow:hidden; position:relative;
      box-shadow:0 4px 24px rgba(0,0,0,.55); transition:box-shadow .32s;
    }
    .card:hover .card-inner { box-shadow:0 20px 60px rgba(0,0,0,.9); }
    .card-poster {
      display:block; width:100%; height:100%;
      object-fit:cover; object-position:center top;
      pointer-events:none; transition:filter .32s;
    }
    .card:hover .card-poster { filter:brightness(.38); }
    .card-no-poster {
      width:100%; height:100%;
      display:flex; flex-direction:column; align-items:center; justify-content:center;
      padding:16px; text-align:center;
      background:linear-gradient(160deg,#1a1a2e,#16213e,#0f3460);
    }
    .card-no-poster .np-icon { font-size:2.4rem; margin-bottom:10px; }
    .card-no-poster .np-title { font-size:0.72rem; font-weight:600; color:#ccc; line-height:1.3; }

    .card-badge {
      position:absolute; top:8px; left:8px; z-index:2;
      background:var(--red); color:#fff;
      font-size:0.52rem; font-weight:900; padding:2px 7px; border-radius:3px;
      letter-spacing:1px; text-transform:uppercase; pointer-events:none;
    }
    .card-star {
      position:absolute; top:8px; right:8px; z-index:2;
      background:rgba(0,0,0,.75); color:#f5c518;
      font-size:0.65rem; font-weight:800; padding:2px 7px; border-radius:3px;
      pointer-events:none;
    }
    .card-hover {
      position:absolute; inset:0; z-index:3;
      padding:12px 10px 10px;
      display:flex; flex-direction:column; justify-content:flex-end;
      opacity:0; transition:opacity .28s; pointer-events:none;
      background:linear-gradient(0deg,rgba(0,0,0,.97) 0%,rgba(0,0,0,.5) 55%,transparent 100%);
    }
    .card:hover .card-hover { opacity:1; pointer-events:auto; }
    .ch-title { font-size:0.8rem; font-weight:800; color:#fff; margin-bottom:3px; line-height:1.2; pointer-events:none; }
    .ch-meta { font-size:0.63rem; color:#999; margin-bottom:6px; pointer-events:none; }
    .ch-genres { display:flex; gap:3px; flex-wrap:wrap; margin-bottom:8px; pointer-events:none; }
    .ch-genre { background:rgba(229,9,20,.22); border:1px solid rgba(229,9,20,.38); color:#ff8888; font-size:0.52rem; padding:1px 5px; border-radius:2px; }
    .ch-play {
      width:100%; background:var(--red); color:#fff; border:none;
      padding:7px 0; border-radius:5px; font-size:0.75rem; font-weight:700;
      cursor:pointer; text-align:center; transition:background .2s; font-family:'DM Sans',sans-serif;
    }
    .ch-play:hover { background:var(--red2); }

    /* ── GENRE TABS ── */
    .genre-tabs { display:flex; gap:8px; overflow-x:auto; padding:0 32px 16px; scrollbar-width:none; }
    .genre-tabs::-webkit-scrollbar { display:none; }
    .genre-tab {
      flex:0 0 auto; background:#161616; border:1px solid #222;
      color:#888; padding:7px 18px; border-radius:20px;
      font-size:0.8rem; font-weight:500; cursor:pointer;
      transition:all .2s; white-space:nowrap; font-family:'DM Sans',sans-serif;
    }
    .genre-tab:hover { background:#222; color:#fff; }
    .genre-tab.active { background:var(--red); border-color:var(--red); color:#fff; }

    /* ── FULLSCREEN MODAL ── */
    .modal-overlay {
      display:none; position:fixed; inset:0; z-index:600;
      background:rgba(8,8,8,.97); backdrop-filter:blur(8px);
      overflow-y:auto;
    }
    .modal-overlay.open { display:block; }

    .modal {
      min-height:100vh; padding:24px 32px 48px;
      max-width:1600px; margin:0 auto;
    }
    .modal-topbar {
      display:flex; align-items:center; gap:14px;
      padding:16px 0 24px;
      position:sticky; top:0; z-index:10;
      background:rgba(8,8,8,.97); backdrop-filter:blur(8px);
      border-bottom:1px solid #1a1a1a; margin-bottom:28px;
    }
    .modal-back {
      background:#1a1a1a; border:1px solid #2a2a2a; color:#aaa;
      width:40px; height:40px; border-radius:50%; font-size:1.2rem;
      cursor:pointer; display:flex; align-items:center; justify-content:center;
      transition:all .2s; flex-shrink:0;
    }
    .modal-back:hover { background:var(--red); border-color:var(--red); color:#fff; }
    .modal-title { font-family:'Bebas Neue',sans-serif; font-size:2rem; color:#fff; letter-spacing:1px; }
    .modal-subtitle { color:#555; font-size:0.85rem; margin-left:auto; white-space:nowrap; }

    .modal-search-wrap { position:relative; margin-left:16px; }
    .modal-search-wrap svg { position:absolute; left:11px; top:50%; transform:translateY(-50%); pointer-events:none; color:#555; width:14px; height:14px; stroke:currentColor; fill:none; stroke-width:2.5; stroke-linecap:round; }
    .modal-search {
      background:rgba(255,255,255,.07); border:1px solid rgba(255,255,255,.1);
      border-radius:24px; padding:8px 16px 8px 34px;
      color:#fff; font-size:0.82rem; width:200px; outline:none;
      transition:all .3s; font-family:'DM Sans',sans-serif;
    }
    .modal-search:focus { background:rgba(255,255,255,.13); border-color:rgba(255,255,255,.28); width:240px; }
    .modal-search::placeholder { color:#444; }

    .modal-grid {
      display:grid;
      grid-template-columns:repeat(auto-fill, minmax(var(--card-w), 1fr));
      gap:14px;
    }
    .modal-grid .card { flex:unset; width:100%; height:var(--card-h); }
    .modal-grid .card-inner { width:100%; height:100%; }
    .modal-grid .card.hidden { display:none; }

    .no-results {
      display:none; grid-column:1/-1;
      text-align:center; padding:60px 20px;
      color:#444; font-size:0.95rem;
    }
    .no-results.show { display:block; }

    /* ── FOOTER ── */
    footer { text-align:center; padding:28px; color:#2a2a2a; font-size:0.75rem; border-top:1px solid #111; }
    footer a { color:#333; }
    footer a:hover { color:var(--red); }

    /* ── RESPONSIVE ── */
    @media(max-width:900px){
      :root { --card-w:140px; --card-h:210px; }
    }
    @media(max-width:768px){
      :root { --sb-w:0px; --card-w:120px; --card-h:180px; --gap:6px; }
      .sidebar { display:none; }
      .content { margin-left:0; }
      .topbar { left:0; padding:0 16px; }
      .hero-content { padding:0 18px 40px; }
      .hero-title { font-size:2rem; }
      .hero-overview { -webkit-line-clamp:2; }
      .row-header { padding:0 16px 10px; }
      .cards-grid { padding:0 16px; }
      .genre-tabs { padding:0 16px 12px; }
      .btn-play, .btn-info { padding:10px 20px; font-size:0.9rem; }
      .modal { padding:16px 16px 40px; }
      .modal-topbar { padding:12px 0 16px; margin-bottom:20px; flex-wrap:wrap; }
      .modal-title { font-size:1.5rem; }
      .modal-search { width:160px; }
      .modal-search:focus { width:160px; }
    }
    @media(max-width:480px){
      :root { --card-w:100px; --card-h:150px; }
      .hero { height:70vh; }
      .modal-grid { gap:8px; }
      .modal-search-wrap { display:none; }
    }
  </style>
</head>
<body>

<!-- ════════════ SIDEBAR ════════════ -->
<nav class="sidebar">
  <div class="sb-logo">
    <div class="sb-logo-mark">TG</div>
    <span class="sb-logo-text">TGINDEX</span>
  </div>
  <div class="sb-group">
    <div class="sb-group-label">Menú</div>
    <a class="sb-item active" href="/">
      <span class="sb-icon"><svg viewBox="0 0 24 24"><path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/></svg></span>
      <span class="sb-label">Inicio</span>
    </a>
    <a class="sb-item" href="/otg">
      <span class="sb-icon"><svg viewBox="0 0 24 24"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg></span>
      <span class="sb-label">OTG Indexing</span>
    </a>
    <a class="sb-item" href="/pc">
      <span class="sb-icon"><svg viewBox="0 0 24 24"><path d="M9 18V5l12-2v13"/><circle cx="6" cy="18" r="3"/><circle cx="18" cy="16" r="3"/></svg></span>
      <span class="sb-label">Playlist</span>
    </a>
  </div>
  <div class="sb-group sb-genres" id="sbGenres">
    <div class="sb-group-label">Géneros</div>
  </div>
  <div class="sb-bottom">
    <div class="sb-avatar">U</div>
    <div class="sb-user-info">
      <div class="sb-user-name">{{ name }}</div>
      <div class="sb-user-sub">TgIndex Pro</div>
    </div>
  </div>
</nav>

<!-- ════════════ MAIN CONTENT ════════════ -->
<div class="content">
  <header class="topbar" id="topbar">
    <span class="topbar-name">{{ name }}</span>
    <div class="spacer"></div>
    <div class="search-wrap">
      <svg viewBox="0 0 24 24"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
      <form method="GET">
        <input class="search-input" type="text" name="search" value="{{ search or '' }}" placeholder="Buscar título...">
      </form>
    </div>
  </header>

  {% set media_items = item_list | selectattr('media') | list %}

  {% if media_items %}

    {# ── Clasificación de items ── #}
    {% set movies      = [] %}
    {% set series_list = [] %}
    {% set top_rated   = [] %}
    {% set newest      = [] %}
    {% set genre_map   = {} %}
    {% set all_genres  = [] %}

    {% for item in media_items %}
      {% set tmdb = item.tmdb if item.get('tmdb') else None %}
      {% if tmdb %}
        {% if tmdb.is_series %}
          {% if series_list.append(item) %}{% endif %}
        {% else %}
          {% if movies.append(item) %}{% endif %}
        {% endif %}
        {% if tmdb.rating and tmdb.rating >= 7.0 %}
          {% if top_rated.append(item) %}{% endif %}
        {% endif %}
        {% if tmdb.year and tmdb.year >= '2024' %}
          {% if newest.append(item) %}{% endif %}
        {% endif %}
        {% for g in tmdb.genres %}
          {% if g not in genre_map %}
            {% if genre_map.update({g:[]}) %}{% endif %}
            {% if all_genres.append(g) %}{% endif %}
          {% endif %}
          {% if genre_map[g].append(item) %}{% endif %}
        {% endfor %}
      {% else %}
        {% if movies.append(item) %}{% endif %}
      {% endif %}
    {% endfor %}

    {# ── HERO ── #}
    {% set hero = namespace(item=None) %}
    {% for item in media_items %}
      {% if not hero.item and item.get('tmdb') and item.tmdb.backdrop %}
        {% set hero.item = item %}
      {% endif %}
    {% endfor %}

    {% if hero.item %}
      {% set hi = hero.item %}
      {% set ht = hi.tmdb %}
      <div class="hero">
        <div class="hero-bg" style="background-image:url('{{ ht.backdrop }}')"></div>
        <div class="hero-vignette"></div>
        <div class="hero-content">
          <span class="hero-badge">{{ 'Serie' if ht.is_series else 'Película' }}</span>
          <h1 class="hero-title">{{ ht.title }}</h1>
          <div class="hero-meta">
            {% if ht.year %}<span>{{ ht.year }}</span>{% endif %}
            {% if ht.rating > 0 %}<span class="hero-rating">⭐ {{ ht.rating }}</span>{% endif %}
            {% if hi.human_size %}<span>{{ hi.human_size }}</span>{% endif %}
          </div>
          {% if ht.overview %}<p class="hero-overview">{{ ht.overview }}</p>{% endif %}
          {% if ht.genres %}
            <div class="hero-genres">
              {% for g in ht.genres[:4] %}<span class="hero-genre">{{ g }}</span>{% endfor %}
            </div>
          {% endif %}
          <div class="hero-actions">
            <a class="btn-play" href="{{ hi.url }}">▶ Ver ahora</a>
            <a class="btn-info" href="{{ hi.url }}">ℹ Más info</a>
          </div>
        </div>
      </div>
    {% endif %}

    {# ══════════ CARD MACRO ══════════ #}
    {% macro card(item) %}
      {% set t = item.tmdb if item.get('tmdb') else None %}
      <a href="{{ item.url }}" class="card" data-title="{{ (t.title if t else item.insight) | lower }}">
        <div class="card-inner">
          {% if t and t.poster %}
            <img class="card-poster" src="{{ t.poster }}" alt="{{ t.title }}" loading="lazy">
          {% else %}
            <div class="card-no-poster">
              <div class="np-icon">{{ '📺' if (t and t.is_series) else '🎬' }}</div>
              <div class="np-title">{{ item.insight }}</div>
            </div>
          {% endif %}
          <span class="card-badge">{{ 'Serie' if (t and t.is_series) else 'Pel' }}</span>
          {% if t and t.rating > 0 %}<span class="card-star">★ {{ t.rating }}</span>{% endif %}
          <div class="card-hover">
            <div class="ch-title">{{ t.title if t else item.insight }}</div>
            <div class="ch-meta">{{ t.year if t else '' }}{% if t and t.rating > 0 %} · ⭐ {{ t.rating }}{% endif %}</div>
            {% if t and t.genres %}
              <div class="ch-genres">{% for g in t.genres[:2] %}<span class="ch-genre">{{ g }}</span>{% endfor %}</div>
            {% endif %}
            <span class="ch-play" onclick="event.preventDefault();event.stopPropagation();window.location=this.closest('a').href">▶ Ver</span>
          </div>
        </div>
      </a>
    {% endmacro %}

    {# ══════════ FULLSCREEN MODAL MACRO ══════════ #}
    {% macro fullmodal(id, title, items) %}
      <div class="modal-overlay" id="{{ id }}">
        <div class="modal">
          <div class="modal-topbar">
            <button class="modal-back" onclick="closeModal('{{ id }}')">←</button>
            <div class="modal-title">{{ title }}</div>
            <span class="modal-subtitle">{{ items | length }} títulos</span>
            <div class="modal-search-wrap">
              <svg viewBox="0 0 24 24"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
              <input class="modal-search" type="text" placeholder="Filtrar..." oninput="filterModal('{{ id }}', this.value)">
            </div>
          </div>
          <div class="modal-grid" id="{{ id }}-grid">
            {# ✅ FIX: eliminado [:15] — se muestran TODOS los items en el modal #}
            {% for item in items %}{{ card(item) }}{% endfor %}
            <div class="no-results" id="{{ id }}-nores">No se encontraron resultados</div>
          </div>
        </div>
      </div>
    {% endmacro %}

    <div class="main">

      {# ── PELÍCULAS ── #}
      {% if movies %}
      <div class="row-section">
        <div class="row-header">
          <h2 class="row-title">🎬 Películas</h2>
          <span class="row-count">{{ movies | length }}</span>
          <div class="row-line"></div>
          {# ✅ FIX: el botón "Ver todas" aparece si hay más de 20, antes era > 15 #}
          {% if movies | length > 20 %}
          <button class="btn-ver-mas" onclick="openModal('modal-movies')">Ver todas ({{ movies | length }}) →</button>
          {% endif %}
        </div>
        {# ✅ FIX: se muestran hasta 20 en la fila principal (era [:15]) #}
        <div class="cards-grid">
          {% for item in movies[:20] %}{{ card(item) }}{% endfor %}
        </div>
      </div>
      {% endif %}

      {# ── SERIES ── #}
      {% if series_list %}
      <div class="row-section">
        <div class="row-header">
          <h2 class="row-title">📺 Series</h2>
          <span class="row-count">{{ series_list | length }}</span>
          <div class="row-line"></div>
          {% if series_list | length > 20 %}
          <button class="btn-ver-mas" onclick="openModal('modal-series')">Ver todas ({{ series_list | length }}) →</button>
          {% endif %}
        </div>
        {# ✅ FIX: se muestran hasta 20 en la fila principal (era [:15]) #}
        <div class="cards-grid">
          {% for item in series_list[:20] %}{{ card(item) }}{% endfor %}
        </div>
      </div>
      {% endif %}

      {# ── MEJOR VALORADAS ── #}
      {% if top_rated %}
      <div class="row-section">
        <div class="row-header">
          <h2 class="row-title">⭐ Mejor valoradas</h2>
          <span class="row-count">{{ top_rated | length }}</span>
          <div class="row-line"></div>
          {% if top_rated | length > 20 %}
          <button class="btn-ver-mas" onclick="openModal('modal-top')">Ver todas ({{ top_rated | length }}) →</button>
          {% endif %}
        </div>
        {# ✅ FIX: se muestran hasta 20 en la fila principal (era [:15]) #}
        <div class="cards-grid">
          {% for item in top_rated[:20] %}{{ card(item) }}{% endfor %}
        </div>
      </div>
      {% endif %}

      {# ── LO MÁS NUEVO ── #}
      {% if newest %}
      <div class="row-section">
        <div class="row-header">
          <h2 class="row-title">🆕 Lo más nuevo</h2>
          <span class="row-count">{{ newest | length }}</span>
          <div class="row-line"></div>
          {% if newest | length > 20 %}
          <button class="btn-ver-mas" onclick="openModal('modal-newest')">Ver todas ({{ newest | length }}) →</button>
          {% endif %}
        </div>
        {# ✅ FIX: se muestran hasta 20 en la fila principal (era [:15]) #}
        <div class="cards-grid">
          {% for item in newest[:20] %}{{ card(item) }}{% endfor %}
        </div>
      </div>
      {% endif %}

      {# ── POR GÉNERO ── #}
      {% if genre_map %}
      <div class="row-section">
        <div class="row-header">
          <h2 class="row-title">🎭 Por género</h2>
          <div class="row-line"></div>
        </div>
        <div class="genre-tabs">
          {% for genre in genre_map.keys() %}
          <button class="genre-tab{% if loop.first %} active{% endif %}" data-genre="{{ genre }}">{{ genre }}</button>
          {% endfor %}
        </div>
        {% for genre, items in genre_map.items() %}
        <div class="genre-panel" data-genre="{{ genre }}" {% if not loop.first %}style="display:none"{% endif %}>
          <div class="row-header" style="padding-top:8px;">
            <span style="color:#555;font-size:0.85rem;">{{ items | length }} títulos</span>
            <div class="row-line"></div>
            {% if items | length > 20 %}
            <button class="btn-ver-mas" onclick="openModal('modal-genre-{{ genre | replace(' ','-') | lower }}')">Ver todas ({{ items | length }}) →</button>
            {% endif %}
          </div>
          {# ✅ FIX: se muestran hasta 20 por género en la fila principal (era [:15]) #}
          <div class="cards-grid">
            {% for item in items[:20] %}{{ card(item) }}{% endfor %}
          </div>
        </div>
        {% endfor %}
      </div>
      {% endif %}

    </div><!-- /.main -->

    {# ══════════ MODALES FULLSCREEN ══════════ #}
    {{ fullmodal('modal-movies',  '🎬 Todas las películas', movies) }}
    {{ fullmodal('modal-series',  '📺 Todas las series',    series_list) }}
    {{ fullmodal('modal-top',     '⭐ Mejor valoradas',     top_rated) }}
    {{ fullmodal('modal-newest',  '🆕 Lo más nuevo',        newest) }}
    {% for genre, items in genre_map.items() %}
      {{ fullmodal('modal-genre-' ~ (genre | replace(' ','-') | lower), '🎭 ' ~ genre, items) }}
    {% endfor %}

  {% else %}
    <div style="display:flex;flex-direction:column;align-items:center;justify-content:center;height:80vh;color:#444;gap:16px;">
      <div style="font-size:5rem;">🎬</div>
      <p style="font-size:1.1rem;">No hay contenido disponible</p>
    </div>
  {% endif %}

  <footer><a href="https://github.com/odysseusmax" target="_blank">@odysseusmax</a></footer>
</div>

<script>
  /* ── Genre tabs ── */
  document.querySelectorAll('.genre-tab').forEach(tab => {
    tab.addEventListener('click', () => {
      const g = tab.dataset.genre;
      document.querySelectorAll('.genre-tab').forEach(t => t.classList.remove('active'));
      tab.classList.add('active');
      document.querySelectorAll('.genre-panel').forEach(p => {
        p.style.display = p.dataset.genre === g ? '' : 'none';
      });
    });
  });

  /* ── Modals ── */
  function openModal(id) {
    const m = document.getElementById(id);
    if (!m) return;
    const inp = m.querySelector('.modal-search');
    if (inp) { inp.value = ''; filterModal(id, ''); }
    m.classList.add('open');
    m.scrollTop = 0;
    document.body.style.overflow = 'hidden';
  }

  function closeModal(id) {
    const m = document.getElementById(id);
    if (!m) return;
    m.classList.remove('open');
    document.body.style.overflow = '';
  }

  /* Cerrar con Escape */
  document.addEventListener('keydown', e => {
    if (e.key === 'Escape') {
      document.querySelectorAll('.modal-overlay.open').forEach(m => closeModal(m.id));
    }
  });

  /* Cerrar al hacer click en el fondo del overlay */
  document.querySelectorAll('.modal-overlay').forEach(overlay => {
    overlay.addEventListener('click', e => {
      if (e.target === overlay) closeModal(overlay.id);
    });
  });

  /* ── Filtro en modal ── */
  function filterModal(id, query) {
    const grid = document.getElementById(id + '-grid');
    const nores = document.getElementById(id + '-nores');
    if (!grid) return;
    const q = query.toLowerCase().trim();
    let visible = 0;
    grid.querySelectorAll('.card').forEach(card => {
      const title = card.dataset.title || '';
      const match = !q || title.includes(q);
      card.classList.toggle('hidden', !match);
      if (match) visible++;
    });
    if (nores) nores.classList.toggle('show', visible === 0);
  }

  /* ── Sidebar géneros ── */
  (function(){
    const genres = [{% for g in all_genres %}'{{ g }}',{% endfor %}];
    const container = document.getElementById('sbGenres');
    genres.forEach(g => {
      const a = document.createElement('a');
      a.className = 'sb-item';
      a.href = '#';
      a.innerHTML = `<span class="sb-icon"><svg viewBox="0 0 24 24" style="width:16px;height:16px;stroke:currentColor;fill:none;stroke-width:2"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/></svg></span><span class="sb-label">${g}</span>`;
      a.addEventListener('click', e => {
        e.preventDefault();
        const tab = [...document.querySelectorAll('.genre-tab')].find(t => t.dataset.genre === g);
        if (tab) {
          tab.click();
          tab.closest('.row-section')?.scrollIntoView({ behavior: 'smooth' });
        }
      });
      container.appendChild(a);
    });
  })();

  /* ── Sticky topbar ── */
  window.addEventListener('scroll', () => {
    const h = document.getElementById('topbar');
    if (h) h.style.background = window.scrollY > 60 ? 'rgba(8,8,8,.98)' : '';
  });
</script>

</body>
</html>
