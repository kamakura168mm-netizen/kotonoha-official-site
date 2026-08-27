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

# 2026-08-02時点：koto_t01は本編動画URL未確定のため全章とも暫定でチャンネルURLへ転送。
# 本編公開後、このBOOKSのvideo_urlを差し替えて再生成するだけで全ページに反映される。
PROVISIONAL_VIDEO_URL = "https://www.youtube.com/@kotonohaeigo"

# koto_t01：#002書籍。本編は8/8 22:5x頃公開・橋検証全項目合格を司令塔がAPI実測で確認済み(2026-08-08司令塔合図)。
KOTO_T01_VIDEO_URL = "https://youtu.be/4V-n_WSkz4A"

# koto_y06：販売中の#001書籍が指す旧動画(Xwlnqn1rgzs)が7/30の英語chリセットで削除された実害修理。
# 新版wIawOZqYL6Eは8/6 21:38公開予約＝それまでは全章ともチャンネルURLへ暫定転送。
# 公開後、KOTO_Y06_VIDEO_URLを実URLへ差し替えて再生成・push（司令塔の合図で実施）。
KOTO_Y06_VIDEO_URL = "https://youtu.be/wIawOZqYL6E"  # 8/6 21:38公開・public実測済み(2026-08-06司令塔合図)

# kko_d03：mCdUIhr2OdIは公開中のため初回から実タイムスタンプへ転送。
KKO_D03_VIDEO_ID = "mCdUIhr2OdI"

# 韓国語chの暫定転送先（book.json記載のチャンネルURL＝英語のPROVISIONAL_VIDEO_URLに相当）。
KKO_PROVISIONAL_CHANNEL_URL = "https://www.youtube.com/channel/UCwRaNI6nFMYQ9fBUb2fdCZA"

# koto_y10：#003書籍。本編は8/10 21:38公開（司令塔第28期がAPI実測でpublic確認済み・21:39:09）。
KOTO_Y10_VIDEO_URL = "https://youtu.be/1oagjWeUC5s"

# kko_t01：#002書籍。本編は8/6 21:38公開予定（koto_y06とセット）＝それまで全章ともチャンネルURLへ暫定転送。
# 公開後、実動画URLへ差し替えて再生成・push（司令塔の合図で実施）。
KKO_T01_VIDEO_URL = "https://youtu.be/RAKVipS86E4"  # 8/6 21:38公開・public実測済み(2026-08-06司令塔合図)

# kko_t02：#003書籍（書籍本体は未制作・QR飛び先の先行インフラとして中継ページのみ先行制作）。
# 本編は8/10 21:38公開（司令塔第28期がAPI実測でpublic確認済み・21:39:09）。
# ※コメント上は当初8/12(水)予定だったが前倒しで8/10に確定（2026-08-09夜ドライランでAPI実測・publishAt=2026-08-10T12:38:00Z確認済み）。
KKO_T02_VIDEO_URL = "https://youtu.be/OThI_ipiW6c"

# kko_t03：#004書籍（書籍本体は未制作・QR飛び先の先行インフラとして中継ページのみ先行制作）。
# 本編の公開日程は本メッセージ時点で未確定＝それまで全章ともチャンネルURLへ暫定転送。
# 公開後、実動画URLへ差し替えて再生成・push（司令塔の合図で実施）。
KKO_T03_VIDEO_URL = "https://www.youtube.com/watch?v=EdOmS7EN25Y"  # 2026-08-14 21:38公開・司令塔配下Sonnetワーカー代行実施

# koto_t02：#004書籍「セクハラになる英語・ならない英語」（book.json記載の号数。司令塔発注メッセージは
# #005表記だったが、原稿/book.jsonを正として#004を採用）。本編は未公開のためチャンネルURLへ暫定転送。
# 公開後、実動画URLへ差し替えて再生成・push（司令塔の合図で実施）。
KOTO_T02_VIDEO_URL = PROVISIONAL_VIDEO_URL  # 公開後に実URLへ差し替え

# koto_s08：#005書籍「寝る前の前向きなひとこと」。本編は未公開のためチャンネルURLへ暫定転送。
# 公開後、実動画URLへ差し替えて再生成・push（司令塔の合図で実施）。
KOTO_S08_VIDEO_URL = "https://youtu.be/az2Jpd_szsw"  # 2026-08-13 21:39:14 JST public確認・司令塔第32期代行(Sonnetワーカー)実施

# koto_d01：#006書籍「知ってる単語だけで、ここまで話せる」（2026-08-07に旧題「中学英語・毎日の基本」
# から本人裁定でタイトル変更・書籍本体のbook_titleは既に新題）。本編は2026-08-21 21:38 JST公開済み
# （公開スケジュール管理レーンがvideos.list実測でprivacyStatus=public確認・video_id=K_rUDKgCeTw）。
# 2026-08-22・司令塔37期GOによりKDPライブ提出第5期が実URLへ差し替え。
KOTO_D01_VIDEO_URL = "https://youtu.be/K_rUDKgCeTw"

# kko_t05：#006書籍「気遣い（ヌンチ）で使う韓国語」。本編は2026-08-18 21:38:22 JST公開済み
# （KDPライブ提出第5期がvideos.list実測でprivacyStatus=public確認済み・2026-08-19）。
KKO_T05_VIDEO_URL = "https://youtu.be/3325PNj6enQ"

# koto_e03：#016書籍「気まずくならない、英語の断り方150フレーズ」。本編は2026-08-25 21:38:27 JST公開済み
# （公開スケジュール管理レーンがvideos.list実測で確認・司令塔39期経由でKDPライブ提出第5期へ着手GO）。
KOTO_E03_VIDEO_URL = "https://youtu.be/FsmqlPykGkc"

# kko_t10：#008書籍「聞こえるのに分からない、乗り物の韓国語150フレーズ」。本編は2026-08-26 21:38予約済み
# （2026-08-26朝時点でまだ非公開・本人指示による提出前倒しのため中継ページを先行生成。QRを today踏んだ
# 場合は非公開表示になるが、審査所要時間を考慮し司令塔判断で実害なしとされている＝2026-08-26司令塔39期）。
KKO_T10_VIDEO_URL = "https://youtu.be/MAolNaiIMJM"

# kko_t04：#005書籍「年齢の聞き方で使う韓国語」。本編は2026-08-27 21:38公開済み
# （KDPライブ提出第6期がvideos.list実測でprivacyStatus=public確認済み・video_id=e2qCAW0D_Sw）。
KKO_T04_VIDEO_URL = "https://youtu.be/e2qCAW0D_Sw"

# koto_e04：#017書籍「我慢しすぎない、英語の怒り方・クレーム150フレーズ」。本編は2026-08-28 21:38公開予約済み
# （video_id=oOcnH5a19m8・2026-08-27時点で未公開）＝それまで全章ともチャンネルURLへ暫定転送。
# 公開後、実動画URLへ差し替えて再生成・push（司令塔の合図で実施）。
KOTO_E04_VIDEO_URL = PROVISIONAL_VIDEO_URL  # 公開後に実URLへ差し替え

# koto_e01：#008書籍「英語面接で使えるフレーズ」。本編は2026-08-29 21:38公開予約済み
# （video_id=K6zmAQjlHbI・2026-08-27時点で未公開・YouTube API実測でpublishAt確認済み）。
# 公開後、実動画URLへ差し替えて再生成・push（司令塔の合図で実施）。
KOTO_E01_VIDEO_URL = PROVISIONAL_VIDEO_URL  # 公開後に実URLへ差し替え

# koto_s02：#007書籍「道案内と電車の英語」。本編は2026-08-31 21:38公開予約済み
# （video_id=_kNVpKSZyqk・2026-08-27時点で未公開・YouTube API実測でpublishAt確認済み）。
# 公開後、実動画URLへ差し替えて再生成・push（司令塔の合図で実施）。
KOTO_S02_VIDEO_URL = PROVISIONAL_VIDEO_URL  # 公開後に実URLへ差し替え


def _load_chapters(path: Path) -> list[tuple[int, str, float]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    return [(c["chapter_no"], c["label"], c["start_sec"]) for c in data]


BOOKS = [
    {
        "source_id": "koto_t01",
        "book_title": "「恋愛で使う英語」英語フレーズ150 #002",
        "channel": "ことのは英語",
        "video_url": KOTO_T01_VIDEO_URL,
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
    {
        "source_id": "koto_y06",
        "book_title": "寝る前に一日をふりかえる 英語フレーズ #001",
        "channel": "ことのは英語",
        "video_url": KOTO_Y06_VIDEO_URL,
        "chapters": [
            (no, label) for no, label, _sec in
            _load_chapters(ROOT.parent / "動画連動フレーズ集" / "koto_y06" / "章構成.json")
        ],
    },
    {
        "source_id": "kko_d03",
        "book_title": "はじめての自己紹介 韓国語フレーズ #001",
        "channel": "ことのは韓国語",
        "video_url": None,  # 章ごとにタイムスタンプ付きURLを個別生成（下記参照）
        "chapters_with_sec": _load_chapters(ROOT.parent / "動画連動フレーズ集" / "kko_d03" / "章構成.json"),
    },
    {
        "source_id": "koto_y10",
        "book_title": "「寝る前に自分をいたわる」英語フレーズ155 #003",
        "channel": "ことのは英語",
        "video_url": KOTO_Y10_VIDEO_URL,
        "chapters": [
            (1, "今夜はあなたのための時間"),
            (2, "今日一日、本当によくがんばった"),
            (3, "完璧じゃなくていい"),
            (4, "弱音を吐いてもいい"),
            (5, "体と心の力を抜く"),
            (6, "気づかれない小さながんばり"),
            (7, "誰かと比べなくていい"),
            (8, "その気持ちのままでいい"),
            (9, "あなたを支えているもの"),
            (10, "明日はまた大丈夫"),
            (11, "眠りへの橋渡し"),
            (12, "おやすみ、そしてありがとう"),
        ],
    },
    {
        "source_id": "kko_t01",
        "book_title": "「恋愛で使う韓国語」韓国語フレーズ150 #002",
        "channel": "ことのは韓国語",
        "video_url": KKO_T01_VIDEO_URL,
        "chapters": [
            (1, "声をかける・第一印象"),
            (2, "名前を聞く・自己紹介"),
            (3, "見た目をほめる"),
            (4, "センス・雰囲気をほめる"),
            (5, "連絡先を交換する"),
            (6, "軽く誘ってみる"),
            (7, "デートの計画を立てる"),
            (8, "「썸」を意識する"),
            (9, "「반말」に切り替える"),
            (10, "好意を伝える"),
            (11, "真剣な気持ちを話す・気持ちを確かめ合う"),
            (12, "付き合う・次の約束"),
        ],
    },
    {
        "source_id": "kko_t02",
        "book_title": "「ケンカと仲直りで使う韓国語」韓国語フレーズ150 #003",
        "channel": "ことのは韓国語",
        "video_url": KKO_T02_VIDEO_URL,
        "chapters": [
            (1, "違和感に気づく"),
            (2, "すれ違いが始まる"),
            (3, "不満を軽く伝える"),
            (4, "沈黙・距離ができる"),
            (5, "我慢の限界を伝える"),
            (6, "本音をぶつける・言い争い"),
            (7, "一人になって考える"),
            (8, "後悔がよぎる"),
            (9, "連絡を取り直す勇気"),
            (10, "謝る"),
            (11, "相手の話を聞く・許す"),
            (12, "仲直り・前より深まる関係"),
        ],
    },
    {
        "source_id": "kko_t03",
        "book_title": "「別れと失恋で使う韓国語」韓国語フレーズ150 #004",
        "channel": "ことのは韓国語",
        "video_url": KKO_T03_VIDEO_URL,
        "chapters": [
            (1, "気持ちが冷めていく"),
            (2, "心の距離を感じる"),
            (3, "別れを意識し始める"),
            (4, "気持ちを確かめ合う"),
            (5, "別れを切り出す・告げられる"),
            (6, "未練が残る"),
            (7, "一人の夜"),
            (8, "友人に話す・慰められる"),
            (9, "忘れようとする"),
            (10, "ふとした瞬間に思い出す"),
            (11, "気持ちの整理がつく"),
            (12, "新しい一歩を踏み出す"),
        ],
    },
    {
        "source_id": "koto_t02",
        "book_title": "「セクハラになる英語・ならない英語」英語フレーズ150 #004",
        "channel": "ことのは英語",
        "video_url": KOTO_T02_VIDEO_URL,
        "chapters": [
            (1, "安全な褒め言葉の基本形"),
            (2, "外見を褒める境界線"),
            (3, "服装・見た目への言及"),
            (4, "体型・年齢の話題【危険度集中】"),
            (5, "職場での距離感"),
            (6, "誘い方の境界線"),
            (7, "しつこい誘い・繰り返しのアプローチ"),
            (8, "不快だと伝える英語"),
            (9, "きっぱり断る英語"),
            (10, "指摘・拒否を受け止める英語"),
            (11, "誤解に気づいて謝る英語"),
            (12, "気持ちよく話せる関係へ"),
        ],
    },
    {
        "source_id": "koto_s08",
        "book_title": "「寝る前の前向きなひとこと」英語フレーズ155 #005",
        "channel": "ことのは英語",
        "video_url": KOTO_S08_VIDEO_URL,
        "chapters": [
            (1, "一日の終わりを認める"),
            (2, "今日できたことを数える"),
            (3, "うまくいかなかったことを受け止める"),
            (4, "がんばった自分をねぎらう"),
            (5, "休んでいい理由を並べる"),
            (6, "体の力を抜いていく"),
            (7, "心配ごとを脇に置く"),
            (8, "小さな失敗を許す"),
            (9, "今いる場所の心地よさに気づく"),
            (10, "心がしずかになっていく"),
            (11, "明日への静かな期待"),
            (12, "眠りに落ちていく"),
        ],
    },
    {
        "source_id": "koto_d01",
        "book_title": "「中学英語・毎日の基本」英語フレーズ155 #006",
        "channel": "ことのは英語",
        "video_url": KOTO_D01_VIDEO_URL,
        "chapters": [
            (1, "朝の支度"),
            (2, "家を出て学校・職場へ"),
            (3, "学校・職場でのひとこま"),
            (4, "お店での買い物"),
            (5, "友人とのおしゃべり"),
            (6, "食事の場面"),
            (7, "電話とメッセージ"),
            (8, "天気の話題"),
            (9, "体調と気分を伝える"),
            (10, "週末の予定を話す"),
            (11, "お礼とちょっとした謝罪"),
            (12, "一日を振り返って"),
        ],
    },
    {
        "source_id": "kko_t05",
        "book_title": "「気遣い（ヌンチ）で使う韓国語」韓国語フレーズ150 #006",
        "channel": "ことのは韓国語",
        "video_url": KKO_T05_VIDEO_URL,
        "chapters": [
            (1, "相手の様子にさりげなく気づく"),
            (2, "さりげなく声をかける"),
            (3, "忙しそうな相手を気遣う"),
            (4, "体調を気遣う"),
            (5, "謝罪と労いが同居する韓国語"),
            (6, "눈치という感覚そのもの"),
            (7, "遠慮を遠慮させる"),
            (8, "ご馳走する・奢る文化の気遣い"),
            (9, "小さな贈り物・気持ちを渡す文化"),
            (10, "別れ際の気遣い"),
            (11, "落ち込んでいる人への気遣い"),
            (12, "集団の中での気遣い"),
            (13, "気遣いを受けた側の感謝"),
        ],
    },
    {
        "source_id": "koto_e03",
        "book_title": "気まずくならない、英語の断り方150フレーズ #016",
        "channel": "ことのは英語",
        "video_url": KOTO_E03_VIDEO_URL,
        "chapters": [
            (1, "誘いを断る"),
            (2, "頼まれごとを断る"),
            (3, "厚意・支払いを遠慮する"),
            (4, "お酒を断る"),
            (5, "告白を断る"),
            (6, "仕事の依頼を断る"),
            (7, "きっぱり伝える"),
            (8, "断られた時の受け止め方"),
            (9, "代案を出して断る"),
            (10, "家族・パートナーに断る"),
            (11, "やわらかいクッション言葉"),
            (12, "断った後のフォロー"),
            (13, "ノーは自分を大切にすること"),
        ],
    },
    {
        "source_id": "kko_t10",
        "book_title": "韓国の地下鉄・バス・タクシーにひとりで乗れる 韓国語フレーズ150 #008",
        "channel": "ことのは韓国語",
        "video_url": KKO_T10_VIDEO_URL,
        "chapters": [
            (1, "地下鉄のアナウンスに気づく"),
            (2, "乗り換えのアナウンスを聞き取る"),
            (3, "ドアの開閉・注意アナウンス"),
            (4, "タクシーに乗る・行き先を伝える"),
            (5, "運転手から話しかけられる"),
            (6, "運転手が確認してくること"),
            (7, "バス停での呼びかけ"),
            (8, "バス車内のアナウンス"),
            (9, "駅員に尋ねる・返ってくる説明"),
            (10, "迷った時に呼び止められる"),
            (11, "空港リムジンバスのアナウンス"),
            (12, "電車内での忘れ物・トラブル放送"),
            (13, "到着・下車時の一言"),
        ],
    },
    {
        "source_id": "kko_t04",
        "book_title": "「年齢の聞き方で使う韓国語」韓国語フレーズ150 #005",
        "channel": "ことのは韓国語",
        "video_url": KKO_T04_VIDEO_URL,
        "chapters": [
            (1, "初対面で年齢が気になる"),
            (2, "敬語で年齢を聞く・同い年で반말提案"),
            (3, "答え方のバリエーション（はぐらかす）"),
            (4, "年上だと分かった時の変化"),
            (5, "年下だと分かった時の変化"),
            (6, "만 나이／세는 나이の戸惑い"),
            (7, "昔の話・共通の話題に広がる"),
            (8, "職場での年齢と社歴の確認"),
            (9, "気まずい場面の切り返し"),
            (10, "年齢を超えた関係へ着地"),
            (11, "家族・呼び方の広がり"),
            (12, "SNS・マッチングアプリの年齢表記文化"),
            (13, "再会・同窓会での年齢の変化"),
        ],
    },
    {
        "source_id": "koto_e04",
        "book_title": "我慢しすぎない、英語の怒り方・クレーム150フレーズ #017",
        "channel": "ことのは英語",
        "video_url": KOTO_E04_VIDEO_URL,
        "chapters": [
            (1, "小さな苛立ちの兆し"),
            (2, "友人へのちょっとした文句"),
            (3, "家族への率直な苛立ち"),
            (4, "店員への軽い指摘"),
            (5, "お店への正式なクレーム"),
            (6, "配達・注文ミスへの苦情"),
            (7, "職場での不満の伝え方"),
            (8, "上司への正式な訴え"),
            (9, "我慢の限界を超えた瞬間"),
            (10, "頭を冷やして言い直す"),
            (11, "謝罪を受け止める・関係を戻す"),
            (12, "対立を和らげる英語特有の一言"),
            (13, "「怒ってもいい」という着地"),
        ],
    },
    {
        "source_id": "koto_e01",
        "book_title": "「英語面接で使えるフレーズ」英語フレーズ150 #008",
        "channel": "ことのは英語",
        "video_url": KOTO_E01_VIDEO_URL,
        "chapters": [
            (1, "英語面接の受付・あいさつ"),
            (2, "英語面接 自己紹介の基本"),
            (3, "英語で職務経歴を話す"),
            (4, "英語面接 志望動機の伝え方"),
            (5, "英語面接 強みのアピール"),
            (6, "英語面接 弱みの答え方"),
            (7, "転職理由を英語で伝える"),
            (8, "英語 面接 エピソード（STAR法）"),
            (9, "会社について聞かれる英語面接の質問"),
            (10, "英語面接 逆質問（キャリア編）"),
            (11, "給与交渉・条件を英語で"),
            (12, "オンライン面接 英語表現"),
            (13, "面接のお礼・フォローアップメール英語"),
        ],
    },
    {
        "source_id": "koto_s02",
        "book_title": "「道案内と電車の英語」英語フレーズ150 #007",
        "channel": "ことのは英語",
        "video_url": KOTO_S02_VIDEO_URL,
        "chapters": [
            (1, "道を尋ねる最初の一言"),
            (2, "切符・改札"),
            (3, "駅構内・ホーム"),
            (4, "電車・バスに乗る"),
            (5, "降りる・タクシー"),
            (6, "道に迷った・助けを求める"),
            (7, "お礼・別れ"),
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
    <div class="brand">{brand}｜動画連動フレーズ集</div>
    <p>まもなく動画へ移動します。</p>
    <p>移動しない場合は <a href="{url}">こちら（{label}）</a> をクリックしてください。</p>
  </div>
<script>window.location.replace({url_js});</script>
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


def build_page_html(title: str, target: RedirectTarget, brand: str) -> str:
    return PAGE_TEMPLATE.format(
        title=xml_escape(title),
        url=xml_escape(target.video_url),
        url_js=json.dumps(target.video_url),
        label=xml_escape(target.fallback_label),
        brand=xml_escape(brand),
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
    for book in BOOKS:
        if "chapters_with_sec" in book:
            # 章ごとに固有のタイムスタンプURLを持つ書籍（例: kko_d03）
            entries = [
                (no, label, f"https://www.youtube.com/watch?v={KKO_D03_VIDEO_ID}&t={int(sec)}s")
                for no, label, sec in book["chapters_with_sec"]
            ]
        else:
            entries = [(no, label, book["video_url"]) for no, label in book["chapters"]]

        for chapter_no, chapter_label, video_url in entries:
            slug = slug_for(book["source_id"], chapter_no)
            title = f"{book['book_title']}｜第{chapter_no}章「{chapter_label}」動画リンク"
            page_dir = go_dir / slug
            page_dir.mkdir(parents=True, exist_ok=True)
            target = RedirectTarget(video_url=video_url)
            html = build_page_html(title, target, book["channel"])
            (page_dir / "index.html").write_text(html, encoding="utf-8")
            mapping.append({
                "source_id": book["source_id"],
                "chapter_no": chapter_no,
                "chapter_label": chapter_label,
                "redirect_target": video_url,
                "new_url": f"https://{CUSTOM_DOMAIN}/go/{slug}/",
            })

    (ROOT / "旧URL_新URL対応表.json").write_text(
        json.dumps(mapping, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return mapping


if __name__ == "__main__":
    result = generate()
    print(f"生成完了: {len(result)}ページ -> {DOCS}")
