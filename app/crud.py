from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app import models, schemas


def list_hcps(db: Session) -> list[models.HCP]:
    stmt = select(models.HCP).order_by(models.HCP.full_name)
    return list(db.scalars(stmt).all())


def get_hcp(db: Session, hcp_id: int) -> models.HCP | None:
    stmt = (
        select(models.HCP)
        .options(selectinload(models.HCP.interactions))
        .where(models.HCP.id == hcp_id)
    )
    return db.scalars(stmt).first()


def list_interactions(db: Session) -> list[models.Interaction]:
    stmt = select(models.Interaction).order_by(models.Interaction.interaction_date.desc())
    return list(db.scalars(stmt).all())


def create_interaction(db: Session, payload: schemas.InteractionCreate) -> models.Interaction:
    interaction = models.Interaction(**payload.model_dump())
    db.add(interaction)
    db.commit()
    db.refresh(interaction)
    return interaction


def update_interaction(
    db: Session, interaction_id: int, payload: schemas.InteractionUpdate
) -> models.Interaction | None:
    interaction = db.get(models.Interaction, interaction_id)
    if not interaction:
        return None

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(interaction, field, value)

    db.commit()
    db.refresh(interaction)
    return interaction
