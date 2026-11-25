"""달력 그리드 화면 위젯.

- 연/월 이동 버튼
- 날짜 버튼 그리드 (계획이 있는 날은 색으로 표시)
- 날짜를 클릭하면 바깥(main)에서 넘겨준 콜백을 호출한다.
"""

import calendar
import tkinter as tk
from datetime import date

from .models import date_key

WEEK_HEADERS = ["일", "월", "화", "수", "목", "금", "토"]


class CalendarView(tk.Frame):
    def __init__(self, master, store, on_date_selected):
        """
        store: PlanStore 인스턴스
        on_date_selected: 날짜를 클릭했을 때 호출할 함수 (year, month, day) 를 받는다.
        """
        super().__init__(master)
        self.store = store
        self.on_date_selected = on_date_selected

        today = date.today()
        self.year = today.year
        self.month = today.month
        self.selected_day = today.day

        self._build_header()
        self._build_grid_area()
        self.refresh()

    # ---------- 화면 구성 ----------
    def _build_header(self):
        header = tk.Frame(self)
        header.pack(fill="x", pady=(0, 8))

        tk.Button(header, text="◀", width=3, command=self.prev_month).pack(side="left")
        self.title_label = tk.Label(header, text="", font=("Malgun Gothic", 14, "bold"))
        self.title_label.pack(side="left", expand=True)
        tk.Button(header, text="▶", width=3, command=self.next_month).pack(side="right")

    def _build_grid_area(self):
        # 요일 헤더
        week_row = tk.Frame(self)
        week_row.pack(fill="x")
        for i, name in enumerate(WEEK_HEADERS):
            color = "red" if i == 0 else ("blue" if i == 6 else "black")
            tk.Label(
                week_row, text=name, width=5, fg=color,
                font=("Malgun Gothic", 10, "bold"),
            ).grid(row=0, column=i, padx=1, pady=1)

        # 날짜 버튼이 들어갈 영역
        self.grid_frame = tk.Frame(self)
        self.grid_frame.pack(fill="both", expand=True)

    # ---------- 월 이동 ----------
    def prev_month(self):
        if self.month == 1:
            self.year -= 1
            self.month = 12
        else:
            self.month -= 1
        self.selected_day = None
        self.refresh()

    def next_month(self):
        if self.month == 12:
            self.year += 1
            self.month = 1
        else:
            self.month += 1
        self.selected_day = None
        self.refresh()

    # ---------- 다시 그리기 ----------
    def refresh(self):
        """제목과 날짜 버튼들을 현재 연/월 기준으로 다시 그린다."""
        self.title_label.config(text=f"{self.year}년 {self.month}월")

        # 기존 버튼 제거
        for child in self.grid_frame.winfo_children():
            child.destroy()

        marked = self.store.month_keys(self.year, self.month)
        cal = calendar.Calendar(firstweekday=6)  # 일요일 시작

        for r, week in enumerate(cal.monthdayscalendar(self.year, self.month)):
            for c, day in enumerate(week):
                if day == 0:
                    tk.Label(self.grid_frame, text="", width=5, height=2).grid(
                        row=r, column=c, padx=1, pady=1
                    )
                    continue

                key = date_key(self.year, self.month, day)
                has_plan = key in marked

                bg = "#d7ecff" if has_plan else "#f5f5f5"
                if day == self.selected_day:
                    bg = "#2383e2"
                fg = "white" if day == self.selected_day else "black"

                btn = tk.Button(
                    self.grid_frame,
                    text=str(day),
                    width=5,
                    height=2,
                    bg=bg,
                    fg=fg,
                    relief="flat",
                    command=lambda d=day: self._select(d),
                )
                btn.grid(row=r, column=c, padx=1, pady=1)

    def _select(self, day):
        self.selected_day = day
        self.refresh()
        self.on_date_selected(self.year, self.month, day)
