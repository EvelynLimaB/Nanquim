#!/usr/bin/env python3
"""
Nanquim — Atualizador automático do catálogo da comunidade (Krita-Artists).

Lê os tópicos públicos da categoria "Brushes and Bundles" do Krita-Artists
via API JSON do Discourse, extrai anexos diretos (.bundle, .kpp, .sut, .zip),
classifica nas categorias do Nanquim e grava `catalogo-comunidade.json` na raiz.

- Não precisa de bibliotecas externas (apenas biblioteca padrão do Python 3).
- Preserva itens manuais marcados com `"manual": true` no JSON atual ou no
  arquivo opcional `catalogo-extras.json`.
"""

from __future__ import annotations

import argparse
import datetime as dt
import html
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

BASE_URL = "https://krita-artists.org"
CATEGORY_URL = f"{BASE_URL}/c/resources/brushes-and-bundles/32.json"
USER_AGENT = "NanquimCatalogBot/1.0 (+https://github.com/isaiasdaniel290308-bot/Nanquim)"

VALID_EXTS = (".bundle", ".kpp", ".sut", ".zip")
EXT_PRIORITY = {".bundle": 0, ".kpp": 1, ".sut": 2, ".zip": 3}

# Links de portais rápidos mantidos no final do catálogo
PORTAL_ITEMS: list[dict[str, Any]] = [
    {
        "id": "portal-krita-artists-brushes",
        "name": "Krita-Artists · Todos os Pincéis e Pacotes",
        "author": "Comunidade Krita",
        "category": "Portais",
        "format": "Portal",
        "license": "Livre / CC",
        "description": "Acervo oficial da comunidade com pacotes .bundle e .kpp. Copie qualquer link direto e cole abaixo para instalar.",
        "tags": ["bundle", "kpp", "comunidade", "pincéis"],
        "download_url": "",
        "page_url": "https://krita-artists.org/c/resources/brushes-and-bundles/32",
    },
    {
        "id": "portal-krita-artists-screentones",
        "name": "Krita-Artists · Retículas e Padrões",
        "author": "Comunidade Krita",
        "category": "Portais",
        "format": "Portal",
        "license": "Livre / CC",
        "description": "Retículas de mangá, hachuras e texturas de papel postadas pela comunidade.",
        "tags": ["retícula", "screentone", "hachura", "padrões"],
        "download_url": "",
        "page_url": "https://krita-artists.org/search?q=screentone%20%23resources",
    },
    {
        "id": "portal-krita-docs-resources",
        "name": "Página Oficial de Recursos do Krita",
        "author": "KDE / Krita",
        "category": "Portais",
        "format": "Portal",
        "license": "GPL / CC0",
        "description": "Lista curada pela equipe do Krita com pacotes clássicos de pintura, tinta e quadrinhos.",
        "tags": ["oficial", "kde", "bundle", "pintura"],
        "download_url": "",
        "page_url": "https://docs.krita.org/en/resources_page.html",
    },
]


def fetch_json(url: str, retries: int = 3, delay: float = 0.5) -> dict[str, Any] | None:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "application/json",
        },
    )
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(req, timeout=25) as resp:
                raw = resp.read().decode("utf-8", errors="replace")
                return json.loads(raw)
        except urllib.error.HTTPError as e:
            if e.code == 429:
                wait = max(3.0, delay * (attempt + 2) * 3)
                print(f"  [429] Limite de taxa em {url}, aguardando {wait:.1f}s…", file=sys.stderr)
                time.sleep(wait)
                continue
            if 500 <= e.code < 600:
                time.sleep(2.0 * (attempt + 1))
                continue
            print(f"  [HTTP {e.code}] Falha em {url}", file=sys.stderr)
            return None
        except Exception as e:
            print(f"  [Erro] {url}: {e}", file=sys.stderr)
            time.sleep(1.5 * (attempt + 1))
    return None


def clean_description(cooked_html: str, max_len: int = 190) -> str:
    if not cooked_html:
        return ""
    # Remove blocos de citação, scripts, estilos e legendas de imagem do Discourse
    text = re.sub(r"<aside\b[^>]*>.*?</aside>", " ", cooked_html, flags=re.I | re.S)
    text = re.sub(r"<blockquote\b[^>]*>.*?</blockquote>", " ", text, flags=re.I | re.S)
    text = re.sub(r'<div class="meta"[^>]*>.*?</div>', " ", text, flags=re.I | re.S)
    text = re.sub(r"<a\b[^>]*class=[\"'][^\"']*attachment[^\"']*[\"'][^>]*>.*?</a>", " ", text, flags=re.I | re.S)
    text = re.sub(r"<br\s*/?>", " ", text, flags=re.I)
    text = re.sub(r"</p>", " ", text, flags=re.I)
    text = re.sub(r"<[^>]+>", " ", text)
    text = html.unescape(text)
    text = re.sub(r"https?://\S+", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) <= max_len:
        return text
    cut = text[: max_len - 1].rsplit(" ", 1)[0].rstrip(".,;:-")
    return (cut or text[: max_len - 1]) + "…"


def normalize_url(href: str) -> str:
    href = html.unescape(href.strip())
    if not href:
        return ""
    if href.startswith("//"):
        return "https:" + href
    if href.startswith("/"):
        return BASE_URL + href
    return href


def detect_extension(url: str, link_text: str = "") -> str:
    path = urllib.parse.urlparse(url).path.lower()
    for ext in VALID_EXTS:
        if path.endswith(ext):
            return ext
    txt = link_text.strip().lower()
    for ext in VALID_EXTS:
        if txt.endswith(ext):
            return ext
    return ""


def is_direct_download_host(url: str) -> bool:
    host = urllib.parse.urlparse(url).netloc.lower()
    if host.endswith("krita-artists.org"):
        return True
    if host in ("github.com", "raw.githubusercontent.com", "objects.githubusercontent.com"):
        return "/releases/download/" in url or host != "github.com"
    if host.endswith("codeberg.org") or host.endswith("gitlab.com"):
        return "/raw/" in url or "/uploads/" in url or "/releases/" in url
    # Evita páginas HTML intermediárias disfarçadas de link direto
    blocked = ("gumroad.com", "ko-fi.com", "patreon.com", "drive.google.com", "mega.nz", "mediafire.com")
    return not any(b in host for b in blocked)


def extract_direct_download(posts: list[dict[str, Any]], author_username: str) -> tuple[str, str]:
    """Procura o melhor link direto (.bundle > .kpp > .sut > .zip) nos posts do autor."""
    candidates: list[tuple[int, str, str]] = []
    anchor_re = re.compile(r"<a\b([^>]*)>(.*?)</a>", flags=re.I | re.S)
    href_re = re.compile(r'href\s*=\s*["\']([^"\']+)["\']', flags=re.I)

    for idx, post in enumerate(posts[:6]):
        if idx > 0 and post.get("username") != author_username:
            continue
        cooked = post.get("cooked") or ""
        for attrs, inner in anchor_re.findall(cooked):
            m = href_re.search(attrs)
            if not m:
                continue
            url = normalize_url(m.group(1))
            if not url.startswith(("http://", "https://")):
                continue
            inner_clean = re.sub(r"<[^>]+>", "", html.unescape(inner)).strip()
            ext = detect_extension(url, inner_clean)
            if not ext:
                continue
            is_attachment = "attachment" in attrs.lower() or "/uploads/short-url/" in url
            if not is_attachment and not is_direct_download_host(url):
                continue
            prio = EXT_PRIORITY.get(ext, 9) + (0 if is_attachment else 10)
            candidates.append((prio, url, ext))
        if candidates and idx == 0:
            break

    if not candidates:
        return "", ""
    candidates.sort(key=lambda c: c[0])
    _, best_url, best_ext = candidates[0]
    return best_url, best_ext


def classify_category(title: str, tags: list[str], description: str) -> str:
    hay = f"{title} {' '.join(tags)} {description}".lower()
    if any(k in hay for k in ("screentone", "halftone", "reticul", "retícula", "manga tone", "tone pack", "hatching", "hachura")):
        return "Retícula"
    if any(k in hay for k in ("pencil", "graphite", "charcoal", "sketch", "crayon", "lápis", "lapis", "grafite")):
        return "Lápis"
    if any(k in hay for k in ("ink", "g-pen", "gpen", "manga", "mangá", "comic", "fineliner", "lineart", "line art", "calligraphy", "sumi", "nanquim", "maru pen", "dip pen")):
        return "Nanquim"
    return "Pintura"


def load_manual_items(root: Path) -> list[dict[str, Any]]:
    manual: list[dict[str, Any]] = []
    seen_ids: set[str] = set()

    for path in (root / "catalogo-extras.json", root / "catalogo-comunidade.json"):
        if not path.exists():
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        arr = data.get("items", []) if isinstance(data, dict) else (data if isinstance(data, list) else [])
        for it in arr:
            if not isinstance(it, dict):
                continue
            is_extra_file = path.name == "catalogo-extras.json"
            if is_extra_file or it.get("manual") is True:
                item_id = str(it.get("id") or "").strip()
                if item_id and item_id not in seen_ids:
                    seen_ids.add(item_id)
                    manual.append(it)
    return manual


def collect_topics(top_pages: int, latest_pages: int, delay: float) -> tuple[list[dict[str, Any]], dict[int, str]]:
    topics_by_id: dict[int, dict[str, Any]] = {}
    users_by_id: dict[int, str] = {}

    urls = [f"{CATEGORY_URL}?order=likes&page={p}" for p in range(top_pages)]
    urls += [f"{CATEGORY_URL}?page={p}" for p in range(latest_pages)]

    for url in urls:
        print(f"Lendo lista: {url}")
        data = fetch_json(url, delay=delay)
        if not data:
            continue
        for u in data.get("users", []):
            uid = u.get("id")
            uname = u.get("name") or u.get("username") or ""
            if uid and uname:
                users_by_id[int(uid)] = str(uname).strip()
        topic_list = (data.get("topic_list") or {}).get("topics") or []
        if not topic_list:
            continue
        for t in topic_list:
            tid = t.get("id")
            if not tid:
                continue
            if t.get("pinned") or t.get("pinned_globally") or t.get("archived"):
                continue
            title = str(t.get("title") or "").strip()
            if not title or title.lower().startswith("about the brushes"):
                continue
            topics_by_id.setdefault(int(tid), t)
        time.sleep(delay)

    topics = list(topics_by_id.values())
    topics.sort(key=lambda t: (int(t.get("like_count") or 0), int(t.get("views") or 0)), reverse=True)
    return topics, users_by_id


def build_catalog(
    root: Path,
    top_pages: int,
    latest_pages: int,
    max_topics: int,
    max_items: int,
    only_direct: bool,
    delay: float,
) -> dict[str, Any]:
    manual_items = load_manual_items(root)
    manual_ids = {str(it.get("id") or "") for it in manual_items}

    topics, users_by_id = collect_topics(top_pages, latest_pages, delay)
    print(f"Tópicos únicos coletados: {len(topics)} (inspecionando até {max_topics})")

    direct_items: list[dict[str, Any]] = []
    portal_linked_items: list[dict[str, Any]] = []

    for idx, t in enumerate(topics[:max_topics], 1):
        tid = int(t["id"])
        item_id = f"ka-{tid}"
        if item_id in manual_ids:
            continue

        slug = str(t.get("slug") or "topic")
        page_url = f"{BASE_URL}/t/{slug}/{tid}"
        title = str(t.get("title") or "").strip()
        likes = int(t.get("like_count") or 0)

        detail = fetch_json(f"{BASE_URL}/t/{tid}.json", delay=delay)
        time.sleep(delay)
        if not detail:
            continue

        posts = (detail.get("post_stream") or {}).get("posts") or []
        if not posts:
            continue
        first_post = posts[0]
        author_username = str(first_post.get("username") or "").strip()
        author_display = str(first_post.get("name") or author_username or "Comunidade Krita").strip()
        if not author_display and t.get("posters"):
            first_uid = t["posters"][0].get("user_id")
            author_display = users_by_id.get(int(first_uid or 0), "Comunidade Krita")

        download_url, ext = extract_direct_download(posts, author_username)
        desc = clean_description(str(first_post.get("cooked") or ""))
        if not desc:
            desc = "Pacote de pincéis compartilhado pela comunidade no Krita-Artists."

        raw_tags = [str(tag).strip() for tag in (detail.get("tags") or t.get("tags") or []) if str(tag).strip()]
        tags: list[str] = []
        for tg in raw_tags:
            if tg.lower() not in [x.lower() for x in tags]:
                tags.append(tg)
        if ext and ext.lstrip(".") not in [x.lower() for x in tags]:
            tags.append(ext.lstrip("."))
        tags = tags[:6]

        category = classify_category(title, tags, desc)
        fmt = ext if ext else "Tópico"

        entry = {
            "id": item_id,
            "name": title,
            "author": author_display,
            "category": category,
            "format": fmt,
            "license": f"Krita-Artists · {likes} curtidas" if likes > 0 else "Krita-Artists",
            "description": desc,
            "tags": tags,
            "download_url": download_url,
            "page_url": page_url,
        }

        if download_url:
            direct_items.append(entry)
            print(f"  [{idx}/{min(len(topics), max_topics)}] +1 direto ({fmt}): {title}")
        elif not only_direct:
            portal_linked_items.append(entry)

        if len(direct_items) >= max_items:
            break

    combined: list[dict[str, Any]] = []
    combined.extend(manual_items)
    remaining = max(0, max_items - len(combined))
    combined.extend(direct_items[:remaining])
    if not only_direct and len(combined) < max_items:
        rest = max_items - len(combined)
        combined.extend(portal_linked_items[:rest])

    existing_ids = {str(it.get("id") or "") for it in combined}
    for p in PORTAL_ITEMS:
        if p["id"] not in existing_ids:
            combined.append(p)

    return {
        "version": 1,
        "updated": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d"),
        "source": "https://krita-artists.org/c/resources/brushes-and-bundles/32",
        "stats": {
            "total": len(combined),
            "instalacao_direta": sum(1 for it in combined if it.get("download_url")),
            "manuais": len(manual_items),
        },
        "items": combined,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Atualiza catalogo-comunidade.json a partir do Krita-Artists.")
    parser.add_argument("--output", default="catalogo-comunidade.json", help="Arquivo JSON de saída")
    parser.add_argument("--top-pages", type=int, default=4, help="Páginas ordenadas por curtidas (30 tópicos/pág.)")
    parser.add_argument("--latest-pages", type=int, default=2, help="Páginas mais recentes")
    parser.add_argument("--max-topics", type=int, default=160, help="Máximo de tópicos inspecionados")
    parser.add_argument("--max-items", type=int, default=150, help="Máximo de itens no catálogo")
    parser.add_argument("--only-direct", action="store_true", help="Incluir apenas itens com download direto em 1 toque")
    parser.add_argument("--delay", type=float, default=0.45, help="Pausa entre requisições (segundos)")
    args = parser.parse_args()

    out_path = Path(args.output).resolve()
    catalog = build_catalog(
        root=out_path.parent,
        top_pages=args.top_pages,
        latest_pages=args.latest_pages,
        max_topics=args.max_topics,
        max_items=args.max_items,
        only_direct=args.only_direct,
        delay=args.delay,
    )

    # Segurança: se o fórum estiver offline, não apaga o catálogo existente
    if catalog["stats"]["instalacao_direta"] == 0 and out_path.exists() and len(catalog["items"]) <= len(PORTAL_ITEMS):
        print("Aviso: nenhum pacote obtido do Krita-Artists agora; mantendo catalogo-comunidade.json atual.", file=sys.stderr)
        return 0

    out_path.write_text(json.dumps(catalog, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(
        f"Pronto! Gravado {out_path.name}: {catalog['stats']['total']} itens "
        f"({catalog['stats']['instalacao_direta']} com instalação em 1 toque)."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
