# chokan

毎朝の「ペライチ朝刊」を静的HTMLで公開するリポジトリ。

## 構成

| パス | 内容 |
| --- | --- |
| `issues/YYYY-MM-DD.html` | その日の号(毎朝のタスクが追加する) |
| `index.html` | 最新号のコピー。ヘッダーに `archive.html` へのリンク付き(生成物) |
| `archive.html` | バックナンバー一覧。日付降順(生成物) |
| `robots.txt` | 全クローラーを拒否 |
| `scripts/build_archive.py` | `index.html` と `archive.html` の生成と、HTMLの検査 |

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
