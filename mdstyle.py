import json
import re
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox
import tinycss2
from tkinterdnd2 import DND_FILES, TkinterDnD
from html import escape

# 設定ファイル（スクリプトと同じフォルダ）
CONFIG_FILE = Path(__file__).with_name("mdstyle.json")


# 前回の設定を読み込む
def load_settings():
    try:
        return json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


# 現在の設定を保存する
def save_settings():
    settings = {
        "markdown": markdown_var.get(),
        "css": css_var.get(),
        "output": output_var.get(),
    }
    try:
        CONFIG_FILE.write_text(
            json.dumps(settings, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    except OSError as e:
        messagebox.showwarning(
            "設定保存エラー",
            f"設定を保存できませんでした。\n{e}",
        )


# CSSからh1、h2、h3のスタイルを取得する
def load_css_styles(css_file):
    css = Path(css_file).read_text(encoding="utf-8")
    rules = tinycss2.parse_stylesheet(
        css, skip_comments=True, skip_whitespace=True
    )

    styles = {"h1": {}, "h2": {}, "h3": {}, "h4": {}, "h5": {}, "h6": {}}

    for rule in rules:
        if rule.type != "qualified-rule":
            continue

        selector = tinycss2.serialize(rule.prelude).strip()
        declarations = tinycss2.parse_declaration_list(
            rule.content, skip_comments=True, skip_whitespace=True
        )

        if selector not in styles:
            continue

        for decl in declarations:
            if decl.type == "declaration":
                styles[selector][decl.name] = (
                    tinycss2.serialize(decl.value).strip()
                )

    return styles


# Markdownの見出しをインラインスタイル付きHTMLに変換する
def convert_markdown(md_file, css_file):
    markdown = Path(md_file).read_text(encoding="utf-8")
    styles = load_css_styles(css_file)

    def replace_heading(match):
        level = len(match.group(1))
        tag = f"h{level}"
        text = escape(match.group(2).strip())

        style = "; ".join(
            f"{name}: {value}"
            for name, value in styles[tag].items()
        )

        if style:
            return (
                f'<{tag} style="{escape(style, quote=True)}">'
                f'{text}</{tag}>'
            )

        return f"<{tag}>{text}</{tag}>"

    pattern = re.compile(
        r"^(#{1,6})[ \t]+(.+?)[ \t]*#*[ \t]*$",
        re.MULTILINE,
    )
    return pattern.sub(replace_heading, markdown)


# Markdownファイルを選択する
def choose_markdown():
    path = filedialog.askopenfilename(
        title="Markdownファイルを選択",
        filetypes=[
            ("Markdownファイル", "*.md *.markdown"),
            ("すべてのファイル", "*.*"),
        ],
    )
    if path:
        markdown_var.set(path)
        if not output_var.get().strip():
            output_var.set(str(Path(path).with_suffix(".html")))
        save_settings()


# CSSファイルを選択する
def choose_css():
    path = filedialog.askopenfilename(
        title="CSSファイルを選択",
        filetypes=[
            ("CSSファイル", "*.css"),
            ("すべてのファイル", "*.*"),
        ],
    )
    if path:
        css_var.set(path)
        save_settings()


# 出力先を選択する
def choose_output():
    path = filedialog.asksaveasfilename(
        title="出力先を選択",
        defaultextension=".html",
        filetypes=[
            ("HTMLファイル", "*.html"),
            ("すべてのファイル", "*.*"),
        ],
    )
    if path:
        output_var.set(path)
        save_settings()


# ドロップされたファイルのパスを入力欄に設定する
def on_drop(event, variable):
    try:
        paths = root.tk.splitlist(event.data)
        if not paths:
            return

        path = paths[0]
        variable.set(path)

        if variable is markdown_var and not output_var.get().strip():
            output_var.set(str(Path(path).with_suffix(".html")))

        save_settings()
    except (tk.TclError, OSError) as e:
        messagebox.showerror("エラー", str(e))


# 入力ファイルを検証してHTML文字列を取得する
def get_converted_html():
    md_file = markdown_var.get().strip()
    css_file = css_var.get().strip()

    if not md_file or not Path(md_file).is_file():
        raise ValueError("Markdownファイルを選択してください。")

    if not css_file or not Path(css_file).is_file():
        raise ValueError("CSSファイルを選択してください。")

    return convert_markdown(md_file, css_file)


# Markdownをスタイル付きHTMLに変換して保存する
def convert():
    output_file = output_var.get().strip()

    if not output_file:
        messagebox.showerror(
            "出力エラー", "出力先を指定してください。"
        )
        return

    try:
        result = get_converted_html()
        Path(output_file).write_text(result, encoding="utf-8")
        save_settings()
        messagebox.showinfo(
            "完了", f"変換しました。\n\n{output_file}"
        )
    except (OSError, ValueError) as e:
        messagebox.showerror("変換エラー", str(e))


# 変換結果をクリップボードにコピーする
def copy_to_clipboard():
    try:
        result = get_converted_html()

        root.clipboard_clear()
        root.clipboard_append(result)
        root.update()  # クリップボードへの反映を確実にする

        save_settings()

        messagebox.showinfo(
            "コピー完了",
            "変換結果をクリップボードにコピーしました。\n\n"
            "貼り付け先で Ctrl+V を押してください。",
        )
    except (OSError, ValueError, tk.TclError) as e:
        messagebox.showerror("コピーエラー", str(e))


# ---------- GUI ----------

root = TkinterDnD.Tk()
root.title("Markdown スタイル変換")
root.geometry("760x280")
root.minsize(600, 280)

settings = load_settings()

markdown_var = tk.StringVar(value=settings.get("markdown", ""))
css_var = tk.StringVar(value=settings.get("css", ""))
output_var = tk.StringVar(value=settings.get("output", ""))


# GUIにファイル選択の行を追加する
def add_file_row(row, label, variable, browse_command, droppable=True):
    tk.Label(root, text=label, width=12, anchor="w").grid(
        row=row, column=0, padx=(10, 4), pady=8, sticky="w"
    )

    entry = tk.Entry(root, textvariable=variable)
    entry.grid(
        row=row, column=1, padx=4, pady=8, sticky="ew"
    )

    tk.Button(
        root, text="参照...", command=browse_command, width=10
    ).grid(row=row, column=2, padx=(4, 10), pady=8)

    if droppable:
        entry.drop_target_register(DND_FILES)
        entry.dnd_bind(
            "<<Drop>>",
            lambda event, var=variable: on_drop(event, var),
        )


root.columnconfigure(1, weight=1)

add_file_row(
    0, "Markdown:", markdown_var, choose_markdown
)
add_file_row(
    1, "CSS:", css_var, choose_css
)
add_file_row(
    2, "出力先:", output_var, choose_output, droppable=False
)

tk.Label(
    root,
    text="Markdown / CSS は入力欄にドラッグ＆ドロップできます。",
    anchor="w",
).grid(row=3, column=0, columnspan=3, padx=12, pady=(0, 8), sticky="w")

# ボタンを横並びに配置する
button_frame = tk.Frame(root)
button_frame.grid(row=4, column=0, columnspan=3, pady=8)

tk.Button(
    button_frame,
    text="変換して保存",
    command=convert,
    width=18,
    height=2,
).pack(side="left", padx=8)

tk.Button(
    button_frame,
    text="変換してクリップボードにコピー",
    command=copy_to_clipboard,
    width=28,
    height=2,
).pack(side="left", padx=8)

root.protocol("WM_DELETE_WINDOW", lambda: (save_settings(), root.destroy()))
root.mainloop()
