(label-contributing)=
# 기여 안내

이 저장소에 관심을 가져 주셔서 감사합니다. 오픈소스이며, 어떤 형태의 기여도
환영합니다.

## 기여할 수 있는 것

### 기준 대조

가장 도움이 되는 기여입니다. 이 저장소의 계수와 조문 번호는
[검증 대조표](user_guide/design_codes/kds.md#기준-값-출처와-검증)에 정리되어
있습니다. KDS 개정에 따라 값이 바뀌었거나 조문 해석이 잘못되었다면 이슈로
알려 주십시오. 다음을 함께 적어 주시면 확인이 빠릅니다.

- 해당 조문 번호와 판 (예: KDS 14 20 22 : 2022, 4.2.1(2))
- 기준의 값과 이 저장소의 값
- 가능하면 손계산 예

### 버그 신고

- 재현 가능한 최소 예제
- 기대한 결과와 실제 결과
- `concreteproperties` 와 Python 버전

### 기능 요청

구현되지 않은 KDS 조문(2방향 슬래브, 스트럿-타이, 뚫림전단 등)이 필요하면
어떤 설계 상황에서 쓰이는지와 함께 요청해 주십시오.

## 개발 환경

```shell
git clone <저장소 주소>
cd concreteproperties-kds

python -m venv .venv
source .venv/bin/activate

pip install -e ".[dev,docs]"
```

## 검사

바꾼 뒤에는 다음 세 가지를 모두 통과해야 합니다.

```shell
# 시험
PYTHONPATH=src python -m pytest tests/ -q

# 정적 검사
ruff check src tests examples --select E,F,W,I,UP,B,SIM

# 예제 실행
cd examples && for f in *.py; do PYTHONPATH=../src:. python "$f" > /dev/null; done
```

## 설계식을 고칠 때

설계식이나 계수를 바꾸는 기여는 다음을 함께 갖춰야 합니다.

1. **조문 근거** — docstring 에 `KDS 14 20 xx 4.x.x, 식 (x.x-x)` 형태로 표기
2. **시험** — 조문의 식을 손계산으로 대조하는 시험
3. **문서 갱신** — 해당 모듈의 문서와
   [검증 대조표](user_guide/design_codes/kds.md#기준-값-출처와-검증)

계수는 각 모듈 상단의 상수·표에 모아 두었으니 그곳만 고치면 됩니다.

| 모듈 | 편집 대상 |
|---|---|
| `kds.py` | `STRESS_BLOCK_*`, `ES`, `PHI_*`, `ALPHA_MAX_*` |
| `loads.py` | `LOAD_COMBINATIONS` |
| `shear.py` | `PHI_SHEAR`, `S_MAX_ABS`, `S_MAX_ABS_CLOSE` |
| `serviceability.py` | `CREEP_FACTOR`, `MINIMUM_THICKNESS_RATIO`, `DEFLECTION_LIMIT`, `KAPPA_CR_*` |
| `durability.py` | `EXPOSURE_REQUIREMENTS` |
| `detailing.py` | `BAR_PROPERTIES`, `MINIMUM_COVER`, `LDB_FACTOR`, `DEVELOPMENT_TABLE_FACTOR` |
| `slender.py` | `PHI_K` |
| `psc.py` | `EPS_Y_PSC`, `EPS_TL_PSC`, `GAMMA_P`, `CRACK_CLASS_LIMIT` |

## 문서

문서는 마크다운(MyST)으로 쓰고, 예제 노트북은 `scripts/build_notebooks.py` 로
생성합니다. 노트북을 직접 고치지 말고 생성 스크립트를 고친 뒤 다시 생성하십시오.

```shell
cd scripts
python build_notebooks.py --run     # 생성 후 실행하여 출력 저장

cd ../docs
make html                           # _build/html/index.html
```

## 코드 스타일

- 줄 길이 88자
- Google 스타일 docstring, **한글**로 작성
- 설계식에는 반드시 KDS 조문과 식 번호를 표기
- 공개 함수·클래스에는 `Args`, `Returns`, `Raises` 를 모두 기술

## 행동 강령

이 저장소에 참여하는 모든 사람은 [행동 강령](codeofconduct.md)을 따릅니다.
