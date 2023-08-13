import json
import os
import pickle
import re
import warnings
from abc import ABCMeta, abstractmethod
from ctypes import CDLL, cdll
from functools import wraps, singledispatch
from typing import Optional, List, Dict, final, Any, Sequence

from ..constant import CACHE_DIR_PATH, LIB_DIR_PATH


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
            warnings.warn('No existing CacheFile')
            return {}
        except EOFError:
            warnings.warn("Bad CacheFile, executing removal")
            os.remove(self._cache_file_path)
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


def persistent_cache(cache_file_path: str):
    """
    装饰器函数，用于缓存函数调用结果并持久化缓存
    :param cache_file_path:
    :return:
    """
    cache = CacheFILE(cache_file_path)

    def decorator(func):
        @wraps(func)
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

        return wrapped  # 更新装饰函数的元信息

    return decorator


def makedirs(path: str):
    if not os.path.exists(path):
        os.makedirs(path)


def set_env_var(env_var: str, value: str):
    os.environ[env_var]: str = value
    makedirs(value)


class Configurable(metaclass=ABCMeta):
    def __init__(self, config_path: str):
        self._config: Dict = {}
        self._config_registry: List[str] = []
        self.register_all_config()
        self.load_config(config_path)
        self.inject_config()

    @abstractmethod
    def register_all_config(self):
        """
        register all the config
        :return:
        """
        pass

    @final
    def register_config(self, config_registry_path: str, value: Optional[Any] = None) -> None:
        """
        Registers the value at the specified location in the nested dictionary _config.

        :param config_registry_path: A list of keys representing the nested location in the dictionary.
        :param value: The value to be registered.
        :return: None
        """
        self._config_registry.append(config_registry_path)
        config_registry_path_chain: List[str] = re.split(pattern='\\|/', string=config_registry_path)

        @singledispatch
        def make_config(body, chain: Sequence[str]) -> Dict:
            raise KeyError('The chain is conflicting')

        @make_config.register(dict)
        def _(body, chain: Sequence[str]) -> Dict:
            if len(chain) == 1:
                # Store the value
                body[chain[0]] = value
                return body
            else:
                body[chain[0]] = make_config(body[chain[0]], chain[1:])
                return body

        @make_config.register(type(None))
        def _(body, chain: Sequence[str]) -> Dict:
            if len(chain) == 1:
                return {chain[0]: value}
            else:
                return {chain[0]: make_config(None, chain[1:])}

        self._config = make_config(self._config, config_registry_path_chain)

    @staticmethod
    def export_config(config_body: Dict, config_registry_path: str) -> Optional[Any]:
        """
        Exports the value at the specified location in the nested dictionary _config.

        Args:
            config_body: the nested dictionary that contains the value.
            config_registry_path: A list of keys representing the nested location in the dictionary.
        :return: The value at the specified location.
        """
        config_registry_path_chain: List[str] = re.split(pattern=CONFIG_PATH_PATTERN, string=config_registry_path)

        @singledispatch
        def get_config(body, chain: Sequence[str]) -> Any:
            raise KeyError('The chain is conflicting')

        @get_config.register(dict)
        def _(body: Dict, chain: Sequence[str]) -> Any:
            if len(chain) == 1:
                # Store the value
                return body.get(chain[0])
            else:
                return get_config(body.get(chain[0]), chain[1:])

        @get_config.register(type(None))
        def _(body: Dict, chain: Sequence[str]) -> Any:
            return None

        return get_config(config_body, config_registry_path_chain)

    @final
    def save_config(self, config_path: str) -> None:
        """
        Saves the configuration to a file.

        :param config_path: The path to the file.
        :return: None
        """
        if os.path.exists(config_path):
            os.remove(config_path)
        with open(config_path, mode='w') as f:
            json.dump(self._config, f, indent=4)

    @final
    def load_config(self, config_path: str) -> None:
        """
        used to load the important configurations.
        will override the default configuration in the self._config.
        :param config_path:
        :return:
        """

        with open(config_path, mode='r') as f:
            temp_config = json.load(f)
        for config_registry_path in self._config_registry:
            config = self.export_config(temp_config, config_registry_path)
            if config is not None:
                self.register_config(config_registry_path, config)

    @final
    def inject_config(self):
        """
        inject the self._config into the instance
        :return:
        """
        for config_registry_path in self._config_registry:
            formatted_path = re.sub(pattern=CONFIG_PATH_PATTERN, repl='_', string=config_registry_path)
            if not hasattr(self, formatted_path):
                setattr(self, formatted_path,
                        self.export_config(config_body=self._config, config_registry_path=config_registry_path))


CONFIG_PATH_PATTERN = '\\|/'


def format_json_file(file_path):
    with open(file_path) as file:
        try:
            json_data = json.load(file)
            formatted_json = json.dumps(json_data, indent=4, ensure_ascii=False)
            return formatted_json
        except json.JSONDecodeError as e:
            return f"Failed to parse JSON: {e}"


@persistent_cache(f'{CACHE_DIR_PATH}/lb_cache')
def load_lib(libname: str) -> CDLL:
    lib_file_name = f'{LIB_DIR_PATH}/{libname}'
    print(f'Loading [{lib_file_name}]')
    return cdll.LoadLibrary(lib_file_name)
