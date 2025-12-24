
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.services.exporter import get_export_files, export_sample_data_to_excel, export_RawData_data_to_excel
import os

router = APIRouter(prefix="/api/exports", tags=["导出文件"])

@router.get("/")
async def get_exports():
    """获取导出文件列表"""
    try:
        exports = get_export_files()
        return exports
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取导出文件失败: {str(e)}"
        )

@router.post("/export-sample-data", status_code=status.HTTP_202_ACCEPTED)
async def export_sample_data(background_tasks: BackgroundTasks):
    """导出抽样数据"""
    # 添加后台任务
    background_tasks.add_task(export_sample_data_to_excel)
    return {"message": "导出任务已启动"}

@router.post("/export-raw-data", status_code=status.HTTP_202_ACCEPTED)
async def export_raw_data(background_tasks: BackgroundTasks):
    """导出原始数据"""
    # 添加后台任务
    background_tasks.add_task(export_RawData_data_to_excel)
    return {"message": "导出任务已启动"}

@router.get("/download/{filename}")
async def download_export(filename: str):
    """下载导出文件"""
    export_dir = os.path.join(os.getcwd(), "exports")
    file_path = os.path.join(export_dir, filename)

    if not os.path.exists(file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"文件 {filename} 不存在"
        )

    return FileResponse(
        path=file_path,
        filename=filename,
        media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )

@router.delete("/delete/{filename}")
async def delete_export(filename: str):
    """删除导出文件"""
    export_dir = os.path.join(os.getcwd(), "exports")
    file_path = os.path.join(export_dir, filename)
    
    if not os.path.exists(file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"文件 {filename} 不存在"
        )
    
    try:
        os.remove(file_path)
        return {"message": f"文件 {filename} 删除成功"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除文件失败: {str(e)}"
        )
