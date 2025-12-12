// lib/services/notification_service.dart
import 'package:flutter_local_notifications/flutter_local_notifications.dart';

class NotificationService {
  NotificationService._internal();
  static final NotificationService _instance = NotificationService._internal();
  factory NotificationService() => _instance;

  final FlutterLocalNotificationsPlugin _plugin =
      FlutterLocalNotificationsPlugin();

  bool _initialized = false;

  Future<void> init() async {
    if (_initialized) return;

    const androidInit = AndroidInitializationSettings('@mipmap/ic_launcher');
    const iosInit = DarwinInitializationSettings();

    const initSettings =
        InitializationSettings(android: androidInit, iOS: iosInit);

    await _plugin.initialize(initSettings);

    _initialized = true;
  }

  /// 유통기한 임박 재료 개수로 간단 알림
  Future<void> showExpiryNotification(int count) async {
    if (!_initialized || count <= 0) return;

    const androidDetails = AndroidNotificationDetails(
      'expiry_channel',
      '유통기한 알림',
      channelDescription: '유통기한 임박 식재료 알림',
      importance: Importance.high,
      priority: Priority.high,
    );

    const iosDetails = DarwinNotificationDetails();

    const details =
        NotificationDetails(android: androidDetails, iOS: iosDetails);

    await _plugin.show(
      0,
      '유통기한 임박',
      '식재료 $count개의 유통기한이 임박했어요.',
      details,
    );
  }
}
