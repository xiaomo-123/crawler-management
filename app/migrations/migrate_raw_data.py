"""
原始数据迁移脚本
将现有的单表数据迁移到按年份分表的结构中
"""
from typing import Dict, List
from datetime import datetime
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.database import engine
from app.models.raw_data import RawDataFactory
from app.utils.raw_data_manager import RawDataManager


def migrate_raw_data() -> Dict[int, int]:
    """
    迁移原始数据到分表结构
    返回每张表迁移的记录数
    """
    try:
        # 检查原始表是否存在
        with engine.connect() as conn:
            result = conn.execute(text(
                "SELECT COUNT(*) FROM information_schema.tables "
                "WHERE table_schema = DATABASE() AND table_name = 'raw_data'"
            ))
            if result.scalar() == 0:
                print("原始表raw_data不存在，无需迁移")
                return {}

        # 获取原始表中的所有数据
        with Session(engine) as session:
            # 获取所有年份
            years_result = session.execute(text("SELECT DISTINCT year FROM raw_data ORDER BY year"))
            years = [row[0] for row in years_result]

            # 按年份迁移数据
            migration_results = {}
            for year in years:
                print(f"开始迁移 {year} 年的数据...")

                # 获取该年份的数据
                data_result = session.execute(text(
                    f"SELECT * FROM raw_data WHERE year = {year}"
                ))
                data_rows = data_result.fetchall()

                # 转换为字典列表
                data_list = []
                columns = data_result.keys()
                for row in data_rows:
                    data_dict = {column: row[i] for i, column in enumerate(columns)}
                    data_list.append(data_dict)

                # 批量插入到分表
                insert_results = RawDataManager.batch_insert_data(data_list)
                migration_results.update(insert_results)

                print(f"完成迁移 {year} 年的数据，共 {insert_results.get(year, 0)} 条记录")

        return migration_results

    except Exception as e:
        print(f"数据迁移失败: {e}")
        return {}


def backup_original_table() -> bool:
    """
    备份原始表
    """
    try:
        backup_name = f"raw_data_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        with engine.connect() as conn:
            conn.execute(text(f"CREATE TABLE {backup_name} AS SELECT * FROM raw_data"))
            conn.commit()
        print(f"原始表已备份为: {backup_name}")
        return True
    except Exception as e:
        print(f"备份原始表失败: {e}")
        return False


def drop_original_table() -> bool:
    """
    删除原始表（谨慎操作）
    """
    try:
        with engine.connect() as conn:
            conn.execute(text("DROP TABLE raw_data"))
            conn.commit()
        print("原始表已删除")
        return True
    except Exception as e:
        print(f"删除原始表失败: {e}")
        return False


def run_migration() -> None:
    """
    执行完整的数据迁移流程
    1. 备份原始表
    2. 迁移数据到分表
    3. 询问是否删除原始表
    """
    print("开始原始数据迁移流程...")

    # 备份原始表
    if not backup_original_table():
        print("备份失败，终止迁移")
        return

    # 迁移数据
    migration_results = migrate_raw_data()
    total_migrated = sum(migration_results.values())
    print(f"数据迁移完成，共迁移 {total_migrated} 条记录")

    # 显示迁移结果
    for year, count in migration_results.items():
        print(f"- {year} 年: {count} 条记录")

    # 询问是否删除原始表
    user_input = input("是否删除原始表? (y/n): ").lower()
    if user_input == 'y':
        if drop_original_table():
            print("迁移流程完成")
        else:
            print("删除原始表失败，请手动处理")
    else:
        print("保留原始表，迁移流程完成")


if __name__ == "__main__":
    run_migration()
