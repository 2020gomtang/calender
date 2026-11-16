"""계획 데이터를 다루는 핵심 로직 (UI와 분리).

PlanStore 는 날짜별 계획을 메모리에 들고 있으면서,
추가/삭제/조회가 일어날 때마다 storage 를 통해 파일에 저장한다.
날짜 키는 항상 'YYYY-MM-DD' 문자열을 사용한다.
"""

from . import storage


def date_key(year: int, month: int, day: int) -> str:
    """연/월/일을 'YYYY-MM-DD' 형태의 키로 만든다."""
    return f"{year:04d}-{month:02d}-{day:02d}"


class PlanStore:
    def __init__(self):
        # { "2024-05-01": ["회의", "운동"], ... }
        self._plans = storage.load()

    def get(self, key: str) -> list:
        """해당 날짜의 계획 목록을 돌려준다 (없으면 빈 리스트)."""
        return list(self._plans.get(key, []))

    def has_any(self, key: str) -> bool:
        """해당 날짜에 계획이 하나라도 있는지."""
        return bool(self._plans.get(key))

    def add(self, key: str, content: str) -> None:
        """계획을 추가하고 저장한다."""
        content = content.strip()
        if not content:
            return
        self._plans.setdefault(key, []).append(content)
        storage.save(self._plans)

    def remove(self, key: str, index: int) -> None:
        """해당 날짜의 index 번째 계획을 삭제하고 저장한다."""
        items = self._plans.get(key)
        if not items:
            return
        if 0 <= index < len(items):
            items.pop(index)
            if not items:          # 그 날 계획이 모두 사라지면 키 자체를 제거
                del self._plans[key]
            storage.save(self._plans)

    def month_keys(self, year: int, month: int) -> set:
        """해당 연-월에 계획이 있는 날짜 키들의 집합."""
        prefix = f"{year:04d}-{month:02d}-"
        return {k for k in self._plans if k.startswith(prefix)}
