import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import '../models/food_item.dart';

class ExpiryBanner extends StatefulWidget {
  final List<FoodItem> items;
  const ExpiryBanner({super.key, required this.items});

  @override
  State<ExpiryBanner> createState() => _ExpiryBannerState();
}

class _ExpiryBannerState extends State<ExpiryBanner> {
  static const int warningDays = 6; 
  
  bool _isVisible = true; 
  int _prevExpiringCount = 0; 

  List<FoodItem> _getExpiringItems() {
    final now = DateTime.now();
    final today = DateTime(now.year, now.month, now.day);
    final warningDateLimit = today.add(const Duration(days: warningDays));

    final list = widget.items.where((item) {
      final expiryDay = DateTime(item.expiryDate.year, item.expiryDate.month, item.expiryDate.day);
      return (expiryDay.isAtSameMomentAs(today) || expiryDay.isAfter(today)) && 
             expiryDay.isBefore(warningDateLimit);
    }).toList();
    
    list.sort((a, b) {
      final dateA = DateTime(a.expiryDate.year, a.expiryDate.month, a.expiryDate.day);
      final dateB = DateTime(b.expiryDate.year, b.expiryDate.month, b.expiryDate.day);
      
      int dateComparison = dateA.compareTo(dateB);
      
      if (dateComparison == 0) {
        return a.name.compareTo(b.name);
      }
      
      return dateComparison;
    });

    return list;
  }

  @override
  void initState() {
    super.initState();
    _prevExpiringCount = _getExpiringItems().length;
  }

  @override
  void didUpdateWidget(ExpiryBanner oldWidget) {
    super.didUpdateWidget(oldWidget);
    final currentExpiringItems = _getExpiringItems();
    final currentCount = currentExpiringItems.length;

    if (currentCount != _prevExpiringCount) {
      setState(() {
        _isVisible = true; 
        _prevExpiringCount = currentCount; 
      });
    }
  }

  void _showDetailDialog(List<FoodItem> expiringItems) {
    showDialog(
      context: context,
      builder: (ctx) {
        return AlertDialog(
          backgroundColor: Colors.white,
          surfaceTintColor: Colors.white,
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
          
          title: const Center(
            child: Text(
              '유통기한이 임박한 식재료',
              style: TextStyle(
                fontWeight: FontWeight.bold,
                fontSize: 18,
              ),
              textAlign: TextAlign.center,
            ),
          ),
          
          content: SizedBox(
            width: double.maxFinite,
            child: ListView.separated(
              shrinkWrap: true,
              itemCount: expiringItems.length,
              separatorBuilder: (ctx, idx) => const Divider(),
              itemBuilder: (ctx, idx) {
                final item = expiringItems[idx];
                final now = DateTime.now();
                final today = DateTime(now.year, now.month, now.day);
                final expiryDay = DateTime(item.expiryDate.year, item.expiryDate.month, item.expiryDate.day);
                final dDay = expiryDay.difference(today).inDays;
                
                String dDayText = (dDay == 0) ? '오늘 만료' : '$dDay일 남음';

                return ListTile(
                  contentPadding: EdgeInsets.zero,
                  dense: true,
                  title: Text(item.name, style: const TextStyle(fontWeight: FontWeight.bold)),
                  subtitle: Text('유통기한: ${DateFormat('yyyy.MM.dd').format(item.expiryDate)}'),
                  trailing: Text(
                    dDayText,
                    style: const TextStyle(color: Colors.red, fontWeight: FontWeight.bold),
                  ),
                );
              },
            ),
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(ctx),
              child: const Text('확인', style: TextStyle(color: Colors.black)),
            ),
          ],
        );
      },
    );
  }

  @override
  Widget build(BuildContext context) {
    if (!_isVisible) {
      return const SizedBox.shrink();
    }

    final List<FoodItem> expiringItems = _getExpiringItems();

    if (expiringItems.isEmpty) {
      return const SizedBox.shrink();
    }

    final int count = expiringItems.length;
    final String message = '식재료 $count개의 유통기한이 임박했어요.';

    return Container(
      width: double.infinity,
      padding: const EdgeInsets.fromLTRB(16, 8, 4, 8), 
      color: Colors.amber.shade100,
      child: Row(
        children: [
          Expanded(
            child: GestureDetector(
              onTap: () => _showDetailDialog(expiringItems),
              behavior: HitTestBehavior.opaque,
              child: Row(
                children: [
                  Icon(Icons.warning_amber_rounded, color: Colors.amber[800], size: 20),
                  const SizedBox(width: 12),
                  Expanded(
                    child: Text(
                      message,
                      style: const TextStyle(
                        color: Colors.black87, 
                        fontWeight: FontWeight.bold, 
                        fontSize: 14,
                        decoration: TextDecoration.underline,
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ),
          IconButton(
            constraints: const BoxConstraints(), 
            padding: EdgeInsets.zero, 
            visualDensity: VisualDensity.compact, 
            icon: const Icon(Icons.close, size: 18, color: Colors.black54),
            onPressed: () {
              setState(() {
                _isVisible = false; 
              });
            },
            tooltip: '닫기',
          ),
        ],
      ),
    );
  }
}