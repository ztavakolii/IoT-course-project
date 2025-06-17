from app import app, db
from models import Device, Zone, Desk

with app.app_context():

    temp_sensor = Device(kind='Temperature', zone_id=None, status='online')
    sound_sensor = Device(kind='Sound', zone_id=None, status='online')
    pollution_sensor = Device(kind='Air Pollution', zone_id=None, status='online')

    db.session.add_all([temp_sensor, sound_sensor, pollution_sensor])
    db.session.commit()
    zone_a = Zone(
        name='A',
        temperature_sensor_id=temp_sensor.id,
        sound_sensor_id=sound_sensor.id,
        pollution_sensor_id=pollution_sensor.id
    )

    db.session.add(zone_a)
    db.session.commit()

    desk1 = Desk(zone_id=zone_a.id, status='free', comment='Desk 1')
    desk2 = Desk(zone_id=zone_a.id, status='free', comment='Desk 2')

    db.session.add_all([desk1, desk2])
    db.session.commit()

    motion1 = Device(kind='Motion', zone_id=zone_a.id, desk_id=desk1.id, status='online')
    motion2 = Device(kind='Motion', zone_id=zone_a.id, desk_id=desk1.id, status='online')

    motion3 = Device(kind='Motion', zone_id=zone_a.id, desk_id=desk2.id, status='online')
    motion4 = Device(kind='Motion', zone_id=zone_a.id, desk_id=desk2.id, status='online')

    db.session.add_all([motion1, motion2, motion3, motion4])
    db.session.commit()

