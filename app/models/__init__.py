from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

from .announcements_model      import WardAnnouncements
from .attendances_model        import Attendance
from .base_model               import Setup, NameCorrections
from .bishoprics_model         import Bishopric
from .business_model           import WardBusiness
from .classes_model            import Classes
from .hymns_model              import Hymns
from .meeting_centers_model    import MeetingCenter
from .members_model            import Member
from .organizations_model      import Organization
from .sacrament_agendas_model  import SacramentAgenda
from .sacrament_meetings_model import SacramentMeeting
from .speakers_model           import Speakers
from .users_model              import User