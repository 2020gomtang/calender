"""계획 데이터를 JSON 파일로 저장하고 불러오는 역할만 담당한다."""

import json
import os

# 이 패키지 폴더 안에 plans.json 을 저장한다.
DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "plans.json")


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
