from pyfcm import FCMNotification

# Replace with your FCM server key from Firebase Console
FCM_SERVER_KEY = "YOUR_FCM_SERVER_KEY_HERE"

push_service = FCMNotification(api_key=FCM_SERVER_KEY)

def send_push_notification(registration_ids, title, message, data=None):
    """
    Send push notification to one or more devices via FCM.
    registration_ids: list of FCM tokens
    title: notification title
    message: notification body
    data: optional dict for custom data
    """
    result = push_service.notify_multiple_devices(
        registration_ids=registration_ids,
        message_title=title,
        message_body=message,
        data_message=data or {}
    )
    return result
