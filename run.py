"""exe 빌드 / 실행용 진입점.

실행:        python run.py
exe 빌드:    pyinstaller --onefile --windowed --name CalendarApp run.py
"""

from calendar_gui.main import main

if __name__ == "__main__":
    main()
