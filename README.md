# 한국금거래소 시세조회 📊

한국금거래소(KoreaGoldX) API를 활용한 실시간 귀금속 시세 조회 데스크톱 애플리케이션

## ✨ 주요 기능

- **실시간 시세 조회**: 순금, 18K, 14K, 백금, 은 시세 자동 갱신 (기본 10초)
- **가격 변동 표시**: 등락률 및 등락폭 색상 표시
- **커스텀 설정**: 화면 텍스트, 업데이트 간격, 항목별 표시/숨김 설정

## 📋 시스템 요구사항

- Python 3.7 이상
- Windows / macOS / Linux
- 인터넷 연결 (API 호출용)

## 🚀 설치 방법

### 1. 의존성 패키지 설치

```bash
pip install -r requirements.txt
```

### 2. 실행

```bash
python main.py
```

## 📖 사용 방법

### 기본 실행

프로그램을 실행하면 자동으로 한국금거래소 API에서 시세를 가져와 화면에 표시합니다.

```bash
python main.py
```

### 관리자 모드

1. 상단의 **⚙** 버튼을 클릭하여 관리자 모드 활성화
2. 각 항목의 **Hide** 버튼으로 특정 시세 숨김/표시
3. **설정** 버튼으로 커스텀 설정 다이얼로그 열기

### 설정 변경

관리자 모드에서 **설정** 버튼을 클릭하면 다음 항목을 변경할 수 있습니다:

- 제목 텍스트
- 매수/매도 헤더 텍스트
- Hide 버튼 텍스트
- 에러 메시지 텍스트
- 업데이트 간격 (초)
- API 에러 타임아웃 (분)
- 각 항목별 노트 (추가 정보 표시)

설정은 자동으로 `settings.json` 파일에 저장됩니다.

## ⚙️ 설정 파일 (settings.json)

설정을 변경하면 자동으로 생성되므로 사용자가 json을 직접 수정할 필요는 없습니다.

참고로 다음과 같은 구조 및 기본값을 가집니다:

```json
{
  "hidden_buy": [],           // 숨길 매수 항목 리스트 (예: ["Gold18k-3.75g"])
  "hidden_sell": [],          // 숨길 매도 항목 리스트
  "custom_texts": {           // 화면에 표시되는 텍스트 커스터마이징
    "title": "한국금거래소 시세",
    "buy_header": "내가 살 때 (VAT포함)",
    "sell_header": "내가 팔 때 (금방금방 앱 기준)",
    "hide_text": "제품시세적용",
    "error_message": "일시적 조회 오류",
    "gold_buy_note": "",
    "gold_sell_note": "",
    "gold18k_buy_note": "",
    "gold18k_sell_note": "",
    "gold14k_buy_note": "",
    "gold14k_sell_note": "",
    "platinum_buy_note": "",
    "platinum_sell_note": "(자사백금바기준)",
    "silver_buy_note": "",
    "silver_sell_note": "(자사실버바기준)"
  },
  "update_interval": 10,      // 자동 업데이트 간격 (초)
  "error_timeout": 3          // API 에러 표시 타임아웃 (분)
}
```

## 🔧 API 정보

이 애플리케이션은 한국금거래소(KoreaGoldX)의 API를 사용합니다.

- [GET] `https://www.koreagoldx.co.kr/api/main`

## 📝 TODO

**개발 환경 및 빌드 환경은 현재 미구성 상태입니다.**
