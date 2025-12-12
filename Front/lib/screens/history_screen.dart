import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import '../models/history_item.dart';

class HistoryScreen extends StatefulWidget {
  final List<HistoryItem> historyItems;
  final Function(HistoryItem) onRestore;
  final Function(HistoryItem) onDelete;

  const HistoryScreen({
    super.key,
    required this.historyItems,
    required this.onRestore,
    required this.onDelete,
  });

  @override
  State<HistoryScreen> createState() => _HistoryScreenState();
}

enum _FilterType { all, used, discarded }

class _HistoryScreenState extends State<HistoryScreen> {
  _FilterType _currentFilter = _FilterType.all;

  @override
  Widget build(BuildContext context) {

    final filteredList = widget.historyItems.where((item) { // 필터링 로직
      if (_currentFilter == _FilterType.all) return true;
      if (_currentFilter == _FilterType.used) {
        return item.action == HistoryAction.used;
      }
      if (_currentFilter == _FilterType.discarded) {
        return item.action != HistoryAction.used; // used가 아니면 폐기로 간주
      }
      return true;
    }).toList();

    filteredList.sort((a, b) { // 정렬 로직
      if (a.action != b.action) {
        return a.action == HistoryAction.used ? -1 : 1;
      }
      return a.name.compareTo(b.name);
    });

    return Scaffold(
      backgroundColor: Colors.grey[50],
      appBar: AppBar(
        title: const Text('히스토리'),
        backgroundColor: Colors.transparent,
        elevation: 0,
        centerTitle: true,
      ),
      body: Column(
        children: [
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
            color: Colors.transparent,
            child: Row(
              children: [
                _buildFilterChip('전체', _FilterType.all),
                const SizedBox(width: 8),
                _buildFilterChip('사용 완료', _FilterType.used),
                const SizedBox(width: 8),
                _buildFilterChip('폐기', _FilterType.discarded),
              ],
            ),
          ),
          
          Expanded(
            child: filteredList.isEmpty
                ? const Center(
                    child: Text(
                      '기록이 없어요.',
                      style: TextStyle(color: Colors.grey, fontSize: 16),
                    ),
                  )
                : ListView.separated(
                    padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                    itemCount: filteredList.length,
                    separatorBuilder: (ctx, idx) => const SizedBox(height: 12),
                    itemBuilder: (context, index) {
                      final item = filteredList[index];
                      final isUsed = item.action == HistoryAction.used;
                      final datePrefix = isUsed ? '재료 소진 일자' : '재료 폐기 일자';

                      return Container(
                        decoration: BoxDecoration(
                          color: Colors.white,
                          borderRadius: BorderRadius.circular(12),
                          boxShadow: [
                            BoxShadow(
                              color: Colors.grey.withOpacity(0.1),
                              blurRadius: 4,
                              offset: const Offset(0, 2),
                            ),
                          ],
                        ),
                        child: ListTile(
                          contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
                          leading: CircleAvatar(
                            backgroundColor: isUsed ? Colors.green[50] : Colors.red[50],
                            child: Icon(
                              isUsed ? Icons.check : Icons.delete_outline,
                              color: isUsed ? Colors.green : Colors.red,
                              size: 20,
                            ),
                          ),
                          title: Text(
                            item.name,
                            style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16),
                          ),
                          subtitle: Padding(
                            padding: const EdgeInsets.only(top: 4),
                            child: Text(
                              '$datePrefix: ${DateFormat('yyyy.MM.dd').format(item.date)} | ${item.quantity.toInt()}${item.unit}',
                              style: TextStyle(fontSize: 13, color: Colors.grey[600]),
                            ),
                          ),
                          trailing: Row(
                            mainAxisSize: MainAxisSize.min,
                            children: [
                              Text(
                                isUsed ? '사용완료' : '폐기',
                                style: TextStyle(
                                  color: isUsed ? Colors.green : Colors.red,
                                  fontWeight: FontWeight.bold,
                                  fontSize: 14,
                                ),
                              ),
                              PopupMenuButton<String>(
                                color: Colors.white,
                                surfaceTintColor: Colors.white,
                                icon: const Icon(Icons.more_vert, color: Colors.grey),
                                onSelected: (value) {
                                  if (value == 'restore') {
                                    widget.onRestore(item);
                                  } else if (value == 'delete') {
                                    widget.onDelete(item);
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
                        ),
                      );
                    },
                  ),
          ),
        ],
      ),
    );
  }

  // 필터 칩 위젯 (디자인: 홈 화면 스타일과 유사하게)
  Widget _buildFilterChip(String label, _FilterType type) {
    final isSelected = _currentFilter == type;
    
    return GestureDetector(
      onTap: () {
        setState(() {
          _currentFilter = type;
        });
      },
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
        decoration: BoxDecoration(
          color: isSelected ? const Color(0xFF0F172A) : Colors.white, // 선택되면 남색, 아니면 흰색
          borderRadius: BorderRadius.circular(20),
          border: Border.all(
            color: isSelected ? const Color(0xFF0F172A) : Colors.grey[300]!,
          ),
        ),
        child: Text(
          label,
          style: TextStyle(
            color: isSelected ? Colors.white : Colors.grey[600],
            fontWeight: isSelected ? FontWeight.bold : FontWeight.normal,
            fontSize: 14,
          ),
        ),
      ),
    );
  }
}