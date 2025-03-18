import hashlib


def get_md5(string: str) -> str:
    """获取字符串的MD5值"""
    md5 = hashlib.md5()
    md5.update(string.encode("utf-8"))
    return md5.hexdigest()
