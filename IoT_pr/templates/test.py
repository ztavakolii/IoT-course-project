@app.route('/sensor-data', methods=['POST'])
def receive_sensor_data():
    try:
        data = request.json
        desk_id = data.get("desk_id")
        token = data.get("token")
        alert_type = data.get("type")

        # برای نوع environment
        temperature = data.get("temperature")
        ppm = data.get("ppm")

        if not desk_id or not token or not alert_type:
            return jsonify({'status': 'fail', 'message': 'Missing parameters'}), 400

        if AUTHORIZED_DEVICES.get(desk_id) != token:
            return jsonify({'status': 'fail', 'message': 'Unauthorized'}), 401

        if alert_type == "environment":
            # ذخیره مقدار درون desk
            desk = Desk.query.get(int(desk_id))
            if desk:
                desk.comment = f"دما: {temperature} °C | آلودگی: {ppm} PPM"
                desk.last_present_time = datetime.utcnow()
                db.session.commit()
            return jsonify({'status': 'success', 'message': 'Environment data recorded'})

        # سایر alert_type ها مثل motion یا sound اینجا...
        return jsonify({'status': 'success', 'message': 'Alert type handled'})

    except Exception as e:
        return jsonify({'status': 'fail', 'message': str(e)}), 500
