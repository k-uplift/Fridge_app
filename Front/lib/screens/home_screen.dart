import 'dart:io';
import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';
import '../models/food_item.dart';
import '../models/history_item.dart';
import './history_screen.dart';
import '../widgets/food_item_card.dart';
import '../widgets/expiry_banner.dart';
import '../services/ocr_service.dart';
import './add_item_screen.dart';
import './recipe_list_screen.dart';
import './ocr_result_dialog.dart';

enum SortOption { expiryDate, name, quantity }

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  StorageLocation? _selectedStorageFilter;
  FoodCategory? _selectedCategoryFilter;
  String _searchQuery = '';
  
  SortOption _sortOption = SortOption.expiryDate;
  bool _isAscending = true; // true: 오름차순, false: 내림차순

  final OcrService _ocrService = OcrService();
  
  final List<HistoryItem> _historyItems = [];
  
  final List<FoodItem> _mockFoodItems = [ // 샘플 데이터
    FoodItem(
      id: '1', name: '감자', quantity: 5, unit: '개',
      category: FoodCategory.vegetable, storageLocation: StorageLocation.roomTemperature,
      expiryDate: DateTime.now().add(const Duration(days: 2)),
    ),
    FoodItem(
      id: '2', name: '우유', quantity: 1, unit: '개',
      category: FoodCategory.dairy, storageLocation: StorageLocation.refrigerated,
      expiryDate: DateTime.now().add(const Duration(days: 6)),
    ),
    FoodItem(
      id: '3', name: '계란', quantity: 10, unit: '개',
      category: FoodCategory.dairy, storageLocation: StorageLocation.refrigerated,
      expiryDate: DateTime.now().subtract(const Duration(days: 6)),
    ),
    FoodItem(
      id: '4', name: '냉동 만두', quantity: 1, unit: '봉지',
      category: FoodCategory.frozen, storageLocation: StorageLocation.frozen,
      expiryDate: DateTime.now().add(const Duration(days: 90)),
    ),
  ];

  void _confirmDeleteOrUse(FoodItem item, {bool isDecrement = false}) {   // 사용완료 or 삭제 시 확인 다이얼로그
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        title: Text(isDecrement ? '수량 소진' : '항목 삭제'),
        content: Text('어떻게 처리할까요?'),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx),
            child: const Text('취소', style: TextStyle(color: Colors.grey)),
          ),
          TextButton(
            onPressed: () {
              _processItemHistory(item, HistoryAction.discarded);
              Navigator.pop(ctx);
            },
            child: const Text('폐기', style: TextStyle(color: Colors.red)),
          ),
          ElevatedButton(
            onPressed: () {
              _processItemHistory(item, HistoryAction.used);
              Navigator.pop(ctx);
            },
            style: ElevatedButton.styleFrom(backgroundColor: Colors.green),
            child: const Text('사용완료'),
          ),
        ],
      ),
    );
  }

  void _processItemHistory(FoodItem item, HistoryAction action) {  // 히스토리로 이동
    setState(() {
      _historyItems.add(HistoryItem(
        id: DateTime.now().toString(),
        name: item.name,
        quantity: item.quantity,
        unit: item.unit,
        date: DateTime.now(),
        action: action,
        
        category: item.category, // 복구를 위해 원본 정보 저장
        storageLocation: item.storageLocation,
        expiryDate: item.expiryDate,
      ));
      _mockFoodItems.remove(item);
    });
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text('${item.name} 처리 완료 (${action == HistoryAction.used ? '사용' : '폐기'})')),
    );
  }

  void _restoreHistoryItem(HistoryItem historyItem) {  // 히스토리에서 복구
    setState(() {
      _mockFoodItems.add(FoodItem(
        id: DateTime.now().toString(), // 복구 시 새 ID
        name: historyItem.name,
        quantity: historyItem.quantity,
        unit: historyItem.unit,
        category: historyItem.category,
        storageLocation: historyItem.storageLocation,
        expiryDate: historyItem.expiryDate,
      ));
      _historyItems.remove(historyItem);
    });
    
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text('식재료를 다시 복구했어요.')),
    );
  }
 
  void _deleteHistoryItem(HistoryItem historyItem) {  // 히스토리에서 삭제
    setState(() {
      _historyItems.remove(historyItem);
    });
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(content: Text('식재료를 삭제했어요.')),
    );
  }
 
  void _incrementQuantity(FoodItem item) {  // 수량 조절
    setState(() {
      item.quantity = item.quantity + 1;
    });
  }

  void _decrementQuantity(FoodItem item) {
    if (item.quantity > 1) {
      setState(() {
        item.quantity = item.quantity - 1;
      });
    } else {
      _confirmDeleteOrUse(item, isDecrement: true);
    }
  }
  
  void _navigateToRecipeList(List<FoodItem> items) { // 레시피 추천 화면 이동
    if (items.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('재료가 없어요.')));
      return;
    }
    Navigator.push(
      context,
      MaterialPageRoute(builder: (context) => RecipeListScreen(items: items)),
    );
  }

  void _navigateToHistory() {   // 히스토리 화면 이동(복구/삭제 콜백 전달)
    Navigator.push(
      context,
      MaterialPageRoute(
        builder: (context) => StatefulBuilder(
          builder: (context, setHistoryState) {
            return HistoryScreen(
              historyItems: _historyItems,
              onRestore: (item) {
                 _restoreHistoryItem(item); 
                 setHistoryState(() {});
                 Navigator.pop(context);
              },
              onDelete: (item) {
                _deleteHistoryItem(item);
                setHistoryState(() {});
              },
            );
          }
        ),
      ),
    );
  }

  List<FoodItem> _getFilteredAndSortedItems() {   // 필터 및 정렬
    List<FoodItem> items = _mockFoodItems.where((item) {
      if (_selectedStorageFilter != null && item.storageLocation != _selectedStorageFilter) {
        return false;
      }

      if (_selectedCategoryFilter != null && item.category != _selectedCategoryFilter) {
        return false;
      }

      if (_searchQuery.isNotEmpty && !item.name.contains(_searchQuery)) {
        return false;
      }

      return true;
    }).toList();

    items.sort((a, b) {
      int result = 0;
      switch (_sortOption) {
        case SortOption.expiryDate:
          result = a.expiryDate.compareTo(b.expiryDate);
          break;
        case SortOption.name:
          result = a.name.compareTo(b.name);
          break;
        case SortOption.quantity:
          result = a.quantity.compareTo(b.quantity);
          break;
      }
      return _isAscending ? result : -result;
    });

    return items;
  }

  void _showFilterModal(BuildContext context) {   // 필터 설정
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      shape: const RoundedRectangleBorder(borderRadius: BorderRadius.vertical(top: Radius.circular(20))),
      builder: (ctx) {
        return StatefulBuilder( 
          builder: (BuildContext context, StateSetter setModalState) {
            return DraggableScrollableSheet(
              initialChildSize: 0.7,
              minChildSize: 0.5,
              maxChildSize: 0.95,
              expand: false,
              builder: (context, scrollController) {
                return SingleChildScrollView(
                  controller: scrollController,
                  padding: const EdgeInsets.all(20),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Text('보관 위치', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
                      const SizedBox(height: 8),
                      Wrap(
                        spacing: 8,
                        children: [
                          FilterChip(
                            label: const Text('전체'),
                            selected: _selectedStorageFilter == null,
                            onSelected: (bool selected) {
                              setModalState(() => _selectedStorageFilter = null);
                              setState(() {}); // 메인 화면 갱신
                            },
                          ),
                          ...StorageLocation.values.map((loc) => FilterChip(
                            label: Text(_getStorageKoreanName(loc)),
                            selected: _selectedStorageFilter == loc,
                            onSelected: (bool selected) {
                              setModalState(() => _selectedStorageFilter = selected ? loc : null);
                              setState(() {}); 
                            },
                          )),
                        ],
                      ),
                      const Divider(height: 30),

                      const Text('카테고리', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
                      const SizedBox(height: 8),
                      Wrap(
                        spacing: 8,
                        children: [
                          FilterChip(
                            label: const Text('전체'),
                            selected: _selectedCategoryFilter == null,
                            onSelected: (bool selected) {
                              setModalState(() => _selectedCategoryFilter = null);
                              setState(() {});
                            },
                          ),
                          ...FoodCategory.values.map((cat) => FilterChip(
                            label: Text(_getCategoryKoreanName(cat)),
                            selected: _selectedCategoryFilter == cat,
                            onSelected: (bool selected) {
                              setModalState(() => _selectedCategoryFilter = selected ? cat : null);
                              setState(() {});
                            },
                          )),
                        ],
                      ),
                      const Divider(height: 30),

                      const Text('정렬 기준', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
                      const SizedBox(height: 8),
                      DropdownButton<SortOption>(
                        value: _sortOption,
                        isExpanded: true,
                        underline: Container(height: 1, color: Colors.deepPurple),
                        items: const [
                          DropdownMenuItem(value: SortOption.expiryDate, child: Text('유통기한')),
                          DropdownMenuItem(value: SortOption.name, child: Text('이름')),
                          DropdownMenuItem(value: SortOption.quantity, child: Text('수량')),
                        ],
                        onChanged: (SortOption? newValue) {
                          if (newValue != null) {
                            setModalState(() => _sortOption = newValue);
                            setState(() {});
                          }
                        },
                      ),
                      
                      const SizedBox(height: 24),

                      const Text('정렬 순서', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
                      const SizedBox(height: 8),
                      DropdownButton<bool>(
                        value: _isAscending,
                        isExpanded: true,
                        underline: Container(height: 1, color: Colors.deepPurple),
                        items: const [
                          DropdownMenuItem(value: true, child: Text('오름차순')),
                          DropdownMenuItem(value: false, child: Text('내림차순')),
                        ],
                        onChanged: (bool? newValue) {
                          if (newValue != null) {
                            setModalState(() => _isAscending = newValue);
                            setState(() {});
                          }
                        },
                      ),
                      
                      const SizedBox(height: 30),
                      SizedBox(
                        width: double.infinity,
                        child: ElevatedButton(
                          onPressed: () => Navigator.pop(ctx),
                          style: ElevatedButton.styleFrom(
                            padding: const EdgeInsets.symmetric(vertical: 12),
                            backgroundColor: Colors.deepPurple.shade50,
                          ),
                          child: const Text('확인', style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
                        ),
                      ),
                    ],
                  ),
                );
              },
            );
          }
        );
      },
    );
  }

  String _getCategoryKoreanName(FoodCategory category) {
    switch (category) {
      case FoodCategory.dairy: return '유제품';
      case FoodCategory.meat: return '육류';
      case FoodCategory.vegetable: return '채소';
      case FoodCategory.fruit: return '과일';
      case FoodCategory.frozen: return '냉동식품';
      case FoodCategory.seasoning: return '조미료';
      case FoodCategory.cooked: return '조리음식';
      case FoodCategory.etc: return '기타';
    }
  }

  String _getStorageKoreanName(StorageLocation location) {
    switch (location) {
      case StorageLocation.refrigerated: return '냉장';
      case StorageLocation.frozen: return '냉동';
      case StorageLocation.roomTemperature: return '상온';
    }
  }

  Future<void> _pickImageAndProcess(ImageSource source) async {   // 이미지 OCR 및 추가 로직
    final picker = ImagePicker();
    final XFile? pickedFile = await picker.pickImage(source: source);
    if (pickedFile != null) {
      showDialog(
        context: context,
        barrierDismissible: false,
        builder: (ctx) => const Center(child: CircularProgressIndicator()),
      );
      try {
        final List<FoodItem> recognizedItems = await _ocrService.uploadImageAndGetItems(File(pickedFile.path));
        Navigator.pop(context);
        if (!mounted) return;
        final List<FoodItem>? confirmedItems = await showDialog<List<FoodItem>>(
          context: context,
          barrierDismissible: false,
          builder: (ctx) => OcrResultDialog(items: recognizedItems),
        );
        if (confirmedItems != null && confirmedItems.isNotEmpty) {
          setState(() {
            _mockFoodItems.addAll(confirmedItems);
          });
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(content: Text('${confirmedItems.length}개의 품목이 추가되었어요.')),
          );
        }
      } catch (e) {
        Navigator.pop(context);
        ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('인식 중 오류가 발생했어요.')));
      }
    }
  }

  void _showAddItemModal(BuildContext context) {
    showModalBottomSheet(
      context: context,
      builder: (ctx) {
        return Container(
          padding: const EdgeInsets.all(16),
          height: 200,
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text('음식 등록하기', style: Theme.of(context).textTheme.titleLarge),
              const SizedBox(height: 16),
              ListTile(
                leading: const Icon(Icons.image),
                title: const Text('사진으로 입력하기'),
                onTap: () {
                  Navigator.pop(ctx);
                  _pickImageAndProcess(ImageSource.gallery);
                },
              ),
              ListTile(
                leading: const Icon(Icons.edit_note),
                title: const Text('직접 입력하기'),
                onTap: () {
                  Navigator.pop(ctx);
                  _navigateAndManageItem(context);
                },
              ),
            ],
          ),
        );
      },
    );
  }

  void _navigateAndManageItem(BuildContext context, {FoodItem? existingItem}) async {
    final resultItem = await Navigator.push<FoodItem>(
      context,
      MaterialPageRoute(
        builder: (context) => AddItemScreen(existingItem: existingItem),
      ),
    );
    if (resultItem != null) {
      setState(() {
        if (existingItem != null) {
          final index = _mockFoodItems.indexWhere((item) => item.id == existingItem.id);
          if (index != -1) _mockFoodItems[index] = resultItem;
        } else {
          _mockFoodItems.add(resultItem);
        }
      });
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('식재료가 ${existingItem != null ? '수정' : '등록'}되었어요.')),
      );
    }
  }

  void _showEditDeleteModal(BuildContext context, FoodItem item) {
    showModalBottomSheet(
      context: context,
      builder: (ctx) {
        return Container(
          padding: const EdgeInsets.all(16),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              ListTile(
                leading: const Icon(Icons.edit, color: Colors.blue),
                title: const Text('수정'),
                onTap: () {
                  Navigator.pop(ctx);
                  _navigateAndManageItem(context, existingItem: item);
                },
              ),
              ListTile(
                leading: const Icon(Icons.delete, color: Colors.red),
                title: const Text('삭제'),
                onTap: () {
                  Navigator.pop(ctx);
                  _confirmDeleteOrUse(item); 
                },
              ),
            ],
          ),
        );
      },
    );
  }

  @override
  Widget build(BuildContext context) {
    final filteredList = _getFilteredAndSortedItems();

    return Scaffold(
      appBar: AppBar(
        title: const Text('나의 냉장고'),
        leading: IconButton(
          icon: const Icon(Icons.filter_list),
          onPressed: () => _showFilterModal(context),
        ),
        actions: [
          IconButton(
            icon: const Icon(Icons.history),
            tooltip: '사용/폐기 기록',
            onPressed: _navigateToHistory,
          ),
          IconButton(
            icon: const Icon(Icons.restaurant_menu, color: Colors.deepPurple),
            tooltip: '레시피 추천',
            onPressed: () => _navigateToRecipeList(_mockFoodItems),
          ),
        ],
      ),
      body: Column(
        children: [
          Padding(
            padding: const EdgeInsets.all(8.0),
            child: TextField(
              decoration: InputDecoration(
                hintText: '식재료 검색',
                prefixIcon: const Icon(Icons.search),
                border: OutlineInputBorder(borderRadius: BorderRadius.circular(10)),
                contentPadding: const EdgeInsets.symmetric(horizontal: 10),
              ),
              onChanged: (value) {
                setState(() {
                  _searchQuery = value;
                });
              },
            ),
          ),
          ExpiryBanner(items: _mockFoodItems),
          Expanded(
            child: filteredList.isEmpty
                ? const Center(child: Text('검색된 식재료가 없어요.'))
                : ListView.builder(
                    itemCount: filteredList.length,
                    itemBuilder: (context, index) {
                      final item = filteredList[index];
                      return FoodItemCard(
                        item: item,
                        onTap: () => _navigateToRecipeList([item]),
                        onIncrement: () => _incrementQuantity(item),
                        onDecrement: () => _decrementQuantity(item),
                        onLongPress: () => _showEditDeleteModal(context, item),
                      );
                    },
                  ),
          ),
        ],
      ),
      floatingActionButton: FloatingActionButton(
        onPressed: () => _showAddItemModal(context),
        child: const Icon(Icons.add),
      ),
    );
  }
}