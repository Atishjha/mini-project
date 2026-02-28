from flask import Blueprint, jsonify

bp = Blueprint('alerts', __name__)

@bp.route('/', methods=['GET'])
def get_alerts():
    """Get recent alerts"""
    alerts = [
        {
            'id': 1,
            'type': 'warning',
            'message': 'Fire reported in Central Delhi',
            'timestamp': '2024-01-15T10:30:00',
            'severity': 'high'
        },
        {
            'id': 2,
            'type': 'info',
            'message': 'Ambulance dispatched to medical emergency',
            'timestamp': '2024-01-15T11:15:00',
            'severity': 'medium'
        }
    ]
    return jsonify(alerts)

@bp.route('/notify', methods=['POST'])
def send_notification():
    """Send notification"""
    return jsonify({
        'message': 'Notification sent successfully',
        'status': 'queued'
    })