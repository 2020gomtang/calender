"""계획 데이터를 JSON 파일로 저장하고 불러오는 역할만 담당한다."""

import json
import os
import sys


def _base_dir() -> str:
    """plans.json 을 저장할 폴더를 정한다.

    - PyInstaller 로 만든 exe 로 실행될 때(sys.frozen): exe 파일이 있는 폴더.
      (--onefile exe 는 임시 폴더에 풀리므로, 그 임시 폴더가 아니라
       실제 exe 옆에 저장해야 재실행해도 계획이 유지된다.)
    - 일반 파이썬으로 실행될 때: 이 패키지 폴더.
    """
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


DATA_FILE = os.path.join(_base_dir(), "plans.json")


def load() -> dict:
    """저장된 계획을 불러온다.

    반환 형태: { "2024-05-01": ["회의", "운동"], ... }
    파일이 없거나 읽지 못하면 빈 dict 를 돌려준다.
    """
    if not os.path.exists(DATA_FILE):
        return {}
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, dict):
                return data
            return {}
    except (json.JSONDecodeError, OSError):
        return {}


def save(plans: dict) -> None:
    """계획 전체를 파일에 저장한다."""
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(plans, f, ensure_ascii=False, indent=2)
