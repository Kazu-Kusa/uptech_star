import os
from functools import lru_cache
import pickle
from typing import Optional, List, Dict


class CacheFILE:
    __cache_file_register: List[str] = []
    __instance_list: List[object] = []

    def __init__(self, cache_file_path: str):
        self._cache_file_path: str = cache_file_path
        self.__cache_file_register.append(cache_file_path)
        self.content: Dict = self.load_cache()
        self.__instance_list.append(self)

    def load_cache(self) -> Dict:
        # 从文件中加载缓存，如果文件不存在则返回空字典
        try:
            with open(self._cache_file_path, 'rb') as f:
                return pickle.load(f)
        except FileNotFoundError:
            return {}

    def save_cache(self) -> None:
        # 保存缓存到文件
        with open(self._cache_file_path, 'wb') as f:
            pickle.dump(self.content, f)

    @classmethod
    def save_all_cache(cls):
        """
        save all cache that have registered
        :return:
        """
        for cache_file in cls.__instance_list:
            cache_file: cls
            cache_file.save_cache()


def persistent_lru_cache(cache_file_path: str, maxsize: Optional[int] = 128):
    """
    装饰器函数，用于缓存函数调用结果并持久化缓存
    :param maxsize:
    :param cache_file_path:
    :return:
    """
    cache = CacheFILE(cache_file_path)

    def decorator(func):
        @lru_cache(maxsize=maxsize)
        def wrapped(*args, **kwargs):
            # 将参数转换为可哈希的形式
            key = (args, frozenset(kwargs.items()))

            # 检查缓存中是否存在对应的结果
            if key in cache.content:
                return cache.content.get(key)

            # 调用函数并缓存结果
            result = func(*args, **kwargs)
            cache.content[key] = result

            return result

        return wrapped

    return decorator


def makedirs(path: str):
    if not os.path.exists(path):
        os.makedirs(path)


def set_env_var(env_var: str, value: str):
    os.environ[env_var]: str = value
    makedirs(value)
