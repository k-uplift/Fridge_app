// lib/widgets/expiry_banner.dart

import 'package:flutter/material.dart';
import '../models/food_item.dart';

class ExpiryBanner extends StatelessWidget {
  // 배너를 표시할 기준일 (예: 3일 이내)
  static const int warningDays = 6;

  final List<FoodItem> items;

  const ExpiryBanner({super.key, required this.items});

  // 유통기한이 임박한 항목 목록을 '임박한 순서대로 정렬'하여 반환
  List<FoodItem> _getExpiringItems() {
    final now = DateTime.now();
    final today = DateTime(now.year, now.month, now.day);
    
    // (기준일: 오늘 + 3일)
    final warningDateLimit = today.add(const Duration(days: warningDays));

    // 1. 기준일 이내의 항목들 필터링
    List<FoodItem> expiringItems = items.where((item) {
      final expiryDay = DateTime(item.expiryDate.year, item.expiryDate.month, item.expiryDate.day);
      
      // 만료일이 (오늘이거나 오늘 이후) 이면서 (기준일 3일 '전') 인 항목
      return (expiryDay.isAtSameMomentAs(today) || expiryDay.isAfter(today)) && 
             expiryDay.isBefore(warningDateLimit);
    }).toList();

    // --- 1. (FIX) 가장 임박한 순서로 정렬 ---
    // (예: '오늘 만료'가 '2일 남음'보다 앞에 오도록)
    expiringItems.sort((a, b) => a.expiryDate.compareTo(b.expiryDate));
    // ------------------------------------

    return expiringItems;
  }

  @override
  Widget build(BuildContext context) {
    final List<FoodItem> expiringItems = _getExpiringItems();

    // 임박한 항목이 없으면 아무것도 표시하지 않음
    if (expiringItems.isEmpty) {
      return const SizedBox.shrink();
    }

    // (FIX) 정렬된 리스트의 '첫 번째' 항목이 가장 임박한 항목임
    final firstItem = expiringItems.first;
    final remainingCount = expiringItems.length - 1;
    
    String message;
    if (remainingCount > 0) {
      // (가장 임박한 항목을 기준으로 메시지 표시)
      message = '${firstItem.name} 외 $remainingCount개의 유통기한이 임박했습니다.';
    } else {
      // --- 2. (FIX) 하드코딩된 메시지 수정 ---
      
      // 1. D-day 계산 (가장 임박한 항목 기준)
      final now = DateTime.now();
      final today = DateTime(now.year, now.month, now.day);
      final expiryDay = DateTime(firstItem.expiryDate.year, firstItem.expiryDate.month, firstItem.expiryDate.day);
      final difference = expiryDay.difference(today).inDays;

      // 2. D-day 라벨 생성
      String dayLabel;
      if (difference == 0) {
        dayLabel = '오늘 만료';
      } else {
        // (필터 로직에 의해 difference는 항상 0, 1, 2 중 하나임)
        dayLabel = '$difference일 남음'; 
      }

      // 3. 올바른 메시지 설정
      message = '${firstItem.name} ($dayLabel)';
      // ------------------------------------
    }

    return Container(
      width: double.infinity,
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
      color: Colors.amber.shade100,
      child: Row(
        children: [
          Icon(Icons.warning_amber_rounded, color: Colors.amber[800]),
          const SizedBox(width: 12),
          Expanded(
            child: Text(
              message,
              style: const TextStyle(color: Colors.black87, fontWeight: FontWeight.bold),
            ),
          ),
        ],
      ),
    );
  }
}