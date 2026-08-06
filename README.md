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
4. **push成功≠公開成功＝必ずビルド状態を確認すること**（下記「pushごとの標準手順」参照）

## pushごとの標準手順（恒久・2026-08-06司令塔指示で明文化）

`git push`が成功しても、GitHub Pages側のビルドが裏で失敗し、新規/更新ページが**サイレントに反映されない**事象が実際に2回発生した（2026-08-03のCNAME再設定直後・2026-08-06のkoto_s08/koto_d01追加時）。push成功をもって完了報告しないこと。

1. push後、`gh api repos/kamakura168mm-netizen/kotonoha-official-site/pages/builds/latest`で該当commitの`status`を確認する
2. `status: "built"` なら次工程（全ページHTTP実測）へ進む
3. `status: "errored"` なら `gh api -X POST repos/kamakura168mm-netizen/kotonoha-official-site/pages/builds` で公式の再ビルドAPIを叩き、再度①へ戻る（2026-08-03・2026-08-06とも1回の再実行で解消した既知パターン）
4. 再ビルドを1回試しても`errored`が続く場合は、原因不明の新種障害の可能性があるため自己判断で繰り返さず司令塔へ一報する
5. ビルド成功確認後、全ページ（`旧URL_新URL対応表.json`記載の全件）をHTTP実測すること。直後は数十秒〜1分程度CDNキャッシュの反映待ちで404が出ることがある（ビルド失敗とは別の正常な遅延＝待って再確認すればよい。ビルドが`errored`のまま何時間待っても解消しない点と区別すること）

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
