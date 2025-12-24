"""
原始数据分表使用示例
展示如何使用新的分表结构来操作数据
"""
from app.utils.raw_data_manager import RawDataManager
from app.models.raw_data import RawDataFactory


def example_create_tables():
    """
    示例：为指定年份创建分表
    """
    print("=== 创建分表示例 ===")

    # 为2023年创建分表
    success = RawDataManager.create_table_for_year(2023)
    print(f"创建2023年分表: {'成功' if success else '失败'}")

    # 批量为多个年份创建分表
    years = [2021, 2022, 2023]
    results = RawDataManager.create_tables_for_years(years)
    for year, success in results.items():
        print(f"创建{year}年分表: {'成功' if success else '失败'}")


def example_insert_data():
    """
    示例：插入数据
    """
    print("
=== 插入数据示例 ===")

    # 插入单条数据
    data = {
        'title': '示例标题',
        'content': '这是示例内容',
        'publish_time': '2023-05-15',
        'answer_url': 'https://example.com/answer/123',
        'author': '示例作者',
        'author_url': 'https://example.com/user/456',
        'author_field': '技术',
        'author_cert': '认证专家',
        'author_fans': 1000,
        'year': 2023,
        'task_id': 1
    }
    success = RawDataManager.insert_data(data)
    print(f"插入单条数据: {'成功' if success else '失败'}")

    # 批量插入数据
    data_list = [
        {
            'title': '示例标题1',
            'content': '这是示例内容1',
            'publish_time': '2023-05-15',
            'answer_url': 'https://example.com/answer/124',
            'author': '示例作者1',
            'author_url': 'https://example.com/user/457',
            'author_field': '技术',
            'author_cert': '认证专家',
            'author_fans': 1000,
            'year': 2023,
            'task_id': 1
        },
        {
            'title': '示例标题2',
            'content': '这是示例内容2',
            'publish_time': '2022-05-15',
            'answer_url': 'https://example.com/answer/125',
            'author': '示例作者2',
            'author_url': 'https://example.com/user/458',
            'author_field': '科学',
            'author_cert': '认证专家',
            'author_fans': 2000,
            'year': 2022,
            'task_id': 2
        }
    ]
    results = RawDataManager.batch_insert_data(data_list)
    for year, count in results.items():
        print(f"批量插入到{year}年分表: {count}条记录")


def example_query_data():
    """
    示例：查询数据
    """
    print("
=== 查询数据示例 ===")

    # 查询所有数据
    all_data = RawDataManager.query_data()
    print(f"查询所有数据: {len(all_data)}条记录")

    # 查询指定年份的数据
    data_2023 = RawDataManager.query_data(years=[2023])
    print(f"查询2023年数据: {len(data_2023)}条记录")

    # 查询指定作者的数据
    author_data = RawDataManager.query_data(author='示例作者')
    print(f"查询作者'示例作者'的数据: {len(author_data)}条记录")

    # 查询指定任务ID的数据
    task_data = RawDataManager.query_data(task_id=1)
    print(f"查询任务ID为1的数据: {len(task_data)}条记录")

    # 分页查询
    page_data = RawDataManager.query_data(limit=5, offset=0)
    print(f"分页查询(第1页，每页5条): {len(page_data)}条记录")


def example_get_statistics():
    """
    示例：获取统计信息
    """
    print("
=== 统计信息示例 ===")

    # 获取所有分表的名称
    table_names = RawDataManager.get_table_names()
    print(f"所有分表: {', '.join(table_names)}")

    # 获取每年分表中的数据量
    data_counts = RawDataManager.get_data_count_by_year()
    for year, count in data_counts.items():
        print(f"{year}年分表中的数据量: {count}条")


def example_direct_model_usage():
    """
    示例：直接使用模型操作数据
    """
    print("
=== 直接使用模型示例 ===")

    # 获取2023年的模型
    model_2023 = RawDataFactory.get_model(2023)
    print(f"2023年模型类名: {model_2023.__name__}")
    print(f"2023年表名: {model_2023.__tablename__}")

    # 使用模型创建实例
    data = {
        'title': '直接使用模型创建的标题',
        'content': '直接使用模型创建的内容',
        'publish_time': '2023-06-15',
        'answer_url': 'https://example.com/answer/126',
        'author': '模型作者',
        'author_url': 'https://example.com/user/459',
        'author_field': '技术',
        'author_cert': '认证专家',
        'author_fans': 1500,
        'year': 2023,
        'task_id': 3
    }

    # 使用RawData.create_instance方法创建实例
    instance = RawDataFactory.get_model(2023)(**data)
    print(f"创建的实例: {instance}")

    # 保存到数据库
    from app.database import SessionLocal
    db = SessionLocal()
    try:
        db.add(instance)
        db.commit()
        print("数据保存成功")
    except Exception as e:
        print(f"数据保存失败: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    # 运行所有示例
    example_create_tables()
    example_insert_data()
    example_query_data()
    example_get_statistics()
    example_direct_model_usage()
