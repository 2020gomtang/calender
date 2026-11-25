"""프로그램 시작점 - 전체 창을 조립한다.

실행: 프로젝트 루트(calender 폴더)에서
    python -m calendar_gui.main
"""

import tkinter as tk

from .models import PlanStore
from .ui_calendar import CalendarView
from .ui_plan_panel import PlanPanel


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("📆 캘린더 계획표")
        self.geometry("720x520")

        self.store = PlanStore()

        # 왼쪽: 달력 / 오른쪽: 계획 패널
        container = tk.Frame(self, padx=12, pady=12)
        container.pack(fill="both", expand=True)

        left = tk.Frame(container)
        left.pack(side="left", fill="both", expand=True)

        right = tk.Frame(container, width=280)
        right.pack(side="right", fill="both", padx=(16, 0))
        right.pack_propagate(False)

        # 오른쪽 패널 먼저 만들고, 달력에 "날짜 선택 시 패널에 알려주는" 콜백을 연결
        self.panel = PlanPanel(right, self.store, on_change=self._on_change)
        self.panel.pack(fill="both", expand=True)

        self.calendar = CalendarView(
            left, self.store, on_date_selected=self._on_date_selected
        )
        self.calendar.pack(fill="both", expand=True)

    def _on_date_selected(self, year, month, day):
        """달력에서 날짜를 클릭하면 오른쪽 패널에 전달한다."""
        self.panel.set_date(year, month, day)

    def _on_change(self):
        """계획이 추가/삭제되면 달력의 표시를 갱신한다."""
        self.calendar.refresh()


def main():
    App().mainloop()


if __name__ == "__main__":
    main()
