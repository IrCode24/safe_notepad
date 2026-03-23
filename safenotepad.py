#========================================================================================
#program infomation
#----------------------------------------------------------------------------------------
# 名  称         ： safenotepad.py
# 概  要         ： テキストを間違って消さずにコピペできるメモ帳
# 必要ライブラリ　： tkinter, filedialog, messagebox, json, os, sys, tkinter.font  
# 実行例         ： Python3.14      safenotepad.py <c:\users\user\python\safe_notepad>
# 作成者　　　　　： IrCode24
# 作成日（再現日）： 2026-03-15
# varsion        : 1.0.0
#========================================================================================

__version__ = "1.0.0"

import tkinter as tk
from tkinter import filedialog, messagebox
import tkinter.font as tkfont
import json
import os
import sys

APP_NAME = "SafeNotepad"


#----------------------------------------------------------------------------
#SafeNotepad 用の保存フォルダ（AppData\Local\SafeNotepad）を取得し、なければ作る
#----------------------------------------------------------------------------
def get_appdata_dir():
    """AppData\Local\SafeNotepad のパスを返す（なければ作成）"""
    local_appdata = os.getenv("LOCALAPPDATA") #パスの取得
    if not local_appdata:
        # 万一取得できない場合はカレントディレクトリにフォールバック(予備ルート)
        local_appdata = os.getcwd()

    app_dir = os.path.join(local_appdata, APP_NAME)    #「local_appdata」と「APP_NAME」を結合
    os.makedirs(app_dir, exist_ok=True)
    return app_dir


def get_settings_path():
    """settings.json のフルパス"""
    return os.path.join(get_appdata_dir(), "setting.json")


def resource_path(relative_path: str) -> str:
    """
    PyInstaller で固めた exe でも、通常の Python 実行でも
    同じようにリソースファイル（アイコンなど）にアクセスできるようにする。
    """
    if hasattr(sys, "_MEIPASS"):
        base_path = sys._MEIPASS  # PyInstaller 展開先
    else:
        base_path = os.path.abspath(os.path.dirname(__file__))
    return os.path.join(base_path, relative_path)

#+++++++++++++++++++
# SafeNotepad クラス
#+++++++++++++++++++
class SafeNotepad:
    #####################################
    ### テキストフォントのデフォルト設定 ###
    DEFAULT_SETTINGS = {"family":"Meiryo", "size":24}

    #########################################
    ### サブメニューフォントのデフォルト設定 ###
    MENU_FONT = ("Meiryo", 12)

    ##################################
    ### ダークモードのデフォルト設定 ###
    DARK_MODE = False

    #++++++++++++++++++++
    # initialize関数
    #++++++++++++++++++++
    def __init__(self, root):
        self.root = root
        self.root.title(f"安全メモ帳（編集ロック付き）v{__version__}")


        #########################################################
        ### ウィンドウアイコン設定（存在しなくてもエラーにしない） ###
        icon_path = resource_path("SN.ico")
        if os.path.exists(icon_path):
            try:
                self.root.iconbitmap(icon_path)
            except Exception:
                pass
       
        ##############################
        ### ショートカットキーの設定 ###
        self.root.bind("<Control-s>", lambda event: self.save_file())
        self.root.bind("<Control-S>", lambda event: self.save_file())  # 大文字対応（環境による）

        self.root.bind("<Control-Shift-S>", lambda event: self.save_file_as())
        self.root.bind("<Control-Shift-s>", lambda event: self.save_file_as())

        self.root.bind("<Control-o>", lambda event: self.open_file())
        self.root.bind("<Control-O>", lambda event: self.open_file())

        self.root.bind("<Control-n>", lambda event: self.new_window())
        self.root.bind("<Control-N>", lambda event: self.new_window())

        self.root.bind("<Control-q>", lambda event: self.quit_app())
        self.root.bind("<Control-Q>", lambda event: self.quit_app())


        ##########################
        ### 編集モードの状態設定 ###
        self.edit_mode = False

        ##################################
        ### 現在開いているファイル名設定 ###
        self.current_file = None

        ##########################
        ### 内容が変更有無の設定 ###
        self.modified = False


        ########################
        ### Text用フォント作成###
        self.font = tkfont.Font(**self.DEFAULT_SETTINGS) 
            #self.font = tkfont.Font(**self.settings)
            #で辞書からフォントを作り
            #self.text.configure(font=self.font)
            #でTextに適用する

        ##########################################################
        ### 閉じる前の確認設定（×ボタンで確認ダイアログを出す処理） ###
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
            # ◇protocol()
            # Tkinter の protocol() は、ウィンドウマネージャ（OS側のウィンドウ管理）に対して
            #「特定のイベントが起きたらこの関数を呼んで」と登録する仕組み。
            # ◇WM_DELETE_WINDOW
            # これは OS が送ってくるイベント名。「Windows の × ボタン」が
            # 押されたときに発生するイベントが WM_DELETE_WINDOW。

        #######################
        ### メニューバー設定 ###
        menubar = tk.Menu(root)
        root.config(menu=menubar)
            #　root ウィンドウに属するメニューバーを作る。

        ##########################
        ### ファイルメニュー設定 ###
        filemenu = tk.Menu(menubar, tearoff=0, font = self.MENU_FONT)
            #　Tkinter のメニューはデフォルトで「切り離し線」が付くので普通は tearoff=0 を指定する。
        menubar.add_cascade(label="ファイル", menu=filemenu)
        filemenu.add_command(label="新規", command=self.new_window)
        filemenu.add_command(label="開く", command=self.open_file)
        filemenu.add_command(label="上書き保存", command=self.save_file)
        filemenu.add_command(label="名前を付けて保存", command=self.save_as)

        ##########################
        ### フォントメニュー設定 ###
        font_menu = tk.Menu(menubar, tearoff=0, font = self.MENU_FONT)
        menubar.add_cascade(label="文字サイズ", menu=font_menu)
        font_menu.add_command(label="スライダーで調整", command=self.open_font_slider)

        #####################################
        ### 表示メニュー（ダークモード）設定 ###
        view_menu = tk.Menu(menubar, tearoff=0, font=self.MENU_FONT)
        menubar.add_cascade(label="表示", menu=view_menu)
        self.dark_mode_var = tk.BooleanVar(value = self.DARK_MODE)
            # BooleanVar
            # チェックボックスやメニューの ON/OFF を管理するための特別な変数。
        view_menu.add_checkbutton(
            label="ダークモード",
            onvalue=True,
            offvalue=False,
            variable=self.dark_mode_var,
            command=self.toggle_dark_mode
        )

        ################################
        ### 編集モードボタンエリア設定 ###
        self.button_frame = tk.Frame(root)
        self.button_frame.pack(fill="x")
            #フレームを横いっぱいに広げて配置
        self.edit_button = tk.Button(
            self.button_frame,
            text="編集モードにする",
            command=self.toggle_edit_mode
        )
        self.edit_button.pack(side="left", padx=5, pady=5)

        #############################################
        ### テキストエリア設定（初期は読み取り専用） ###
        self.text = tk.Text(root, height=20, width=60, font=self.font)
        self.text.pack(fill="both", expand=True)
        self.text.config(state="disabled")
        
        #######################
        ### 変更検知イベント ###
        self.text.bind("<<Modified>>", self.on_modified)

        #################
        ### テーマ適用 ###
        self.apply_theme()


    #+++++++++++++++++
    # 設定ファイル関数
    #+++++++++++++++++
    def load_settings(self):
        """AppData の settings.json から設定を読み込む（壊れていたら復旧）"""
        default = {
            "font_size": 14,
            "dark_mode": False
        }

        settings_path = get_settings_path()
        if not os.path.exists(settings_path):
            return default

        try:
            with open(settings_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            # 足りないキーはデフォルトで補完
            merged = {**default, **data}
            return merged
        except Exception:
            # 壊れていた場合はバックアップして復旧
            try:
                backup_path = settings_path + ".bak"
                os.replace(settings_path, backup_path)
            except Exception:
                pass
            return default
    # -------------------------
    # 設定ファイル保存
    # -------------------------
    def save_settings():
        """AppData の settings.json に設定を保存"""
        settings = {
            "font_size": self.font['size'],
            "dark_mode": bool(self.dark_mode_var.get())
        }
        settings_path = get_settings_path()
        try:
            with open(settings_path, "w", encoding="utf-8") as f:
                json.dump(settings, f, ensure_ascii=False, indent=2)
        except Exception as e:
            messagebox.showerror("エラー", f"設定を保存できませんでした:\n{e}")

    # -------------------------
    # ダークモード
    # -------------------------
    def apply_theme(self):
        dark = bool(self.dark_mode_var.get())

        if dark:
            bg = "#1e1e1e"
            fg = "#ffffff"
            text_bg = "#252526"
            text_fg = "#ffffff"
            button_bg = "#3c3c3c"
            button_fg = "#ffffff"
        else:
            bg = "#f0f0f0"
            fg = "#000000"
            text_bg = "#ffffff"
            text_fg = "#000000"
            button_bg = "#e0e0e0"
            button_fg = "#000000"

        # ウィンドウ背景
        self.root.config(bg=bg)

        # ボタン
        self.button_frame.config(bg=bg)
        self.edit_button.config(bg=button_bg, fg=button_fg)

        # Text
        self.text.config(bg=text_bg, fg=text_fg, insertbackground=fg)

    def toggle_dark_mode(self):
        self.apply_theme()
        self.save_settings()

    ############################
    # フォントスライダー
    ############################
    def open_font_slider(self):
            # Tkinter には2種類のウィンドウがある。
            # tk.Tk()       ⇒ メインウィンドウ（アプリの本体）
            # tk.Toplevel() ⇒ サブウィンドウ（設定画面・ダイアログなど）
            # Toplevel を使うと、メインウィンドウとは別の独立したウィンドウが開く。
        slider_win = tk.Toplevel(self.root)  # ※self.root ⇒ 親ウインドウ
        slider_win.title("文字サイズの調整")
        slider_win.geometry("300x120")

        current_size = self.font['size']
            # self.font['size'] ⇒
            # 現在のサイズ（数値）を取り出してスライダーの現在のフォントサイズからスタート

        label = tk.Label(slider_win, text=f"現在のサイズ: {current_size} pt")
        label.pack(pady=5)
            # pack() ⇒ ウィジェットを配置するメソッド
            # pady=5 ⇒ 上下に 5px の余白をつける
        slider = tk.Scale(
            slider_win,
            from_=8, to=40,
            orient="horizontal",
            length=250,
            command=lambda v: self.update_font_size(v, label)
        )
            # slider = tk.Scale() ⇒ スライダーを作る
            #   slider_win ⇒ 親ウインドウ、 from_=8 ⇒ 最小値 8pt、 to=40 ⇒ 40pt
            #   orient="horizontal" ⇒ 横向きスライダー、 length=250 ⇒ 長さ250px
            #   command=lambda v: self.update_font_size(v, label) ⇒ スライダーを動かしたときに呼ばれる関数

            # ※Tkinter の Scale（スライダー）は、command に「引数1つだけの関数」を渡す仕様になっている。
            #     例：command=関数(値)
            # update_font_sizeに引数を２つ渡したいためにlambdaを使用する。
            
            # lambdaについて ***defを使わず名前のない小さな関数（無名関数）を、その場で作るための構文）***
            #   Tkinter が渡してくる値（v）を受け取り label も一緒に渡す"橋渡し"をしている。
            #   lambdaの構文 ⇒ lambd 引数: 戻り値       引数を取り出す場合は--- f = lambda 引数: 戻り値(x*2)など
        slider.set(current_size)
        slider.pack(pady=5)

    def update_font_size(self, value, label=None):
        size = int(value)
        self.font.configure(size=size)
            # size= ⇒ Font.configure のオプション名（固定の文字列）
            # size  ⇒ 変数（ローカル変数）
            # 別例　self.font.configure(size=20)

            # configure(コンフィギュア)＝設定する/構成するの意味
            # configure(正式) = config(短縮形) どちらを使っても大丈夫
        if label:
            label.config(text=f"現在のサイズ: {size} pt")

        #self.save_settings()

    # -------------------------
    # 編集モード切り替え
    # -------------------------
    def toggle_edit_mode(self):
        if self.edit_mode:
            self.text.config(state="disabled")
            self.edit_button.config(text="編集モードにする")
            self.edit_mode = False
        else:
            self.text.config(state="normal")
            self.edit_button.config(text="編集を終了する")
            self.edit_mode = True

    # -------------------------
    # 内容が変更されたとき
    # -------------------------
    def on_modified(self, event=None):
        if not self.modified:
            self.modified = True
            title = self.root.title()
            if not title.endswith("*"):
                self.root.title(title + " *")
        self.text.edit_modified(False)

    # -------------------------
    # ファイルを開く
    # -------------------------
    def open_file(self):
        path = filedialog.askopenfilename(
            filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")]
        )
        if not path:
            return

        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception as e:
            messagebox.showerror("エラー", f"ファイルを開けませんでした:\n{e}")
            return

        self.text.config(state="normal")
        self.text.delete("1.0", tk.END)
        self.text.insert("1.0", content)
        self.text.config(state="disabled")

        self.edit_mode = False
        self.edit_button.config(text="編集モードにする")

        self.current_file = path
        self.modified = False
        self.root.title(f"安全メモ帳（編集ロック付き） - {path}")

    # -------------------------
    # 上書き保存
    # -------------------------
    def save_file(self):
        if self.current_file is None:
            self.save_as()
            return

        try:
            was_locked = not self.edit_mode
            if was_locked:
                self.text.config(state="normal")

            content = self.text.get("1.0", tk.END)
            with open(self.current_file, "w", encoding="utf-8") as f:
                f.write(content)

            if was_locked:
                self.text.config(state="disabled")

            self.modified = False
            self.root.title(f"安全メモ帳（編集ロック付き） - {self.current_file}")
            messagebox.showinfo("保存", "上書き保存しました。")

        except Exception as e:
            messagebox.showerror("エラー", f"保存できませんでした:\n{e}")

    # -------------------------
    # 名前を付けて保存
    # -------------------------
    def save_as(self):
        path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")]
        )
        if not path:
            return

        try:
            was_locked = not self.edit_mode
            if was_locked:
                self.text.config(state="normal")

            content = self.text.get("1.0", tk.END)
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)

            if was_locked:
                self.text.config(state="disabled")

            self.current_file = path
            self.modified = False
            self.root.title(f"安全メモ帳（編集ロック付き） - {path}")
            messagebox.showinfo("保存", "保存しました。")

        except Exception as e:
            messagebox.showerror("エラー", f"保存できませんでした:\n{e}")

    # -------------------------
    # 新しいファイルを開く
    # -------------------------
    def new_window(self):
        new_root = tk.Tk()
        SafeNotepad(new_root)
        new_root.mainloop()

    # -------------------------
    # 閉じる前の確認
    # -------------------------
    def on_closing(self):
        was_locked = not self.edit_mode
        if was_locked:
            self.text.config(state="normal")

        content = self.text.get("1.0", tk.END).strip()

        if was_locked:
            self.text.config(state="disabled")

        if content == "":
            self.root.destroy()
            return

        if self.modified:
            result = messagebox.askyesnocancel("終了確認", "保存しますか？")
            if result is None:
                return
            if result:
                self.save_file()

        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    #インスタンス化
    app = SafeNotepad(root)
    root.mainloop()