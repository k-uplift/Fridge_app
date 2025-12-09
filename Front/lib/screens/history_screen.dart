import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import '../models/history_item.dart';

class HistoryScreen extends StatelessWidget {
  final List<HistoryItem> historyItems;
  final Function(HistoryItem) onRestore; // 복구 콜백
  final Function(HistoryItem) onDelete;  // 삭제 콜백

  const HistoryScreen({
    super.key, 
    required this.historyItems,
    required this.onRestore,
    required this.onDelete,
  });

  @override
  Widget build(BuildContext context) {
    final sortedList = List<HistoryItem>.from(historyItems)
      ..sort((a, b) => b.date.compareTo(a.date));

    return Scaffold(
      appBar: AppBar(title: const Text('히스토리')),
      body: sortedList.isEmpty
          ? const Center(child: Text('아직 기록이 없어요.'))
          : ListView.separated(
              itemCount: sortedList.length,
              separatorBuilder: (ctx, idx) => const Divider(),
              itemBuilder: (context, index) {
                final item = sortedList[index];
                final isUsed = item.action == HistoryAction.used;
                
                return ListTile(
                  leading: CircleAvatar(
                    backgroundColor: isUsed ? Colors.green[100] : Colors.red[100],
                    child: Icon(
                      isUsed ? Icons.restaurant : Icons.delete_outline,
                      color: isUsed ? Colors.green : Colors.red,
                    ),
                  ),
                  title: Text(item.name, style: const TextStyle(fontWeight: FontWeight.bold)),
                  subtitle: Text(
                    '${DateFormat('yyyy.MM.dd HH:mm').format(item.date)} | ${item.quantity}${item.unit}',
                  ),
                  trailing: Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Text(
                        isUsed ? '사용완료' : '폐기',
                        style: TextStyle(
                          color: isUsed ? Colors.green : Colors.red,
                          fontWeight: FontWeight.bold,
                        ),
                      ),

                      PopupMenuButton<String>(
                        onSelected: (value) {
                          if (value == 'restore') {
                            onRestore(item);
                          } else if (value == 'delete') {
                            onDelete(item);
                          }
                        },
                        itemBuilder: (BuildContext context) => <PopupMenuEntry<String>>[
                          const PopupMenuItem<String>(
                            value: 'restore',
                            child: Row(
                              children: [
                                Icon(Icons.restore, size: 20, color: Colors.blue),
                                SizedBox(width: 8),
                                Text('복구'),
                              ],
                            ),
                          ),
                          const PopupMenuItem<String>(
                            value: 'delete',
                            child: Row(
                              children: [
                                Icon(Icons.delete_forever, size: 20, color: Colors.red),
                                SizedBox(width: 8),
                                Text('삭제'),
                              ],
                            ),
                          ),
                        ],
                      ),
                    ],
                  ),
                );
              },
            ),
    );
  }
}