import 'dart:io';
import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';
import '../models/food_item.dart';
import '../models/history_item.dart';
import '../models/recipe.dart'; 
import './history_screen.dart';
import '../widgets/food_item_card.dart';
import '../widgets/expiry_banner.dart';
import '../services/ocr_service.dart';
import './add_item_screen.dart';
import './recipe_list_screen.dart';
import './recipe_detail_screen.dart';
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
  bool _isAscending = true; 

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

  List<FoodCategory> get _sortedCategories {   
    final categories = FoodCategory.values.toList();
    categories.sort((a, b) {
      if (a == FoodCategory.etc) return 1;
      if (b == FoodCategory.etc) return -1;
      return _getCategoryKoreanName(a).compareTo(_getCategoryKoreanName(b));
    });
    return categories;
  }

  String _getParticle(String word) {
    if (word.isEmpty) return '로';
    
    int code = word.runes.last;
    if (code < 0xAC00 || code > 0xD7A3) return '로'; 

    int jongseong = (code - 0xAC00) % 28;

    if (jongseong == 0 || jongseong == 8) { 
      return '로';
    } else {
      return '으로';
    }
  }

  void _showRecipeDialog(BuildContext context, FoodItem item) {
    final List<Recipe> matchingRecipes = MOCK_RECIPES.where(
      (recipe) => recipe.mainIngredients.any(
        (ingredient) => item.name.contains(ingredient),
      ),
    ).toList();

    showDialog(
      context: context,
      builder: (context) {
        return Dialog(
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
          backgroundColor: Colors.white,
          insetPadding: const EdgeInsets.symmetric(horizontal: 20, vertical: 24),
          child: Container(
            height: 500,
            decoration: BoxDecoration(
              color: Colors.white,
              borderRadius: BorderRadius.circular(16),
            ),
            child: Stack(
              children: [
                // 1. 내용물
                Padding(
                  padding: const EdgeInsets.fromLTRB(20, 10, 20, 20),
                  child: Column(
                    children: [
                      const SizedBox(height: 24),
                      Text(
                        '${item.name}${_getParticle(item.name)} 만들 수 있는 요리',
                        textAlign: TextAlign.center,
                        style: const TextStyle(
                          fontSize: 20,
                          fontWeight: FontWeight.bold,
                        ),
                        maxLines: 2,
                        overflow: TextOverflow.ellipsis,
                      ),
                      const SizedBox(height: 8),
                      Text(
                        '${item.name}(를) 활용한 레시피를 선택하세요.',
                        style: TextStyle(color: Colors.grey[600], fontSize: 14),
                        textAlign: TextAlign.center,
                      ),
                      const SizedBox(height: 20),

                      Expanded(
                        child: matchingRecipes.isEmpty
                            ? const Center(child: Text("등록된 레시피가 없어요."))
                            : ListView.builder(
                                itemCount: matchingRecipes.length,
                                itemBuilder: (context, index) {
                                  final recipe = matchingRecipes[index];
                                  return Container(
                                    margin: const EdgeInsets.only(bottom: 12),
                                    decoration: BoxDecoration(
                                      border: Border.all(color: Colors.grey[300]!),
                                      borderRadius: BorderRadius.circular(12),
                                    ),
                                    child: ListTile(
                                      contentPadding: const EdgeInsets.all(12),
                                      title: Text(
                                        recipe.name,
                                        style: const TextStyle(fontWeight: FontWeight.bold),
                                      ),
                                      subtitle: Column(
                                        crossAxisAlignment: CrossAxisAlignment.start,
                                        children: [
                                          const SizedBox(height: 8),
                                          Row(
                                            children: [
                                              Icon(Icons.access_time, size: 14, color: Colors.grey[600]),
                                              const SizedBox(width: 4),
                                              Text('${recipe.durationInMinutes}분  ',
                                                  style: TextStyle(fontSize: 12, color: Colors.grey[600])),
                                              const SizedBox(width: 8),
                                              Container(
                                                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                                                decoration: BoxDecoration(
                                                  color: recipe.difficulty == '쉬움' ? Colors.black : Colors.grey[300],
                                                  borderRadius: BorderRadius.circular(4),
                                                ),
                                                child: Text(
                                                  recipe.difficulty,
                                                  style: TextStyle(
                                                    fontSize: 11,
                                                    color: recipe.difficulty == '쉬움' ? Colors.white : Colors.black,
                                                    fontWeight: FontWeight.bold,
                                                  ),
                                                ),
                                              ),
                                            ],
                                          ),
                                          const SizedBox(height: 8),
                                          Text(
                                            '재료: ${recipe.ingredients.take(3).join(", ")} 외 ${recipe.ingredients.length > 3 ? recipe.ingredients.length - 3 : 0}개',
                                            style: TextStyle(color: Colors.grey[600], fontSize: 13),
                                            maxLines: 1,
                                            overflow: TextOverflow.ellipsis,
                                          ),
                                        ],
                                      ),
                                      onTap: () {
                                        showDialog(
                                          context: context,
                                          builder: (context) => RecipeDetailScreen(recipe: recipe),
                                        );
                                      },
                                    ),
                                  );
                                },
                              ),
                      ),
                    ],
                  ),
                ),

                // 2. 닫기 버튼
                Positioned(
                  top: 8,
                  right: 8,
                  child: Material(
                    color: Colors.transparent,
                    child: InkWell(
                      borderRadius: BorderRadius.circular(20),
                      onTap: () => Navigator.pop(context),
                      child: Padding(
                        padding: const EdgeInsets.all(8.0),
                        child: const Icon(
                          Icons.close,
                          size: 20,
                          color: Colors.grey,
                        ),
                      ),
                    ),
                  ),
                ),
              ],
            ),
          ),
        );
      },
    );
  }

  void _confirmDeleteOrUse(FoodItem item, {bool isDecrement = false}) { 
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        backgroundColor: Colors.white,
        surfaceTintColor: Colors.white,
        title: Text(isDecrement ? '수량 소진' : '항목 삭제'),
        content: const Text('어떻게 처리할까요?'),
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
            child: const Text('사용완료', style: TextStyle(color: Colors.white)),
          ),
        ],
      ),
    );
  }

  void _processItemHistory(FoodItem item, HistoryAction action) {
    setState(() {
      _historyItems.add(HistoryItem(
        id: DateTime.now().toString(),
        name: item.name,
        quantity: item.quantity,
        unit: item.unit,
        date: DateTime.now(),
        action: action,
        category: item.category,
        storageLocation: item.storageLocation,
        expiryDate: item.expiryDate,
      ));
      _mockFoodItems.remove(item);
    });
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text('${item.name} 처리 완료 (${action == HistoryAction.used ? '사용' : '폐기'})')),
    );
  }

  void _restoreHistoryItem(HistoryItem historyItem) {
    setState(() {
      _mockFoodItems.add(FoodItem(
        id: DateTime.now().toString(),
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
      const SnackBar(content: Text('식재료를 다시 복구했어요.')),
    );
  }
 
  void _deleteHistoryItem(HistoryItem historyItem) {
    setState(() {
      _historyItems.remove(historyItem);
    });
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(content: Text('기록을 삭제했어요.')),
    );
  }
 
  void _incrementQuantity(FoodItem item) {
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
  
  void _navigateToRecipeList(List<FoodItem> items) {
    if (items.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('재료가 없어요.')));
      return;
    }
    Navigator.push(
      context,
      MaterialPageRoute(builder: (context) => RecipeListScreen(items: items)),
    );
  }

  void _navigateToHistory() {
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

  List<FoodItem> _getFilteredAndSortedItems() {  // 필터 및 정렬
    List<FoodItem> items = _mockFoodItems.where((item) {
      if (_selectedStorageFilter != null && item.storageLocation != _selectedStorageFilter) return false;
      if (_selectedCategoryFilter != null && item.category != _selectedCategoryFilter) return false;
      if (_searchQuery.isNotEmpty && !item.name.contains(_searchQuery)) return false;
      return true;
    }).toList();

    items.sort((a, b) {
      int result = 0;
      switch (_sortOption) {
        case SortOption.expiryDate: result = a.expiryDate.compareTo(b.expiryDate); break;
        case SortOption.name: result = a.name.compareTo(b.name); break;
        case SortOption.quantity: result = a.quantity.compareTo(b.quantity); break;
      }
      return _isAscending ? result : -result;
    });
    return items;
  }

  void _showFilterModal(BuildContext context) {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.white, 
      shape: const RoundedRectangleBorder(borderRadius: BorderRadius.vertical(top: Radius.circular(20))),
      builder: (ctx) {
        return StatefulBuilder( 
          builder: (BuildContext context, StateSetter setModalState) {
            return DraggableScrollableSheet(
              initialChildSize: 0.5,
              minChildSize: 0.4,
              maxChildSize: 0.8,
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
                            backgroundColor: Colors.white,
                            selectedColor: Colors.grey[200],
                            onSelected: (bool selected) {
                              setModalState(() => _selectedStorageFilter = null);
                              setState(() {});
                            },
                          ),
                          ...StorageLocation.values.map((loc) => FilterChip(
                            label: Text(_getStorageKoreanName(loc)),
                            selected: _selectedStorageFilter == loc,
                            backgroundColor: Colors.white,
                            selectedColor: Colors.grey[200],
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
                            backgroundColor: Colors.white,
                            selectedColor: Colors.grey[200],
                            onSelected: (bool selected) {
                              setModalState(() => _selectedCategoryFilter = null);
                              setState(() {});
                            },
                          ),
                          ..._sortedCategories.map((cat) => FilterChip(
                            label: Text(_getCategoryKoreanName(cat)),
                            selected: _selectedCategoryFilter == cat,
                            backgroundColor: Colors.white,
                            selectedColor: Colors.grey[200],
                            onSelected: (bool selected) {
                              setModalState(() => _selectedCategoryFilter = selected ? cat : null);
                              setState(() {});
                            },
                          )),
                        ],
                      ),
                      const SizedBox(height: 30),
                      SizedBox(
                        width: double.infinity,
                        child: ElevatedButton(
                          onPressed: () => Navigator.pop(ctx),
                          style: ElevatedButton.styleFrom(
                            padding: const EdgeInsets.symmetric(vertical: 12),
                            backgroundColor: const Color(0xFF0F172A),
                          ),
                          child: const Text('확인', style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: Colors.white)),
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

  Future<void> _pickImageAndProcess(ImageSource source) async {
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
            SnackBar(content: Text('${confirmedItems.length}개의 품목을 추가했어요.')),
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
      backgroundColor: Colors.white,
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
                title: const Text('이미지로 입력'),
                onTap: () {
                  Navigator.pop(ctx);
                  _pickImageAndProcess(ImageSource.gallery);
                },
              ),
              ListTile(
                leading: const Icon(Icons.edit_note),
                title: const Text('직접 입력'),
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
    final resultItem = await showDialog<FoodItem>(
      context: context,
      barrierDismissible: false, 
      builder: (context) => AddItemScreen(existingItem: existingItem),
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
        SnackBar(content: Text('식재료를 ${existingItem != null ? '수정' : '등록'}했어요.')),
      );
    }
  }

  void _showEditDeleteModal(BuildContext context, FoodItem item) {
    showModalBottomSheet(
      context: context,
      backgroundColor: Colors.white,
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
      backgroundColor: Colors.grey[50], 
      appBar: AppBar(
        title: const Text('나의 냉장고'),
        backgroundColor: Colors.grey[50],
        surfaceTintColor: Colors.grey[50],
        leading: IconButton(
          icon: const Icon(Icons.menu), 
          onPressed: () => _showFilterModal(context),
        ),
        actions: [
          IconButton(
            icon: const Icon(Icons.history),
            tooltip: '사용/폐기 기록',
            onPressed: _navigateToHistory,
          ),
          IconButton(
            icon: const Icon(Icons.restaurant_menu), 
            tooltip: '전체 재료로 레시피 추천',
            onPressed: () => _navigateToRecipeList(_mockFoodItems),
          ),
        ],
      ),
      body: Column(
        children: [
          ExpiryBanner(items: _mockFoodItems),

          Expanded(
            child: ListView.builder(
              padding: const EdgeInsets.symmetric(vertical: 8.0),
              itemCount: filteredList.isEmpty ? 2 : filteredList.length + 1,
              itemBuilder: (context, index) {
                if (index == 0) {
                  return Column(
                    children: [
                      Padding(
                        padding: const EdgeInsets.fromLTRB(16, 8, 16, 4),
                        child: TextField(
                          decoration: InputDecoration(
                            hintText: '식재료 검색',
                            prefixIcon: const Icon(Icons.search),
                            filled: true,
                            fillColor: Colors.white,
                            border: OutlineInputBorder(borderRadius: BorderRadius.circular(10)),
                            contentPadding: const EdgeInsets.symmetric(horizontal: 10),
                            isDense: true,
                          ),
                          onChanged: (value) {
                            setState(() {
                              _searchQuery = value;
                            });
                          },
                        ),
                      ),
                      Padding(
                        padding: const EdgeInsets.symmetric(horizontal: 16.0),
                        child: Row(
                          mainAxisAlignment: MainAxisAlignment.end,
                          children: [
                            DropdownButton<SortOption>(
                              value: _sortOption,
                              icon: const Icon(Icons.sort, size: 18),
                              style: const TextStyle(fontSize: 13, color: Colors.black87),
                              underline: Container(), 
                              isDense: true, 
                              dropdownColor: Colors.white,
                              alignment: AlignmentDirectional.centerEnd,
                              onChanged: (SortOption? newValue) {
                                if (newValue != null) {
                                  setState(() => _sortOption = newValue);
                                }
                              },
                              items: const [
                                DropdownMenuItem(value: SortOption.expiryDate, child: Text('유통기한')),
                                DropdownMenuItem(value: SortOption.name, child: Text('이름')),
                                DropdownMenuItem(value: SortOption.quantity, child: Text('수량')),
                              ],
                            ),
                            const SizedBox(width: 12),
                            DropdownButton<bool>(
                              value: _isAscending,
                              icon: Icon(_isAscending ? Icons.arrow_upward : Icons.arrow_downward, size: 16),
                              style: const TextStyle(fontSize: 13, color: Colors.black87),
                              underline: Container(),
                              isDense: true,
                              dropdownColor: Colors.white,
                              alignment: AlignmentDirectional.centerEnd,
                              onChanged: (bool? newValue) {
                                if (newValue != null) {
                                  setState(() => _isAscending = newValue);
                                }
                              },
                              items: const [
                                DropdownMenuItem(value: true, child: Text('오름차순')),
                                DropdownMenuItem(value: false, child: Text('내림차순')),
                              ],
                            ),
                          ],
                        ),
                      ),
                    ],
                  );
                }

                if (filteredList.isEmpty) {
                  return const Padding(
                    padding: EdgeInsets.only(top: 50.0),
                    child: Center(child: Text('조건에 맞는 식재료가 없어요.')),
                  );
                }

                final item = filteredList[index - 1];
                return FoodItemCard(
                  item: item,
                  onTap: () => _showRecipeDialog(context, item),
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
        backgroundColor: const Color(0xFF0F172A),
        foregroundColor: Colors.white,
        child: const Icon(Icons.add),
      ),
    );
  }
}