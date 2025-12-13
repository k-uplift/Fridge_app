import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import '../models/food_item.dart';

class OcrResultDialog extends StatefulWidget {
  final List<FoodItem> items;

  const OcrResultDialog({super.key, required this.items});

  @override
  State<OcrResultDialog> createState() => _OcrResultDialogState();
}

class _OcrResultDialogState extends State<OcrResultDialog> {
  late List<FoodItem> _items;

  @override
  void initState() {
    super.initState();
    _items = widget.items;
  }

  String _getStorageKoreanName(StorageLocation location) {
    switch (location) {
      case StorageLocation.refrigerated: return '냉장';
      case StorageLocation.frozen: return '냉동';
      case StorageLocation.roomTemperature: return '실온';
    }
  }

  @override
  Widget build(BuildContext context) {
    return AlertDialog(
      title: const Text('영수증 인식 결과'),
      content: SizedBox(
        width: double.maxFinite,
        height: 300,
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Text(
              '다음 품목들을 인식했어요.\n확인 후 저장 버튼을 눌러주세요.',
              style: TextStyle(fontSize: 13, color: Colors.grey),
            ),
            const SizedBox(height: 10),
            Expanded(
              child: ListView.separated(
                itemCount: _items.length,
                separatorBuilder: (ctx, idx) => const Divider(),
                itemBuilder: (context, index) {
                  final item = _items[index];
                  return ListTile(
                    title: Text(// 품목명
                      item.name, 
                      style: const TextStyle(fontWeight: FontWeight.bold)
                    ),
                   
                    subtitle: Text(  // 수량, 보관위치, 유통기한
                      '${item.quantity}${item.unit} | ${_getStorageKoreanName(item.storageLocation)} | ${DateFormat('yyyy-MM-dd').format(item.expiryDate)}'
                    ),

                    trailing: IconButton( // 잘못 인식된 경우 개별 삭제 가능
                      icon: const Icon(Icons.close, color: Colors.red, size: 20),
                      onPressed: () {
                        setState(() {
                          _items.removeAt(index);
                        });
                      },
                    ),
                  );
                },
              ),
            ),
          ],
        ),
      ),
      actions: [
        TextButton(
          onPressed: () => Navigator.pop(context), // 취소 시 null 반환
          child: const Text('취소', style: TextStyle(color: Colors.grey)),
        ),
        ElevatedButton(
          onPressed: () {
            Navigator.pop(context, _items); // 사용자가 확인한 최종 리스트 반환
          },
          child: const Text('저장'),
        ),
      ],
    );
  }
}