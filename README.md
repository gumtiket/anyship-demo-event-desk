# Event Desk · 모여봐요

동아리 모임을 골라 **신청 → 신청 기록 확인 → 취소**하는 FastAPI + SQLAlchemy ORM + PostgreSQL 앱입니다. 팀원이 개인 저장소를 fork하고 AnyShip의 분석·PR·배포 흐름을 시연할 수 있습니다.

이 저장소는 분석 전 원본입니다. 루트 Dockerfile과 /healthz는 아직 없고, 실제 비밀 대신 `dummy-secret-do-not-use`만 사용합니다. 배포하려면 먼저 AnyShip의 변경안을 검토·병합하세요. SQLAlchemy 모델과 신청·취소 기능은 완성된 상태이며 DB 저장 방식 변환은 하지 않습니다.

## 시연 순서

1. 개인 계정으로 fork합니다. GitHub App이 해당 저장소를 읽고 PR을 만들 수 있도록 허용합니다.
2. AnyShip에 fork URL을 연결하고 AI 분석을 실행합니다.
3. 코드와 배포 파일의 변경안을 보여주고 Draft PR을 생성합니다.
4. PR에서 **postgres → DATABASE_URL** 선언과 **release.migrate: python -m app.migrate**가 유지되는지 확인한 뒤 병합합니다.
5. 연결이 확인된 AWS 상시 실행 또는 온프레미스 환경을 선택해 배포합니다.
6. 공개 URL에서 `백엔드 번개 스터디`를 선택하고 가상 닉네임으로 신청합니다.
7. 남은 자리 감소·신청 기록을 보여주고 취소합니다. 새로고침해도 기록과 수량이 유지됩니다.

현재 PostgreSQL 자원 보존 수정인 팀 PR #75가 서비스에 반영되어 있어야 합니다. 기존 main만 사용하면 필요한 DB 선언과 초기화 명령이 빠질 수 있습니다. 앱 코드를 분석하는 것과 실제 컨테이너·원격 배포 검증은 별개입니다. 웹 분석은 자체 Docker 게이트를 실행하지 않습니다.

## 기능과 데이터

- 세 모임은 `python -m app.migrate`가 새 DB의 테이블을 만들면서 준비합니다.
- 초기화 명령을 반복해도 기존 신청을 지우거나 정원을 초기화하지 않습니다.
- 신청은 행사 행을 잠그고 정원·동일 모임 닉네임 중복을 확인한 뒤 ORM 트랜잭션으로 기록합니다.
- 취소는 기록을 삭제하지 않고 취소 상태로 바꾸며 자리를 한 번만 복원합니다.
- 접수 번호는 HMAC으로 만들고 DB에 보관합니다. 실제 로그인 서비스는 아니며, 시연용 신청 목록과 접수 정보는 참여자끼리 공유됩니다. 가상의 닉네임으로 사용하세요.
- 모든 실제 DB 접속 정보는 환경변수로 받습니다. 이 앱에 SQLite·파일 저장·외부 API·실제 키는 없습니다.

## 실행

분석·PR 병합 후 Dockerfile이 생기면 서비스를 통해 배포하거나 로컬의 별도 PostgreSQL DB에서 다음 순서로 실행합니다.

```bash
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
# DATABASE_URL과 분석 후 명세에서 요구하는 SECRET_KEY·LOG_LEVEL을 환경변수로 설정
.venv/bin/python -m app.migrate
PORT=8080 .venv/bin/python -m app.main
```

원본의 직접 실행 포트는 8000이고 로그 파일은 실행한 작업 디렉터리에 생깁니다. 원본·원본 DB를 보호하려면 로컬 시험도 복사본과 새 DB에서 진행하세요. 분석 후에는 PORT를 읽고 stdout으로 로그를 출력하는 변경안을 확인할 수 있습니다.

의존성은 시연 중 새 버전이 설치되지 않도록 고정했습니다. 기존 데이터 이전이나 스키마 변경 마이그레이션은 구현하지 않았습니다. `app.migrate`는 이 새 데모의 테이블 생성과 초기 모임 준비만 수행합니다.

검증 결과는 `VERIFICATION.md`에 기록합니다. 실제 AWS·온프레미스 성공에는 서비스의 SSH·DB·DNS·TLS 설정도 필요합니다.

MIT License. `jaedong29`의 개인 데모이며 팀 서비스 코드 변경은 포함하지 않습니다.
