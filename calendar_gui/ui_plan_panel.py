"""선택한 날짜의 계획을 추가 / 조회 / 삭제하는 오른쪽 패널 위젯."""

import tkinter as tk
from tkinter import messagebox

from .models import date_key


class PlanPanel(tk.Frame):
    def __init__(self, master, store, on_change):
        """
        store: PlanStore 인스턴스
        on_change: 계획이 바뀌었을 때 호출 (달력을 다시 그리게 하기 위함)
        """
        super().__init__(master)
        self.store = store
        self.on_change = on_change

        # 현재 선택된 날짜 (year, month, day). 처음엔 선택 없음.
        self.current = None

        self._build()

    def _build(self):
        self.title_label = tk.Label(
            self, text="날짜를 선택하세요", font=("Malgun Gothic", 13, "bold")
        )
        self.title_label.pack(anchor="w", pady=(0, 8))

        # 계획 목록
        self.listbox = tk.Listbox(self, height=12, font=("Malgun Gothic", 11))
        self.listbox.pack(fill="both", expand=True)

        # 입력 + 추가 버튼
        input_row = tk.Frame(self)
        input_row.pack(fill="x", pady=8)

        self.entry = tk.Entry(input_row, font=("Malgun Gothic", 11))
        self.entry.pack(side="left", fill="x", expand=True)
        self.entry.bind("<Return>", lambda e: self.add_plan())

        tk.Button(input_row, text="추가", width=6, command=self.add_plan).pack(
            side="left", padx=(6, 0)
        )

        tk.Button(self, text="선택한 계획 삭제", command=self.delete_plan).pack(fill="x")

    # ---------- 외부에서 날짜가 선택되면 호출 ----------
    def set_date(self, year, month, day):
        self.current = (year, month, day)
        self.title_label.config(text=f"{year}년 {month}월 {day}일 계획")
        self.refresh_list()
        self.entry.focus_set()

    def refresh_list(self):
        """현재 날짜의 계획을 리스트박스에 다시 채운다."""
        self.listbox.delete(0, tk.END)
        if not self.current:
            return
        key = date_key(*self.current)
        for item in self.store.get(key):
            self.listbox.insert(tk.END, item)

    # ---------- 기능 ----------
    def add_plan(self):
        if not self.current:
            messagebox.showinfo("안내", "먼저 달력에서 날짜를 선택하세요.")
            return
        content = self.entry.get().strip()
        if not content:
            return
        key = date_key(*self.current)
        self.store.add(key, content)
        self.entry.delete(0, tk.END)
        self.refresh_list()
        self.on_change()

    def delete_plan(self):
        if not self.current:
            return
        selection = self.listbox.curselection()
        if not selection:
            messagebox.showinfo("안내", "삭제할 계획을 목록에서 선택하세요.")
            return
        index = selection[0]
        key = date_key(*self.current)
        self.store.remove(key, index)
        self.refresh_list()
        self.on_change()
