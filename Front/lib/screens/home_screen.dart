import 'package:flutter/material.dart';
import '../models/food_item.dart';
import '../widgets/food_item_card.dart';
import '../widgets/expiry_banner.dart';
import './add_item_screen.dart';
import './recipe_list_screen.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  StorageLocation? _selectedFilter;
  String _appBarTitle = '전체';

  final List<FoodItem> _mockFoodItems = [
    FoodItem(
      id: '1',
      name: '감자',
      quantity: 5,
      unit: '개',
      category: FoodCategory.vegetable,
      storageLocation: StorageLocation.roomTemperature,
      expiryDate: DateTime.now().add(const Duration(days: 2)),
    ),
    FoodItem(
      id: '2',
      name: '우유',
      quantity: 1,
      unit: '개',
      category: FoodCategory.dairy,
      storageLocation: StorageLocation.refrigerated,
      expiryDate: DateTime.now().add(const Duration(days: 6)),
    ),
    FoodItem(
      id: '3',
      name: '계란',
      quantity: 10,
      unit: '개',
      category: FoodCategory.dairy,
      storageLocation: StorageLocation.refrigerated,
      expiryDate: DateTime.now().subtract(const Duration(days: 6)),
    ),
    FoodItem(
      id: '4',
      name: '냉동 만두',
      quantity: 1,
      unit: '봉지',
      category: FoodCategory.frozen,
      storageLocation: StorageLocation.frozen,
      expiryDate: DateTime.now().add(const Duration(days: 90)),
    ),
  ];

  void _incrementQuantity(FoodItem item) {
    setState(() {
      item.quantity = item.quantity + 1;
    });
  }

  void _decrementQuantity(FoodItem item) {
    setState(() {
      if (item.quantity > 1) {
        item.quantity = item.quantity - 1;
      } else {
        _mockFoodItems.remove(item);
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('${item.name} 항목을 모두 사용했습니다 (삭제됨).')),
        );
      }
    });
  }

  void _showFilterModal(BuildContext context) {
    showModalBottomSheet(
      context: context,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      builder: (ctx) {
        
        Widget buildFilterButton(String title, StorageLocation? filterValue) {
          final bool isSelected = _selectedFilter == filterValue;
          return Padding(
            padding: const EdgeInsets.symmetric(vertical: 4.0),
            child: ListTile(
              title: Text(
                title,
                style: TextStyle(
                  color: isSelected ? Colors.white : Colors.black,
                  fontWeight: isSelected ? FontWeight.bold : FontWeight.normal,
                ),
              ),
              tileColor: isSelected ? Colors.black87 : Colors.white,
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(10),
                side: BorderSide(color: isSelected ? Colors.transparent : Colors.grey.shade200)
              ),
              onTap: () {
                setState(() {
                  _selectedFilter = filterValue;
                  _appBarTitle = title;
                });
                Navigator.pop(ctx);
              },
            ),
          );
        }

        return Container(
          padding: const EdgeInsets.fromLTRB(20, 20, 20, 40),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            mainAxisSize: MainAxisSize.min,
            children: [
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Text(
                    '보관 위치 선택',
                    style: Theme.of(context).textTheme.titleLarge?.copyWith(fontWeight: FontWeight.bold),
                  ),
                  IconButton(
                    icon: const Icon(Icons.close),
                    onPressed: () => Navigator.pop(ctx),
                  ),
                ],
              ),
              Text(
                '조회할 보관 위치를 선택하세요',
                style: Theme.of(context).textTheme.bodyMedium?.copyWith(color: Colors.grey[600]),
              ),
              const SizedBox(height: 24),
              buildFilterButton('전체', null),
              buildFilterButton(_getStorageKoreanName(StorageLocation.refrigerated), StorageLocation.refrigerated),
              buildFilterButton(_getStorageKoreanName(StorageLocation.frozen), StorageLocation.frozen),
              buildFilterButton(_getStorageKoreanName(StorageLocation.roomTemperature), StorageLocation.roomTemperature),
            ],
          ),
        );
      },
    );
  }
  
  String _getStorageKoreanName(StorageLocation location) {
    switch (location) {
      case StorageLocation.refrigerated:
        return '냉장';
      case StorageLocation.frozen:
        return '냉동';
      case StorageLocation.roomTemperature:
        return '상온';
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
                title: const Text('이미지로 입력'),
                onTap: () {
                  Navigator.pop(ctx);
                  ScaffoldMessenger.of(context).showSnackBar(
                    const SnackBar(content: Text('준비 중입니다.')),
                  );
                },
              ),
              ListTile(
                leading: const Icon(Icons.edit_note),
                title: const Text('수동으로 입력'),
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
          if (index != -1) {
            _mockFoodItems[index] = resultItem;
          }
        } else {
          _mockFoodItems.add(resultItem);
        }
      });
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('${resultItem.name}(이)가 ${existingItem != null ? '수정' : '등록'}되었습니다.')),
      );
    }
  }

  void _navigateToRecipeList(String ingredientName) {
    Navigator.push(
      context,
      MaterialPageRoute(
        builder: (context) => RecipeListScreen(ingredientName: ingredientName),
      ),
    );
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
                title: const Text('수정하기'),
                onTap: () {
                  Navigator.pop(ctx);
                  _navigateAndManageItem(context, existingItem: item);
                },
              ),
              ListTile(
                leading: const Icon(Icons.delete, color: Colors.red),
                title: const Text('삭제하기'),
                onTap: () {
                  Navigator.pop(ctx);
                  _deleteItem(item);
                },
              ),
            ],
          ),
        );
      },
    );
  }

  void _deleteItem(FoodItem item) {
    setState(() {
      _mockFoodItems.remove(item);
    });
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text('${item.name}(을)를 삭제했습니다.')),
    );
  }

  @override
  Widget build(BuildContext context) {
    final List<FoodItem> filteredList;

    if (_selectedFilter == null) {
      filteredList = _mockFoodItems;
    } else {
      filteredList = _mockFoodItems
          .where((item) => item.storageLocation == _selectedFilter)
          .toList();
    }

    final List<FoodItem> sortedList = List.from(filteredList);
    sortedList.sort((a, b) => a.expiryDate.compareTo(b.expiryDate));

    return Scaffold(
      appBar: AppBar(
        title: Text(_appBarTitle),
        leading: IconButton(
          icon: const Icon(Icons.menu),
          onPressed: () {
            _showFilterModal(context);
          },
        ),
        actions: [
        ],
      ),
      body: Column(
        children: [
          ExpiryBanner(items: _mockFoodItems),
          
          Expanded(
            child: ListView.builder(
              itemCount: sortedList.length, 
              itemBuilder: (context, index) {
                final item = sortedList[index]; 
                return FoodItemCard(
                  item: item,
                  onTap: () {
                    _navigateToRecipeList(item.name);
                  },
                  onIncrement: () {
                    _incrementQuantity(item);
                  },
                  onDecrement: () {
                    _decrementQuantity(item);
                  },
                  onLongPress: () {
                    _showEditDeleteModal(context, item);
                  },
                );
              },
            ),
          ),
        ],
      ),
      floatingActionButton: FloatingActionButton(
        onPressed: () {
          _showAddItemModal(context);
        },
        child: const Icon(Icons.add),
      ),
    );
  }
}