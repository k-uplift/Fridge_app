import 'dart:io';
import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';
import 'package:shared_preferences/shared_preferences.dart';
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
import './login_screen.dart'; 

enum SortOption { expiryDate, name, quantity }

class HomeScreen extends StatefulWidget {
  final String userId; 

  const HomeScreen({super.key, required this.userId});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  String _fridgeNickname = '나의 냉장고';

  StorageLocation? _selectedStorageFilter;
  FoodCategory? _selectedCategoryFilter;
  String _searchQuery = '';
  
  SortOption _sortOption = SortOption.expiryDate;
  bool _isAscending = true; 

  final OcrService _ocrService = OcrService();
  final List<HistoryItem> _historyItems = [];
  
  List<FoodItem> _mockFoodItems = []; 

  @override
  void initState() {
    super.initState();
    _loadUserItems();
  }

  Future<void> _loadUserItems() async { // 사용자별 데이터 저장 및 불러오기
    final prefs = await SharedPreferences.getInstance();
    
    setState(() {
      _fridgeNickname = prefs.getString('nickname_${widget.userId}') ?? '나의 냉장고';
    });

    final String? jsonString = prefs.getString('food_items_${widget.userId}');
    if (jsonString != null) {
      final List<dynamic> jsonList = jsonDecode(jsonString);
      setState(() {
        _mockFoodItems = jsonList.map((jsonItem) => _fromJson(jsonItem)).toList();
      });
    } else {
      setState(() {
        _mockFoodItems = [];
      });
    }
  }

  Future<void> _saveUserItems() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString('nickname_${widget.userId}', _fridgeNickname);
    final String jsonString = jsonEncode(_mockFoodItems.map((item) => _toJson(item)).toList());
    await prefs.setString('food_items_${widget.userId}', jsonString);
  }

  Map<String, dynamic> _toJson(FoodItem item) {
    return {
      'id': item.id,
      'name': item.name,
      'quantity': item.quantity,
      'unit': item.unit,
      'category': item.category.index,
      'storageLocation': item.storageLocation.index,
      'expiryDate': item.expiryDate.toIso8601String(),
    };
  }

  FoodItem _fromJson(Map<String, dynamic> json) {
    return FoodItem(
      id: json['id'],
      name: json['name'],
      quantity: json['quantity'],
      unit: json['unit'],
      category: FoodCategory.values[json['category']],
      storageLocation: StorageLocation.values[json['storageLocation']],
      expiryDate: DateTime.parse(json['expiryDate']),
    );
  }

  List<FoodCategory> get _sortedCategories {   
    final categories = FoodCategory.values.toList();
    categories.sort((a, b) {
      if (a == FoodCategory.etc) return 1;
      if (b == FoodCategory.etc) return -1;
      return _getCategoryKoreanName(a).compareTo(_getCategoryKoreanName(b));
    });
    return categories;
  }

  void _showLogoutDialog() { // 로그아웃 확인 팝업
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        backgroundColor: Colors.white,
        surfaceTintColor: Colors.white,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
        title: const Text("로그아웃", style: TextStyle(fontWeight: FontWeight.bold, fontSize: 18)),
        content: const Text("로그아웃을 할까요?"),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx),
            child: const Text("취소", style: TextStyle(color: Colors.grey)),
          ),
          ElevatedButton(
            onPressed: () {
              Navigator.pop(ctx); // 팝업 닫기
              
              Navigator.pushAndRemoveUntil( // 로그인 화면으로 이동
                context,
                MaterialPageRoute(builder: (context) => const LoginScreen()),
                (route) => false,
              );

              ScaffoldMessenger.of(context).showSnackBar( // 로그아웃 알림 띄우기
                const SnackBar(
                  content: Text("로그아웃 되었어요."),
                  duration: Duration(seconds: 2),
                ),
              );
            },
            style: ElevatedButton.styleFrom(
              backgroundColor: const Color(0xFF0F172A),
              foregroundColor: Colors.white,
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
            ),
            child: const Text("확인"),
          ),
        ],
      ),
    );
  }

  void _showWithdrawConfirmDialog() { // 회원탈퇴 1단계: 단순 확인 팝업
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        backgroundColor: Colors.white,
        surfaceTintColor: Colors.white,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
        title: const Text("회원탈퇴", style: TextStyle(fontWeight: FontWeight.bold, fontSize: 18)),
        content: const Text("회원탈퇴를 할까요?"),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx),
            child: const Text("취소", style: TextStyle(color: Colors.grey)),
          ),
          ElevatedButton(
            onPressed: () {
              Navigator.pop(ctx); // 1차 팝업 닫기
              showDialog( // 2차 팝업(비밀번호 입력) 띄우기
                context: context,
                barrierDismissible: false,
                builder: (context) => WithdrawPasswordDialog(userId: widget.userId),
              );
            },
            style: ElevatedButton.styleFrom(
              backgroundColor: const Color(0xFF0F172A),
              foregroundColor: Colors.white,
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
            ),
            child: const Text("확인"),
          ),
        ],
      ),
    );
  }

  void _showEditNicknameDialog() {
    final controller = TextEditingController(text: _fridgeNickname);

    showDialog(
      context: context,
      builder: (ctx) => Dialog(
        backgroundColor: Colors.white,
        surfaceTintColor: Colors.white,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
        child: Padding(
          padding: const EdgeInsets.all(20),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Text('별명 설정하기', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
              const SizedBox(height: 16),
              TextField(
                controller: controller,
                autofocus: true,
                decoration: InputDecoration(
                  hintText: '별명을 입력하세요',
                  filled: true,
                  fillColor: Colors.grey[100],
                  border: OutlineInputBorder(
                    borderRadius: BorderRadius.circular(8),
                    borderSide: BorderSide.none,
                  ),
                  contentPadding: const EdgeInsets.symmetric(horizontal: 12, vertical: 12),
                ),
              ),
              const SizedBox(height: 24),
              Row(
                mainAxisAlignment: MainAxisAlignment.end,
                children: [
                  TextButton(
                    onPressed: () => Navigator.pop(ctx),
                    child: const Text('취소', style: TextStyle(color: Colors.grey)),
                  ),
                  const SizedBox(width: 8),
                  ElevatedButton(
                    onPressed: () {
                      if (controller.text.trim().isNotEmpty) {
                        setState(() {
                          _fridgeNickname = controller.text.trim();
                        });
                        _saveUserItems();
                      }
                      Navigator.pop(ctx);
                    },
                    style: ElevatedButton.styleFrom(
                      backgroundColor: const Color(0xFF0F172A),
                      foregroundColor: Colors.white,
                      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
                    ),
                    child: const Text('저장'),
                  ),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }

  String _getParticle(String word) {
    if (word.isEmpty) return '로';
    int code = word.runes.last;
    if (code < 0xAC00 || code > 0xD7A3) return '로'; 
    int jongseong = (code - 0xAC00) % 28;
    if (jongseong == 0 || jongseong == 8) return '로';
    else return '으로';
  }

  String _getObjectParticle(String word) {
    if (word.isEmpty) return '를';
    int code = word.runes.last;
    if (code < 0xAC00 || code > 0xD7A3) return '를';
    int jongseong = (code - 0xAC00) % 28;
    return jongseong == 0 ? '를' : '을';
  }

  Color _getDifficultyColor(String difficulty) {
    switch (difficulty) {
      case '쉬움':
        return Colors.green.shade400;
      case '보통':
        return Colors.orange.shade400;
      case '어려움':
        return Colors.red.shade500;
      default:
        return Colors.grey;
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
                        '${item.name}${_getObjectParticle(item.name)} 활용한 레시피를 선택하세요.',
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
                                                  color: _getDifficultyColor(recipe.difficulty),
                                                  borderRadius: BorderRadius.circular(4),
                                                ),
                                                child: Text(
                                                  recipe.difficulty,
                                                  style: const TextStyle(
                                                    fontSize: 11,
                                                    color: Colors.white,
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
      builder: (ctx) => Dialog(
        backgroundColor: Colors.white,
        surfaceTintColor: Colors.white,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
        child: Stack(
          children: [
            Padding(
              padding: const EdgeInsets.fromLTRB(20, 40, 20, 20),
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Text(
                    isDecrement ? '수량 소진' : '식재료 삭제',
                    style: const TextStyle(fontSize: 20, fontWeight: FontWeight.bold),
                  ),
                  const SizedBox(height: 12),
                  const Text(
                    '어떻게 할까요?',
                    style: TextStyle(fontSize: 15, color: Colors.black87),
                  ),
                  const SizedBox(height: 24),
                  
                  Row(
                    children: [
                      Expanded(
                        child: TextButton(
                          onPressed: () {
                            _processItemHistory(item, HistoryAction.discarded);
                            Navigator.pop(ctx);
                          },
                          style: TextButton.styleFrom(
                            padding: const EdgeInsets.symmetric(vertical: 12),
                            foregroundColor: Colors.red,
                          ),
                          child: const Text(
                            '폐기',
                            style: TextStyle(color: Colors.red, fontWeight: FontWeight.bold, fontSize: 16),
                          ),
                        ),
                      ),
                      const SizedBox(width: 12),
                      Expanded(
                        child: ElevatedButton(
                          onPressed: () {
                            _processItemHistory(item, HistoryAction.used);
                            Navigator.pop(ctx);
                          },
                          style: ElevatedButton.styleFrom(
                            backgroundColor: Colors.green,
                            padding: const EdgeInsets.symmetric(vertical: 12),
                            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
                            elevation: 0,
                          ),
                          child: const Text(
                            '사용완료',
                            style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 16),
                          ),
                        ),
                      ),
                    ],
                  ),
                ],
              ),
            ),
            
            Positioned(
              right: 8,
              top: 8,
              child: IconButton(
                onPressed: () => Navigator.pop(ctx),
                icon: const Icon(Icons.close, color: Colors.grey, size: 24),
                padding: EdgeInsets.zero,
                constraints: const BoxConstraints(),
              ),
            ),
          ],
        ),
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
    _saveUserItems();
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
    _saveUserItems();
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
    _saveUserItems();
  }

  void _decrementQuantity(FoodItem item) {
    if (item.quantity > 1) {
      setState(() {
        item.quantity = item.quantity - 1;
      });
      _saveUserItems();
    } else {
      _confirmDeleteOrUse(item, isDecrement: true);
    }
  }
  
  void _navigateToRecipeList(List<FoodItem> items) {
    if (items.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('식재료를 먼저 추가해주세요.')));
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

  List<FoodItem> _getFilteredAndSortedItems() { 
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
              initialChildSize: 0.6,
              minChildSize: 0.4,
              maxChildSize: 0.8,
              expand: false,
              builder: (context, scrollController) {
                return SingleChildScrollView(
                  controller: scrollController,
                  padding: const EdgeInsets.fromLTRB(20, 30, 20, 20),
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
                      const SizedBox(height: 40),
                      
                      SizedBox(
                        width: double.infinity,
                        child: ElevatedButton(
                          onPressed: () => Navigator.pop(ctx),
                          style: ElevatedButton.styleFrom(
                            padding: const EdgeInsets.symmetric(vertical: 14),
                            backgroundColor: const Color(0xFF0F172A),
                            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                          ),
                          child: const Text('확인', style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: Colors.white)),
                        ),
                      ),
                      
                      const SizedBox(height: 20),

                      Row(
                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                        children: [
                          TextButton(
                            onPressed: () {
                              Navigator.pop(ctx); 
                              _showLogoutDialog(); 
                            },
                            child: const Text(
                              '로그아웃',
                              style: TextStyle(color: Colors.grey, fontSize: 12),
                            ),
                          ),
                          TextButton(
                            onPressed: () {
                              Navigator.pop(ctx);
                              _showWithdrawConfirmDialog(); // 회원탈퇴 확인 팝업 호출
                            },
                            child: const Text(
                              '회원탈퇴',
                              style: TextStyle(color: Colors.grey, fontSize: 12),
                            ),
                          ),
                        ],
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
      case StorageLocation.roomTemperature: return '실온';
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
          _saveUserItems();
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
              Text('식재료 등록하기', style: Theme.of(context).textTheme.titleLarge),
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
      _saveUserItems();
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
        title: GestureDetector(
          onTap: _showEditNicknameDialog,
          child: Row(
            mainAxisSize: MainAxisSize.min,
            children: [
              Text(_fridgeNickname),
              const SizedBox(width: 6),
              const Icon(Icons.edit, size: 16, color: Colors.grey),
            ],
          ),
        ),
        centerTitle: true,
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
                            hintText: '검색',
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
                    child: Center(child: Text('식재료를 등록 해주세요.')),
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

class WithdrawPasswordDialog extends StatefulWidget { // 회원탈퇴시 비밀번호 재확인
  final String userId;
  const WithdrawPasswordDialog({super.key, required this.userId});

  @override
  State<WithdrawPasswordDialog> createState() => _WithdrawPasswordDialogState();
}

class _WithdrawPasswordDialogState extends State<WithdrawPasswordDialog> {
  final TextEditingController _pwController = TextEditingController();
  String? _errorText;

  Future<void> _handleWithdraw() async {
    final inputPw = _pwController.text.trim();
    final prefs = await SharedPreferences.getInstance();
    
    final String? storedPw = prefs.getString(widget.userId);

    if (inputPw == storedPw) { // 계정 삭제
      await prefs.remove(widget.userId);
      await prefs.remove('nickname_${widget.userId}');
      await prefs.remove('food_items_${widget.userId}');
      
      if (!mounted) return;
      Navigator.pop(context);
      
      Navigator.pushAndRemoveUntil(
        context,
        MaterialPageRoute(builder: (context) => const LoginScreen()),
        (route) => false,
      );
      
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text("회원탈퇴가 완료되었어요.")),
      );
    } else {
      setState(() {
        _errorText = "비밀번호가 맞지 않아요.";
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return AlertDialog(
      backgroundColor: Colors.white,
      surfaceTintColor: Colors.white,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
      title: const Text("비밀번호 확인", style: TextStyle(fontWeight: FontWeight.bold, fontSize: 18)),
      content: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text("비밀번호를 다시 입력해주세요."),
          const SizedBox(height: 10),
          TextField(
            controller: _pwController,
            obscureText: true,
            decoration: InputDecoration(
              labelText: "비밀번호",
              errorText: _errorText,
              border: const OutlineInputBorder(),
              contentPadding: const EdgeInsets.symmetric(horizontal: 10, vertical: 10),
            ),
            onChanged: (val) {
              if (_errorText != null) {
                setState(() {
                  _errorText = null;
                });
              }
            },
          ),
        ],
      ),
      actions: [
        TextButton(
          onPressed: () => Navigator.pop(context),
          child: const Text("취소", style: TextStyle(color: Colors.grey)),
        ),
        ElevatedButton(
          onPressed: _handleWithdraw,
          style: ElevatedButton.styleFrom(
            backgroundColor: Colors.red,
            foregroundColor: Colors.white,
            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
          ),
          child: const Text("탈퇴"),
        ),
      ],
    );
  }
}