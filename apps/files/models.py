"""
文件管理模型。

知识点:
  1. FileField: Django 文件字段
  2. content_type: 文件的 MIME 类型
  3. 文件哈希: 去重校验
"""
import hashlib
import os

from django.db import models

from common.base_model import BaseModel
from common.enums import FileType


def upload_path(instance, filename: str) -> str:
    """
    上传路径: /media/{type}/{yyyymm}/{uuid}_{filename}。

    知识点:
      - 函数生成文件路径
      - 按日期分目录
      - UUID 前缀防重名
    """
    import uuid
    from datetime import datetime
    ext = os.path.splitext(filename)[1]
    date_str = datetime.now().strftime("%Y%m")
    new_name = f"{uuid.uuid4().hex}{ext}"
    return f"uploads/{date_str}/{new_name}"


class UploadedFile(BaseModel):
    """上传文件记录。"""

    original_name = models.CharField(verbose_name="原始文件名", max_length=500)
    file = models.FileField(
        verbose_name="文件",
        upload_to=upload_path,
        max_length=500,
    )
    file_size = models.IntegerField(verbose_name="文件大小(字节)", default=0)
    content_type = models.CharField(verbose_name="MIME 类型", max_length=100, blank=True)
    file_type = models.CharField(
        verbose_name="文件分类",
        max_length=20,
        choices=[(f.value, f.name) for f in FileType],
        default=FileType.OTHER.value,
    )
    md5 = models.CharField(verbose_name="MD5", max_length=32, blank=True, db_index=True)

    class Meta:
        db_table = "sys_file"
        verbose_name = "文件"
        verbose_name_plural = "文件列表"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return self.original_name

    def save(self, *args, **kwargs) -> None:
        """保存前计算文件大小和 MD5。"""
        if self.file and not self.file_size:
            self.file_size = self.file.size
        if self.file and not self.md5:
            self.md5 = self._calc_md5()
        super().save(*args, **kwargs)

    def _calc_md5(self) -> str:
        """计算文件 MD5。"""
        md5 = hashlib.md5()
        for chunk in self.file.chunks(8192):
            md5.update(chunk)
        return md5.hexdigest()

    @property
    def url(self) -> str:
        """文件 URL。"""
        return self.file.url if self.file else ""

    @property
    def size_display(self) -> str:
        """可读的文件大小。"""
        size = self.file_size
        for unit in ["B", "KB", "MB", "GB"]:
            if size < 1024:
                return f"{size:.1f}{unit}"
            size /= 1024
        return f"{size:.1f}TB"
