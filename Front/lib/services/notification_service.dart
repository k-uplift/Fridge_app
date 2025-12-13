import 'dart:io' show Platform;

import 'package:flutter/foundation.dart';
import 'package:flutter_local_notifications/flutter_local_notifications.dart';
import 'package:timezone/data/latest_all.dart' as tz;
import 'package:timezone/timezone.dart' as tz;

class NotificationService {
  NotificationService._internal();
  static final NotificationService _instance = NotificationService._internal();
  factory NotificationService() => _instance;

  final FlutterLocalNotificationsPlugin _plugin =
      FlutterLocalNotificationsPlugin();

  bool _initialized = false;
  bool _tzInitialized = false;

  static const int _dailyExpiryNotificationId = 100;

  bool get _isSupportedPlatform {
    if (kIsWeb) return false;
    return Platform.isAndroid || Platform.isIOS;
  }

  Future<void> _initTimeZone() async {
    if (_tzInitialized) return;
    tz.initializeTimeZones();
    tz.setLocalLocation(tz.getLocation('Asia/Seoul'));
    _tzInitialized = true;
  }

  Future<void> init() async {
    if (_initialized) return;
    if (!_isSupportedPlatform) {
      _initialized = true;
      return;
    }

    const androidInit = AndroidInitializationSettings('@mipmap/ic_launcher');
    const iosInit = DarwinInitializationSettings(
      requestAlertPermission: true,
      requestBadgePermission: true,
      requestSoundPermission: true,
    );

    const initSettings =
        InitializationSettings(android: androidInit, iOS: iosInit);

    await _plugin.initialize(initSettings);
    await _initTimeZone();

    _initialized = true;
  }

  Future<void> showExpiryNotification(int count) async {
    if (!_initialized || count <= 0 || !_isSupportedPlatform) return;

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

  Future<void> updateDailyExpiryReminder(String? bodyText) async {
    if (!_initialized || !_isSupportedPlatform) return;

    await _plugin.cancel(_dailyExpiryNotificationId);

    if (bodyText == null || bodyText.trim().isEmpty) return;

    final now = tz.TZDateTime.now(tz.local);
    var firstTriggerTime = tz.TZDateTime(
      tz.local,
      now.year,
      now.month,
      now.day,
      9, 
      0,
    );

    if (firstTriggerTime.isBefore(now)) {
      firstTriggerTime = firstTriggerTime.add(const Duration(days: 1));
    }

    const androidDetails = AndroidNotificationDetails(
      'expiry_daily_channel',
      '유통기한 매일 알림',
      channelDescription: '유통기한이 임박한 식재료를 매일 아침 알려주는 채널',
      importance: Importance.max,
      priority: Priority.high,
    );

    const iosDetails = DarwinNotificationDetails();

    const notificationDetails = NotificationDetails(
      android: androidDetails,
      iOS: iosDetails,
    );

    await _plugin.zonedSchedule(
      _dailyExpiryNotificationId,
      '유통기한 알림',
      bodyText,
      firstTriggerTime,
      notificationDetails,
      androidScheduleMode: AndroidScheduleMode.exactAllowWhileIdle,
      uiLocalNotificationDateInterpretation:
          UILocalNotificationDateInterpretation.absoluteTime,
      matchDateTimeComponents: DateTimeComponents.time,
    );
  }
}
