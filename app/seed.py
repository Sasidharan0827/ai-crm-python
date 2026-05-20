from datetime import date, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import HCP, Interaction


def seed_data(db: Session) -> None:
    if db.scalar(select(HCP.id).limit(1)):
        return

    hcps = [
        HCP(
            full_name="Dr. Ananya Mehta",
            specialty="Cardiology",
            organization="Apex Heart Institute",
            city="Mumbai",
            tier="A",
            preferred_channel="In-person",
            prescribing_focus="Heart failure and lipid management",
            notes="Open to outcomes data and patient adherence discussion.",
        ),
        HCP(
            full_name="Dr. Rohan Iyer",
            specialty="Endocrinology",
            organization="Metro Care Hospital",
            city="Bengaluru",
            tier="A",
            preferred_channel="Video call",
            prescribing_focus="Type 2 diabetes and obesity",
            notes="Values quick comparisons and post-market evidence.",
        ),
        HCP(
            full_name="Dr. Nisha Kapoor",
            specialty="Oncology",
            organization="Northline Cancer Center",
            city="Delhi",
            tier="B",
            preferred_channel="WhatsApp follow-up",
            prescribing_focus="Supportive care and adverse event management",
            notes="Prefers short clinical summaries with citations.",
        ),
    ]

    db.add_all(hcps)
    db.flush()

    interactions = [
        Interaction(
            hcp_id=hcps[0].id,
            interaction_date=date.today() - timedelta(days=7),
            channel="In-person",
            title="Quarterly product detail",
            objective="Reinforce efficacy narrative",
            summary="Discussed updated data and patient adherence barriers.",
            sentiment="positive",
            products_discussed=["CardioX", "LipiFlow"],
            follow_up_date=date.today() + timedelta(days=10),
            next_action="Share adherence support leave-behind and arrange nurse educator session.",
        ),
        Interaction(
            hcp_id=hcps[1].id,
            interaction_date=date.today() - timedelta(days=4),
            channel="Video call",
            title="Obesity portfolio discussion",
            objective="Introduce new evidence",
            summary="Doctor requested a concise comparison against current standard of care.",
            sentiment="neutral",
            products_discussed=["GlucoZen"],
            follow_up_date=date.today() + timedelta(days=5),
            next_action="Send one-page evidence summary with safety profile highlights.",
        ),
    ]

    db.add_all(interactions)
    db.commit()
