# MarkdownにCSSを適用する簡易ツール

Pythonで動作する簡易的なGUIツールです。

## (1) dlpp.py
ProtoPediaの記事のMarkdownをファイル保存するツールです。

ProtoPediaの作品ページ（例えば https://protopedia.net/prototype/8534 ）の作品番号 (8534) を指定すると、そのページから「システム構成」と「ストーリー」の Markdown をファイルに保存します。ただし、ファイル名は、作品番号＋"_A.md" および 作品番号＋"_B.md" となります。 (例：8534_A.md, 8534_B.md)

### 依存ライブラリのインストール
```bash
pip install requests beautifulsoup4
```

## (2) mdstyle.py
MarkdownにCSSを適用する簡易ツールです。

指定したMarkdownファイルから、見出し行 ```#```, ```##```, ```###``` をHTMLの見出し```<h1>```, ```<h2>```, ```<h3>``` 要素に変換します。指定したCSSファイルのスタイルを使用します。ただし、```<style>```要素を用いるのではなく、個々の見出し要素のタグに ```style=``` の形で記述します。

一般的に、ProtoPediaのようなCMSサイトではセキュリティ上の理由から ```<style>```要素を記事に使用しても無効化されます。このツールを使えば、CMSに貼り付け可能なHTMLを生成できます。

### 依存ライブラリのインストール
```bash
pip install tinycss2 tkinterdnd2
```
