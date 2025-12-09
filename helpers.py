import re

def sanitize_filename(filename):
    """تنظيف اسم الملف من الأحغير غير الآمنة"""
    # إزالة الأحغير غير المسموح بها
    filename = re.sub(r'[<>:"/\\|?*]', '', filename)
    filename = re.sub(r'\s+', ' ', filename)
    filename = filename.strip()
    
    # تحديد طول معقول
    if len(filename) > 100:
        filename = filename[:100]
    
    return filename

def format_file_size(bytes_size):
    """تنسيق حجم الملف"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_size < 1024.0:
            return f"{bytes_size:.1f} {unit}"
        bytes_size /= 1024.0
    return f"{bytes_size:.1f} TB"
