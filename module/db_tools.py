from functools import lru_cache
import pickle


def persistent_lru_cache(CACHE_FILE: str, maxsize: int or None = 128):
    """
    装饰器函数，用于缓存函数调用结果并持久化缓存
    :param maxsize:
    :param CACHE_FILE:
    :return:
    """

    # 从文件中加载缓存，如果文件不存在则返回空字典
    def load_cache():
        try:
            with open(CACHE_FILE, 'rb') as f:
                return pickle.load(f)
        except FileNotFoundError:
            return {}

    # 保存缓存到文件
    def save_cache(cache):
        with open(CACHE_FILE, 'wb') as f:
            pickle.dump(cache, f)

    def decorator(func):
        cache = load_cache()

        @lru_cache(maxsize=maxsize)
        def wrapped(*args, **kwargs):
            # 将参数转换为可哈希的形式
            key = (args, frozenset(kwargs.items()))

            # 检查缓存中是否存在对应的结果
            if key in cache:
                return cache[key]

            # 调用函数并缓存结果
            result = func(*args, **kwargs)
            cache[key] = result

            # 持久化缓存到文件
            save_cache(cache)

            return result

        return wrapped

    return decorator
