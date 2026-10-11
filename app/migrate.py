from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import Base, engine
from app.models import Event


def main() -> None:
    Base.metadata.create_all(engine)
    events = [
        (
            1,
            "백엔드 번개 스터디",
            "STUDY",
            "API 설계 이야기부터 작은 코드 리뷰까지. 함께 배우는 30분.",
            8,
        ),
        (
            2,
            "보드게임 라운지",
            "PLAY",
            "처음 만난 사이도 금세 친해지는 한 판. 가볍게 놀러 오세요.",
            6,
        ),
        (
            3,
            "포트폴리오 피드백",
            "TALK",
            "만들고 있는 프로젝트를 소개하고 서로의 생각을 나눠요.",
            4,
        ),
    ]
    with Session(engine) as session, session.begin():
        for identifier, title, category, description, capacity in events:
            if session.scalar(select(Event.id).where(Event.id == identifier)) is None:
                session.add(
                    Event(
                        id=identifier,
                        title=title,
                        category=category,
                        description=description,
                        capacity=capacity,
                        occupied=0,
                    )
                )
    print("Event Desk schema and demo events are ready.")


if __name__ == "__main__":
    main()
