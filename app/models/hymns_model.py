# app/models/hymns.py
from app.models import db

class Hymns(db.Model):
    id     = db.Column(db.Integer, primary_key=True)
    number = db.Column(db.Integer, nullable=False, unique=True)
    title  = db.Column(db.String(200), nullable=False)
    lang   = db.Column(db.String(5), nullable=False)
    topic  = db.Column(db.Integer, nullable=False)

    # Diccionario para mapear números a temas
    TOPICS = {
        1: "Restauración",
        2: "Alabanza y agradecimiento",
        3: "Súplica",
        4: "Santa Cena",
        5: "Pascua de Resurrección",
        6: "Navidad",
        7: "Temas varios",
        8: "Para niños",
        9: "Para mujeres",
        10: "Para hombres",
        11: "Día de Reposo y día de semana",
        12: "Pascua de Resurrección y Navidad",
    }

    __table_args__ = (
        db.UniqueConstraint('number', name='uq_hymns_number'),
    )

    def get_topic_name(self):
        return self.TOPICS.get(self.topic, "Desconocido")
