
```
attendance
├─ app
│  ├─ babel.cfg
│  ├─ config
│  │  ├─ base.py
│  │  ├─ development.py
│  │  ├─ production.py
│  │  └─ __init__.py
│  ├─ forms
│  │  ├─ agenda_form.py
│  │  ├─ announcement_form.py
│  │  ├─ attendance_form.py
│  │  ├─ auth_form.py
│  │  ├─ business_form.py
│  │  ├─ clase_form.py
│  │  ├─ hymn_form.py
│  │  ├─ meeting_center_form.py
│  │  ├─ member_form.py
│  │  ├─ organization_form.py
│  │  ├─ selected_hymns_form.py
│  │  ├─ speaker_form.py
│  │  ├─ user_form.py
│  │  └─ __init__.py
│  ├─ messages.pot
│  ├─ models
│  │  ├─ agenda_model.py
│  │  ├─ announcements_model.py
│  │  ├─ attendances_model.py
│  │  ├─ base_model.py
│  │  ├─ bishoprics_model.py
│  │  ├─ business_model.py
│  │  ├─ classes_model.py
│  │  ├─ hymns_model.py
│  │  ├─ meeting_centers_model.py
│  │  ├─ members_model.py
│  │  ├─ organizations_model.py
│  │  ├─ prayers_model.py
│  │  ├─ selected_hymns_model.py
│  │  ├─ speakers_model.py
│  │  ├─ users_model.py
│  │  └─ __init__.py
│  ├─ passenger_wsgi.py
│  ├─ routes
│  │  ├─ admin_route.py
│  │  ├─ agendas_route.py
│  │  ├─ announcements_route.py
│  │  ├─ attendance_route.py
│  │  ├─ auth_route.py
│  │  ├─ bishopric_route.py
│  │  ├─ bussines_route.py
│  │  ├─ centers_route.py
│  │  ├─ classes_route.py
│  │  ├─ hymns_route copy.py
│  │  ├─ hymns_route.py
│  │  ├─ import_member.py
│  │  ├─ members_route.py
│  │  ├─ name_correction_route.py
│  │  ├─ organization_route.py
│  │  ├─ pdf_route.py
│  │  ├─ register_route.py
│  │  ├─ speakers_route.py
│  │  ├─ stats_route.py
│  │  ├─ swal_route.py
│  │  ├─ users_route.py
│  │  └─ __init__.py
│  ├─ static
│  │  ├─ css
│  │  │  └─ styles.css
│  │  ├─ img
│  │  │  └─ flags
│  │  │     ├─ en.png
│  │  │     ├─ es.png
│  │  │     ├─ lang.svg
│  │  │     └─ pt.png
│  │  └─ js
│  │     └─ scripts.js
│  ├─ templates
│  │  ├─ admin
│  │  │  ├─ admin.html
│  │  │  ├─ admin_script.html
│  │  │  ├─ name_correction.html
│  │  │  ├─ non_attendance.html
│  │  │  └─ with_attendance.html
│  │  ├─ agendas
│  │  │  ├─ add.html
│  │  │  ├─ form copy.html
│  │  │  ├─ form.html
│  │  │  └─ list.html
│  │  ├─ announcements
│  │  │  ├─ add.html
│  │  │  └─ list.html
│  │  ├─ attendance
│  │  │  ├─ attendance.html
│  │  │  ├─ check.html
│  │  │  ├─ check_script.html
│  │  │  ├─ list.html
│  │  │  ├─ list_script.html
│  │  │  ├─ list_table.html
│  │  │  ├─ manual.html
│  │  │  ├─ manual_script.html
│  │  │  ├─ report.html
│  │  │  ├─ report_script.html
│  │  │  └─ report_table.html
│  │  ├─ auth
│  │  │  ├─ login.html
│  │  │  └─ login_script.html
│  │  ├─ base.html
│  │  ├─ bishopric
│  │  │  └─ manage.html
│  │  ├─ business
│  │  │  ├─ add.html
│  │  │  └─ list.html
│  │  ├─ classes
│  │  │  ├─ list.html
│  │  │  └─ list_script.html
│  │  ├─ errors
│  │  │  └─ 4xx.html
│  │  ├─ form
│  │  │  ├─ form.html
│  │  │  ├─ macros.html
│  │  │  └─ member_form.html
│  │  ├─ hymns
│  │  │  ├─ add.html
│  │  │  ├─ list.html
│  │  │  └─ selected.html
│  │  ├─ index.html
│  │  ├─ layout.html
│  │  ├─ meeting_centers
│  │  │  └─ list.html
│  │  ├─ members
│  │  │  ├─ list.html
│  │  │  ├─ list_script.html
│  │  │  ├─ pivot.html
│  │  │  ├─ profile copy.html
│  │  │  └─ profile.html
│  │  ├─ organizations
│  │  │  └─ list.html
│  │  ├─ partials
│  │  │  ├─ flashes.html
│  │  │  ├─ footer.html
│  │  │  ├─ form_filter.html
│  │  │  ├─ head.html
│  │  │  ├─ navbar.html
│  │  │  └─ scripts
│  │  │     └─ bottom.html
│  │  ├─ pdfs
│  │  │  ├─ list.html
│  │  │  └─ list_script.html
│  │  ├─ reset_name.html
│  │  ├─ speakers
│  │  │  ├─ add.html
│  │  │  └─ list.html
│  │  ├─ stats
│  │  │  ├─ stats.html
│  │  │  └─ stats_script.html
│  │  └─ users
│  │     ├─ list.html
│  │     └─ list_script.html
│  ├─ translations
│  │  ├─ es
│  │  │  └─ LC_MESSAGES
│  │  │     ├─ messages.mo
│  │  │     └─ messages.po
│  │  └─ pt
│  │     └─ LC_MESSAGES
│  │        ├─ messages.mo
│  │        └─ messages.po
│  ├─ utils.py
│  └─ __init__.py
├─ instance
│  └─ attendance_dev.db
├─ requirements.txt
└─ run.py

```