# kotonoha-official.com

「ことのは」書籍・動画連動フレーズ集の章別中継ページ（GitHub Pages配信）。

## 背景

はてなブログ中継ページ（kotonoha-links.hatenablog.com）が、はてな公式ガイドラインの
「外部サイトへの強制リダイレクト禁止」に抵触することが判明したため、2026-08-02に
独自ドメイン + GitHub Pagesへ移行することになった。詳細はブログ実装セッションの
司令塔宛て報告を参照。

## 構成

- `docs/` — GitHub Pages配信ルート（Settings > Pages > Source を `main` ブランチ
  `/docs` に設定すること）
- `docs/CNAME` — カスタムドメイン設定（kotonoha-official.com）
- `docs/go/{source_id}-ch{NN}/index.html` — 書籍・章ごとの中継ページ（1章1URL・恒久固定）
- `docs/index.html` — トップページ（現状は準備中プレースホルダー。将来「公式サイト」を配置）
- `generate_site.py` — 全ページの生成スクリプト。`BOOKS`定義を編集して再実行すれば全ページに反映

## 動画URL確定後の更新手順

1. `generate_site.py`の`PROVISIONAL_VIDEO_URL`（または該当書籍のvideo_url）を実際のURLへ更新
2. `python generate_site.py`で再生成
3. `git add -A && git commit -m "..." && git push`

## DNS設定（お名前.com側）

アペックスドメイン（kotonoha-official.com）にAレコード4本を登録：

```
185.199.108.153
185.199.109.153
185.199.110.153
185.199.111.153
```

## v1のスコープ外（意図的）

- GA4等の計測タグ（司令塔裁定：転送優先。流入計測はYouTube Analytics側の外部参照元で代替）
- 章別クリック計測（後付け可能という前提で見送り）
- 紙版QRの12個化（工数大のため次回改訂で検討）
