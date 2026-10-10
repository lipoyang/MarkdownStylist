import json
import re
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path

import requests
from bs4 import BeautifulSoup


# 設定ファイル（スクリプトと同じフォルダ）
CONFIG_FILE = Path(__file__).with_name("dlpp.json")

# 前回の設定を読み込む
def load_config():
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return {}


# 現在の設定を保存する
def save_config():
    config = {
        "prototype_id": prototype_id_var.get(),
        "output_dir": output_dir_var.get(),
    }
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
    except OSError as e:
        messagebox.showwarning(
            "設定保存エラー",
            f"設定を保存できませんでした。\n{e}"
        )


# 出力先フォルダを選択する
def choose_output_dir():
    initial_dir = output_dir_var.get() or str(Path.home())

    directory = filedialog.askdirectory(
        title="出力先フォルダを選択",
        initialdir=initial_dir,
        mustexist=True,
    )

    if directory:
        output_dir_var.set(directory)
        save_config()


# 作品ページを取得して2つのMarkdownファイルを保存する
def download_files():
    prototype_id = prototype_id_var.get().strip()
    output_dir = output_dir_var.get().strip()

    if not prototype_id or not re.fullmatch(r"\d+", prototype_id):
        messagebox.showerror(
            "入力エラー",
            "作品番号を数字で入力してください。"
        )
        return

    if not output_dir or not Path(output_dir).is_dir():
        messagebox.showerror(
            "入力エラー",
            "有効な出力先フォルダを選択してください。"
        )
        return

    save_config()

    # 二重実行を防止
    download_button.config(state="disabled")
    status_var.set("作品ページを取得しています...")

    def worker():
        try:
            url = f"https://protopedia.net/prototype/{prototype_id}"

            response = requests.get(
                url,
                timeout=30,
                headers={"User-Agent": "Mozilla/5.0"},
            )
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")

            system_description = soup.find(
                "input", id="systemDescription"
            )
            free_comment = soup.find(
                "input", id="freeComment"
            )

            if system_description is None:
                raise ValueError(
                    'id="systemDescription" が見つかりません。'
                )

            if free_comment is None:
                raise ValueError(
                    'id="freeComment" が見つかりません。'
                )

            value_a = system_description.get("value", "")
            value_b = free_comment.get("value", "")

            destination = Path(output_dir)
            file_a = destination / f"{prototype_id}_A.md"
            file_b = destination / f"{prototype_id}_B.md"

            # 改行コードを変換せずに保存
            with open(file_a, "w", encoding="utf-8", newline="") as f:
                f.write(value_a)

            with open(file_b, "w", encoding="utf-8", newline="") as f:
                f.write(value_b)

            root.after(
                0,
                lambda: finish_success(file_a, file_b)
            )

        except Exception as e:
            root.after(
                0,
                lambda error=str(e): finish_error(error)
            )

    threading.Thread(target=worker, daemon=True).start()


# 完了メッセージ
def finish_success(file_a, file_b):
    download_button.config(state="normal")
    status_var.set("")

    messagebox.showinfo(
        "完了",
        f"次の2ファイルを保存しました。\n\n"
        f"{file_a}\n{file_b}"
    )


# エラーメッセージ
def finish_error(error):
    download_button.config(state="normal")
    status_var.set("")

    messagebox.showerror(
        "エラー",
        f"取得または保存に失敗しました。\n\n{error}"
    )


# ---------- GUI ----------

root = tk.Tk()
root.title("ProtoPedia Markdown取得")
root.resizable(False, False)

config = load_config()

prototype_id_var = tk.StringVar(
    value=config.get("prototype_id", "")
)
output_dir_var = tk.StringVar(
    value=config.get("output_dir", str(Path.home()))
)
status_var = tk.StringVar(value="")

frame = ttk.Frame(root, padding=16)
frame.grid(row=0, column=0, sticky="nsew")
frame.columnconfigure(1, weight=1)

# 作品番号
ttk.Label(frame, text="作品番号：").grid(
    row=0, column=0, sticky="w", pady=6
)
prototype_entry = ttk.Entry(
    frame, textvariable=prototype_id_var, width=32
)
prototype_entry.grid(
    row=0, column=1, columnspan=2, sticky="ew", pady=6
)

# 出力先
ttk.Label(frame, text="出力先：").grid(
    row=1, column=0, sticky="w", pady=6
)
output_entry = ttk.Entry(
    frame, textvariable=output_dir_var, width=32
)
output_entry.grid(
    row=1, column=1, sticky="ew", pady=6
)
ttk.Button(
    frame, text="参照...", command=choose_output_dir
).grid(row=1, column=2, padx=(6, 0), pady=6)

# 実行ボタン
download_button = ttk.Button(
    frame, text="取得・保存", command=download_files
)
download_button.grid(
    row=2, column=0, columnspan=3, sticky="ew", pady=(12, 8)
)

# ステータス
ttk.Label(
    frame, textvariable=status_var, wraplength=380
).grid(row=3, column=0, columnspan=3, sticky="w", pady=4)

root.protocol("WM_DELETE_WINDOW", lambda: (save_config(), root.destroy()))

prototype_entry.focus_set()
root.mainloop()
