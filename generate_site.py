# -*- coding: utf-8 -*-
"""kotonoha-official.com（GitHub Pages）向け、書籍章別・動画タイムスタンプ中継ページの静的生成。

はてなブログ側の中継ページ（kotonoha-links.hatenablog.com）が、はてな公式ガイドラインの
「外部サイトへの強制リダイレクト禁止」に抵触することが判明したための移行先（2026-08-02
司令塔裁定・鎌倉さん承認）。GitHub Pagesは自分のサイトなので同種の規約制約がなく、広告も出ない。

設計：
- パスは `/go/{source_id}-ch{2桁}/`（例: /go/koto-t01-ch01/）。sourceの言語プレフィックス
  （koto_=英語／kko_=韓国語）を含めることで、将来book番号が言語間で衝突しても安全。
- v1はGA4等の計測を持たない（司令塔裁定：転送の確実さ最優先。流入計測はYouTube Analytics
  側の外部参照元＝kotonoha-official.comで代替。章別クリック計測は後付け可能という判断）。
- リダイレクトは<meta refresh>とJSの二重掛け（JS無効環境でも確実に転送されるように。
  はてな側はJSのみだった）。

再生成: python generate_site.py
"""
from __future__ import annotations

import json
import shutil
from dataclasses import dataclass
from pathlib import Path
from xml.sax.saxutils import escape as xml_escape

ROOT = Path(__file__).parent
DOCS = ROOT / "docs"
CUSTOM_DOMAIN = "kotonoha-official.com"

# 2026-08-02時点：本編動画URL未確定のため全章とも暫定でチャンネルURLへ転送。
# 本編公開後、このBOOKSのvideo_urlを差し替えて再生成するだけで全ページに反映される。
PROVISIONAL_VIDEO_URL = "https://www.youtube.com/@kotonohaeigo"

BOOKS = [
    {
        "source_id": "koto_t01",
        "book_title": "「恋愛で使う英語」英語フレーズ150 #002",
        "chapters": [
            (1, "第一印象のあいさつ"),
            (2, "名前を聞く・自己紹介"),
            (3, "見た目をほめる"),
            (4, "センス・雰囲気をほめる"),
            (5, "連絡先を交換する"),
            (6, "軽く誘ってみる"),
            (7, "デートの計画を立てる"),
            (8, "好意を伝える"),
            (9, "真剣な気持ちを話す"),
            (10, "相手の気持ちを探る"),
            (11, "気持ちを確かめ合う"),
            (12, "次のデートを約束する"),
        ],
    },
]


@dataclass
class RedirectTarget:
    video_url: str
    fallback_label: str = "動画を見る"


def slug_for(source_id: str, chapter_no: int) -> str:
    """パス用スラッグ（言語プレフィックス込み・go-プレフィックスは付けない＝ディレクトリが/go/なので冗長）。"""
    return f"{source_id.replace('_', '-')}-ch{chapter_no:02d}"


PAGE_TEMPLATE = """<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<link rel="icon" href="/favicon.png">
<meta http-equiv="refresh" content="0;url={url}">
<meta name="robots" content="noindex">
<style>
  html,body{{height:100%;margin:0;background:#03102a;color:#f3e6c8;
    font-family:"Hiragino Sans","Yu Gothic",sans-serif;}}
  body{{display:flex;align-items:center;justify-content:center;text-align:center;padding:24px;
    box-sizing:border-box;}}
  .card{{max-width:420px;}}
  .brand{{font-size:14px;letter-spacing:.08em;color:#c9a35a;margin-bottom:18px;}}
  p{{font-size:16px;line-height:1.8;margin:0 0 12px;}}
  a{{color:#f5d98c;text-decoration:underline;}}
</style>
</head>
<body>
  <div class="card">
    <div class="brand">ことのは英語｜動画連動フレーズ集</div>
    <p>まもなく動画へ移動します。</p>
    <p>移動しない場合は <a href="{url}">こちら（{label}）</a> をクリックしてください。</p>
  </div>
<script>window.location.replace("{url}");</script>
</body>
</html>
"""

ROOT_INDEX_TEMPLATE = """<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>ことのは公式サイト（準備中）</title>
<link rel="icon" href="/favicon.png">
<style>
  html,body{{height:100%;margin:0;background:#03102a;color:#f3e6c8;
    font-family:"Hiragino Sans","Yu Gothic",sans-serif;}}
  body{{display:flex;align-items:center;justify-content:center;text-align:center;}}
  h1{{font-weight:500;letter-spacing:.06em;}}
</style>
</head>
<body>
  <h1>ことのは公式サイト（準備中）</h1>
</body>
</html>
"""


def build_page_html(title: str, target: RedirectTarget) -> str:
    return PAGE_TEMPLATE.format(
        title=xml_escape(title),
        url=xml_escape(target.video_url),
        label=xml_escape(target.fallback_label),
    )


def generate() -> list[dict]:
    if DOCS.exists():
        shutil.rmtree(DOCS)
    DOCS.mkdir(parents=True)

    (DOCS / "CNAME").write_text(CUSTOM_DOMAIN + "\n", encoding="utf-8")
    (DOCS / "index.html").write_text(ROOT_INDEX_TEMPLATE, encoding="utf-8")
    (DOCS / ".nojekyll").write_text("", encoding="utf-8")

    icon_src = ROOT.parent / "kotonoha_links" / "画像" / "koto_links_icon.png"
    if icon_src.exists():
        shutil.copy(icon_src, DOCS / "favicon.png")

    go_dir = DOCS / "go"
    go_dir.mkdir(exist_ok=True)

    mapping = []
    target = RedirectTarget(video_url=PROVISIONAL_VIDEO_URL)
    for book in BOOKS:
        for chapter_no, chapter_label in book["chapters"]:
            slug = slug_for(book["source_id"], chapter_no)
            title = f"{book['book_title']}｜第{chapter_no}章「{chapter_label}」動画リンク"
            page_dir = go_dir / slug
            page_dir.mkdir(parents=True, exist_ok=True)
            (page_dir / "index.html").write_text(build_page_html(title, target), encoding="utf-8")
            mapping.append({
                "source_id": book["source_id"],
                "chapter_no": chapter_no,
                "chapter_label": chapter_label,
                "old_hatena_url": f"https://kotonoha-links.hatenablog.com/entry/go-{slug}",
                "new_url": f"https://{CUSTOM_DOMAIN}/go/{slug}/",
            })

    (ROOT / "旧URL_新URL対応表.json").write_text(
        json.dumps(mapping, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return mapping


if __name__ == "__main__":
    result = generate()
    print(f"生成完了: {len(result)}ページ -> {DOCS}")
