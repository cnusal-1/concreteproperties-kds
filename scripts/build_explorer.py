"""대화형 탐색기 `docs/_static/explorer.html` 를 만든다.

`explorer_data.py` 가 계산한 JSON 을 `explorer_template.html` 의 자리표시자에
그대로 끼워 넣어, 외부 파일 없이 혼자 도는 한 장짜리 페이지로 만든다. 정적
호스팅과 오프라인 열람 모두를 위해서다.

실행:
    python scripts/explorer_data.py      # 값 계산 (오래 걸린다)
    python scripts/build_explorer.py     # 페이지 조립
"""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "scripts" / "explorer_data.json"
TEMPLATE = ROOT / "scripts" / "explorer_template.html"
OUT = ROOT / "docs" / "_static" / "explorer.html"

PLACEHOLDER = "/*__DATA__*/"


def main() -> int:
    """자리표시자에 데이터를 넣어 페이지를 쓴다.

    Returns:
        종료 코드
    """
    if not DATA.exists():
        print(f"{DATA} 가 없다. 먼저 scripts/explorer_data.py 를 실행한다.")
        return 1

    html = TEMPLATE.read_text(encoding="utf-8")
    if PLACEHOLDER not in html:
        print(f"{TEMPLATE} 에서 {PLACEHOLDER} 를 찾지 못했다.")
        return 1

    html = html.replace(PLACEHOLDER, DATA.read_text(encoding="utf-8"), 1)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(html, encoding="utf-8")
    print(f"생성  {OUT.relative_to(ROOT)}  ({OUT.stat().st_size / 1024:.0f} KB)")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
