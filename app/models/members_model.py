from datetime import date
from app.models import db


class Member(db.Model):
    id                = db.Column(db.Integer, primary_key=True)
    full_name         = db.Column(db.String(255), nullable=False)
    preferred_name    = db.Column(db.String(100))
    short_name        = db.Column(db.String(50))
    birth_date        = db.Column(db.Date)
    gender            = db.Column(db.String(1), nullable=False)  # 'M' o 'F'
    marital_status    = db.Column(db.String(20))
    priesthood        = db.Column(db.String(50))
    priesthood_office = db.Column(db.String(50))
    address           = db.Column(db.String(255))
    city              = db.Column(db.String(100))
    state             = db.Column(db.String(50))
    zip_code          = db.Column(db.String(15))
    sector            = db.Column(db.String(50))
    lat               = db.Column(db.Float)
    lon               = db.Column(db.Float)
    fixed_address     = db.Column(db.String(100))
    excluded          = db.Column(db.Boolean, default=False)
    new               = db.Column(db.Boolean, default=False)
    calling           = db.Column(db.String(100))
    arrival_date      = db.Column(db.Date)
    moved_out         = db.Column(db.Boolean, default=False)
    active            = db.Column(db.Boolean, default=True)
    meeting_center_id = db.Column(db.Integer, db.ForeignKey('meeting_center.id'), nullable=False)
    family_head       = db.Column(db.String(100))

    # Constructor personalizado para calcular los nombres
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._calculate_names()
        self._format_fields()

    def _calculate_names(self):
        """Método para calcular preferred_name y short_name solo si están vacíos"""
        if self.full_name:
            if not self.preferred_name:  # Solo calcula si preferred_name está vacío
                name_parts = self.full_name.split(',')
                last_name = name_parts[0].strip().split()[0]
                first_name = name_parts[1].strip().split()[0]
                self.preferred_name = f"{first_name} {last_name}"

            if not self.short_name:  # Solo calcula si short_name está vacío
                name_parts = self.full_name.split(',')
                last_name = name_parts[0].strip().split()[0]
                first_name = name_parts[1].strip().split()[0]
                self.short_name = f"{last_name}, {first_name}"


    def _format_fields(self):
        """Método para formatear address, city y state a título"""
        if self.address:
            self.address = self.address.title() or ""
        if self.city:
            self.city = self.city.title() or ""
        if self.state:
            self.state = self.state.title() or ""


    def age(self):
        if self.birth_date:
            today = date.today()
            return today.year - self.birth_date.year - ((today.month, today.day) < (self.birth_date.month, self.birth_date.day))
        return None
