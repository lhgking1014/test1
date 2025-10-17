# 단청상회 (K-shoppingmall)

한국 전통 아이템을 판매하는 쇼핑몰의 Django 기반 백엔드/프론트 MVP입니다.

## 주요 기능

- 구글 비전 API 기반 상품 이미지 분석(자격증명 미지정 시 목업 응답)
- 이메일/구글 소셜 로그인 (`django-allauth`)
- 장바구니, 주문, Mock 결제(Visa/Mastercard, 네이버페이)
- 배송/CS 정책 및 관리자 워크플로 (Django Admin 커스터마이징)
- Celery를 사용한 비동기 작업(비전 분석, 이메일 발송)
- 국립중앙박물관 단청 키보드 감성의 Tailwind 템플릿

## 요구 사항

- Python 3.11+
- Redis (Celery 브로커)
- PostgreSQL (또는 `.env`에서 SQLite 설정 가능)
- Google Cloud Vision API 자격증명(JSON)

## 빠른 시작

```bash
cd K-shoppingmall
python -m venv .venv && source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

별도 쉘에서 Celery 워커를 실행합니다.

```bash
celery -A kshoppingmall worker -l info
```

## 구글 비전 파이프라인

1. 관리자 페이지에서 상품 이미지 등록 후 "Queue Google Vision analysis" 액션 실행
2. `catalog.tasks.run_vision_analysis` Celery 태스크가 실행되어 `ai_suggestions`에 후보가 저장
3. 후보 검수 후 상품명을 확정하고 `status`를 `active`로 전환

## 결제 (Mock)

- 카드 결제: 카드 번호/만료일/CCV 등 입력 → Luhn 체크 후 가짜 승인 번호 발급
- 네이버페이: Sandbox 플로우를 모사하여 승인 ID 발급
- 실제 PG 계약 이후 `payments.gateway.PaymentGateway`를 교체하여 확장합니다.

## 이메일

- Gmail App Password를 `.env`에 설정
- 주문/인증 관련 이메일 템플릿은 `core` 앱에서 확장 예정

## 배송 & CS

- 50,000원 이상 무료 배송 / 기본 3,000원 배송비
- 결제 후 2~3영업일 이내 출고, 반품/교환 7일 이내 신청 가능
- 고객센터: 월~금 10:00~18:00, support@k-shoppingmall.kr / 02-1234-5678

## 관리자 워크플로

1. 상품 이미지 등록 → 비전 분석 결과 검토 → 상품명/가격/재고 확정
2. 주문 접수 → Mock 결제 확인 → 송장 입력 → 고객 알림 발송
3. 반품/교환 요청 처리 및 재고/환불 반영
4. 월별 판매/결제 통계 확인 (추후 대시보드 확장)

## 테스트 데이터

`K-shoppingmall/data` 폴더에는 전통 아이템 이미지 샘플이 포함되어 있으며, 비전 파이프라인 검증용으로 사용할 수 있습니다.

