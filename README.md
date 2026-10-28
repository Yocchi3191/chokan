# chokan

毎朝の「朝刊」を静的HTMLで公開するリポジトリ。

## 構成

| パス | 内容 |
| --- | --- |
| `issues/YYYY-MM-DD.html` | その日の号(毎朝のタスクが追加する) |
| `index.html` | 最新号のコピー。ヘッダーに `archive.html` へのリンク付き(生成物) |
| `archive.html` | バックナンバー一覧。日付降順(生成物) |
| `robots.txt` | 全クローラーを拒否 |
| `scripts/build_archive.py` | `index.html` と `archive.html` の生成と、HTMLの検査 |
| `compose.yaml` | ローカルでのビルドと表示確認用のコンテナ定義 |

## 運用

毎朝のタスクは `issues/YYYY-MM-DD.html` を追加し、続けて次を実行してからpushする。

```bash
python scripts/build_archive.py
```

`issues/` 内のHTMLが次の条件を満たさないと、スクリプトは何も書かずに失敗する。

- `<meta name="robots" content="noindex, nofollow">` がある
- `script`、`iframe`、`form`、`link`、`object`、`embed` を使わない
- 外部JS・外部CSS・外部画像を使わない(`src` などは `data:` のみ可、CSSの `@import` と `url()` も不可)
- `onclick` などのイベントハンドラ属性を使わない

Python 3 の標準ライブラリだけで動く。

## 紙面の仕様(号の生成側が守ること)

号のHTMLは毎朝のタスクが生成する。テンプレートはこのリポジトリに無いため、次の仕様をタスク側にそろえる。

- 題号は「朝刊」。日付行は和暦だけ(`令和8年10月28日（水）`)
- 欄名は、上から順に「脆弱性」(全幅の大見出し)、「技術」、「カルチャー」、「よもやま」、「コラム」
- 「技術」は左列、「カルチャー」「よもやま」「コラム」は右列に積む(`<div class="col-wrap">` の直下に、左列の `section` と右列の `<div class="col">` を置く)

## ローカル環境(コンテナ)

Docker があれば、Python を入れなくてもビルドと表示確認ができる。

```bash
docker compose run --rm build   # index.html / archive.html を生成
docker compose up serve         # http://localhost:8000/ で確認
```

## Cloudflare の設定

### Workers(静的アセット)

Git連携(Workers Builds)で自動デプロイする。ビルドはしない。設定はリポジトリ内のファイルで持つ。

| 項目 | 値 |
| --- | --- |
| Build command | (空) |
| Deploy command | `npx wrangler deploy`(既定) |
| `wrangler.jsonc` | `assets.directory` を `./`(リポジトリのルート)にしてある |
| `.assetsignore` | `README.md`、`scripts/`、設定ファイルを公開対象から外す |

### Pages

Pagesを使う場合は、Build command を空、Build output directory を `/` にする。この場合は `.assetsignore` が効かず、`README.md` や `scripts/` も公開される。非公開にしたい情報は置かない。
