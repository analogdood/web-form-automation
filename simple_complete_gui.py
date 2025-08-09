#!/usr/bin/env python3
"""
Simple GUI focused on running ONLY the Complete Workflow.

- Select a CSV file
- Choose round selection (Auto from filename / Specify / Latest)
- Optional headless mode and keep-open option
- Start and watch logs
"""
from __future__ import annotations

import logging
import queue
import re
import threading
from pathlib import Path
import sys
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

# Ensure local imports work even in isolated mode
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from complete_toto_automation import CompleteTotoAutomation


class TkTextHandler(logging.Handler):
    """Logging handler that appends records into a tkinter Text widget safely."""

    def __init__(self, text: tk.Text, line_limit: int = 2000) -> None:
        super().__init__()
        self.text = text
        self.queue: queue.Queue[str] = queue.Queue()
        self.line_limit = line_limit
        # Start periodic flush
        self.text.after(200, self._poll)

    def emit(self, record: logging.LogRecord) -> None:
        try:
            msg = self.format(record)
            self.queue.put(msg + "\n")
        except Exception:
            pass

    def _poll(self) -> None:
        try:
            while True:
                msg = self.queue.get_nowait()
                self._append(msg)
        except queue.Empty:
            pass
        finally:
            self.text.after(200, self._poll)

    def _append(self, msg: str) -> None:
        self.text.configure(state=tk.NORMAL)
        self.text.insert(tk.END, msg)
        # Trim lines if over limit
        if int(self.text.index('end-1c').split('.')[0]) > self.line_limit:
            self.text.delete('1.0', '2.0')
        self.text.see(tk.END)
        self.text.configure(state=tk.DISABLED)


class CompleteWorkflowGUI:
    def __init__(self) -> None:
        self.root = tk.Tk()
        self.root.title("TotoKN - Complete Workflow")
        self.root.geometry("780x600")

        # State vars
        self.csv_path_var = tk.StringVar()
        self.round_mode_var = tk.StringVar(value="auto")  # auto | manual | latest
        self.round_manual_var = tk.StringVar()
        self.headless_var = tk.BooleanVar(value=False)
        self.keep_open_var = tk.BooleanVar(value=True)
        self.timeout_var = tk.IntVar(value=15)

        self._build_ui()
        self._configure_logging()

        self.worker = None  # type: threading.Thread | None
        self.running = False

    def _build_ui(self) -> None:
        pad = 10
        frm = ttk.Frame(self.root)
        frm.pack(fill=tk.BOTH, expand=True, padx=pad, pady=pad)

        # CSV selector
        csv_frame = ttk.LabelFrame(frm, text="CSVファイル")
        csv_frame.pack(fill=tk.X, padx=0, pady=(0, pad))
        ttk.Entry(csv_frame, textvariable=self.csv_path_var).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(8, 6), pady=8)
        ttk.Button(csv_frame, text="参照...", command=self._browse_csv).pack(side=tk.LEFT, padx=(0, 8), pady=8)

        # Round selection
        round_frame = ttk.LabelFrame(frm, text="ラウンド選択")
        round_frame.pack(fill=tk.X, padx=0, pady=(0, pad))
        rb1 = ttk.Radiobutton(round_frame, text="自動（CSVファイル名から）", value="auto", variable=self.round_mode_var, command=self._toggle_round_entry)
        rb2 = ttk.Radiobutton(round_frame, text="指定", value="manual", variable=self.round_mode_var, command=self._toggle_round_entry)
        rb3 = ttk.Radiobutton(round_frame, text="最新を使用", value="latest", variable=self.round_mode_var, command=self._toggle_round_entry)
        rb1.grid(row=0, column=0, sticky=tk.W, padx=8, pady=6)
        rb2.grid(row=0, column=1, sticky=tk.W, padx=8, pady=6)
        rb3.grid(row=0, column=2, sticky=tk.W, padx=8, pady=6)
        ttk.Label(round_frame, text="番号:").grid(row=1, column=0, sticky=tk.E, padx=(8, 2))
        self.round_entry = ttk.Entry(round_frame, textvariable=self.round_manual_var, width=12)
        self.round_entry.grid(row=1, column=1, sticky=tk.W, padx=(0, 8), pady=(0, 8))
        self._toggle_round_entry()

        # Options
        opt_frame = ttk.LabelFrame(frm, text="オプション")
        opt_frame.pack(fill=tk.X, padx=0, pady=(0, pad))
        ttk.Checkbutton(opt_frame, text="ヘッドレス（画面非表示）", variable=self.headless_var).grid(row=0, column=0, sticky=tk.W, padx=8, pady=8)
        ttk.Label(opt_frame, text="タイムアウト(s):").grid(row=0, column=1, sticky=tk.E, padx=(16, 4))
        ttk.Spinbox(opt_frame, from_=5, to=60, textvariable=self.timeout_var, width=6).grid(row=0, column=2, sticky=tk.W)
        ttk.Checkbutton(opt_frame, text="完了後にブラウザを閉じない", variable=self.keep_open_var).grid(row=0, column=3, sticky=tk.W, padx=(16, 8))

        # Controls
        ctrl_frame = ttk.Frame(frm)
        ctrl_frame.pack(fill=tk.X, padx=0, pady=(0, pad))
        self.start_btn = ttk.Button(ctrl_frame, text="開始", command=self._on_start)
        self.start_btn.pack(side=tk.LEFT, padx=(8, 6))
        ttk.Button(ctrl_frame, text="終了", command=self.root.destroy).pack(side=tk.LEFT)
        self.status_var = tk.StringVar(value="待機中")
        ttk.Label(ctrl_frame, textvariable=self.status_var).pack(side=tk.RIGHT, padx=8)

        # Logs
        log_frame = ttk.LabelFrame(frm, text="ログ")
        log_frame.pack(fill=tk.BOTH, expand=True)
        self.log_text = tk.Text(log_frame, wrap=tk.NONE, height=22, state=tk.DISABLED)
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

    def _configure_logging(self) -> None:
        logger = logging.getLogger()
        logger.setLevel(logging.INFO)
        fmt = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
        if not any(isinstance(h, logging.StreamHandler) for h in logger.handlers):
            sh = logging.StreamHandler()
            sh.setFormatter(fmt)
            logger.addHandler(sh)
        tkh = TkTextHandler(self.log_text)
        tkh.setFormatter(fmt)
        logger.addHandler(tkh)

    def _toggle_round_entry(self) -> None:
        mode = self.round_mode_var.get()
        state = tk.NORMAL if mode == "manual" else tk.DISABLED
        self.round_entry.configure(state=state)

    def _browse_csv(self) -> None:
        path = filedialog.askopenfilename(
            title="CSVファイルを選択",
            filetypes=[("CSV Files", "*.csv"), ("All Files", "*.*")],
        )
        if path:
            self.csv_path_var.set(path)

    @staticmethod
    def _extract_round_from_filename(csv_path: str) -> str | None:
        stem = Path(csv_path).stem
        m = re.search(r"(\d{4,5})", stem)
        return m.group(1) if m else None

    def _on_start(self) -> None:
        if self.running:
            return
        csv_path = self.csv_path_var.get().strip()
        if not csv_path:
            messagebox.showwarning("入力不足", "CSVファイルを選択してください。")
            return
        if not Path(csv_path).exists():
            messagebox.showerror("エラー", "CSVファイルが見つかりません。")
            return

        mode = self.round_mode_var.get()
        round_number: str | None
        if mode == "manual":
            rn = self.round_manual_var.get().strip()
            if not rn:
                messagebox.showwarning("入力不足", "ラウンド番号を入力するか、他のモードを選択してください。")
                return
            round_number = rn
        elif mode == "auto":
            rn = self._extract_round_from_filename(csv_path)
            round_number = rn  # may be None -> latest fallback
        else:  # latest
            round_number = None

        headless = bool(self.headless_var.get())
        timeout = int(self.timeout_var.get())
        keep_open = bool(self.keep_open_var.get())

        # Run in background thread
        self.running = True
        self.start_btn.configure(state=tk.DISABLED)
        self.status_var.set("実行中...")
        t = threading.Thread(target=self._run_workflow, args=(csv_path, round_number, headless, timeout, keep_open), daemon=True)
        self.worker = t
        t.start()

    def _run_workflow(self, csv_path: str, round_number: str | None, headless: bool, timeout: int, keep_open: bool) -> None:
        try:
            logging.info("Starting Complete Workflow...")
            automation = CompleteTotoAutomation(headless=headless, timeout=timeout, keep_browser_open=keep_open)
            ok = automation.execute_complete_workflow(csv_path, round_number)
            if ok:
                logging.info("✅ 完了: すべてのバッチが処理されました。")
                self.root.after(0, lambda: messagebox.showinfo("完了", "全バッチの処理が完了しました。ブラウザは開いたままです。" if keep_open else "全バッチの処理が完了しました。"))
            else:
                logging.error("❌ 失敗: ワークフローに失敗しました。ログを確認してください。")
                self.root.after(0, lambda: messagebox.showerror("失敗", "ワークフローに失敗しました。ログを確認してください。"))
        except Exception as e:
            logging.exception(f"Unexpected error: {e}")
        finally:
            self.root.after(0, self._on_finished)

    def _on_finished(self) -> None:
        self.running = False
        self.start_btn.configure(state=tk.NORMAL)
        self.status_var.set("完了")

    def run(self) -> None:
        self.root.mainloop()


if __name__ == "__main__":
    app = CompleteWorkflowGUI()
    app.run()
