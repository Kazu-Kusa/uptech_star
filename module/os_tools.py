import json
import os
import re
import warnings
from abc import ABCMeta, abstractmethod
from ctypes import CDLL, cdll
from functools import wraps, singledispatch, lru_cache
from typing import Optional, List, Dict, final, Any, Sequence, Set

from dill import dump, load

from ..constant import LIB_DIR_PATH

CONFIG_PATH_PATTERN = r"[\\/]"


# region get_config
@singledispatch
def get_config(body, chain: Sequence[str]) -> Any:
    """
    get config recursively form the nested dict
    Args:
        body (dict):
        chain ():

    Returns:

    """
    raise KeyError("The chain is conflicting")


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


# endregion


# region make_config
@singledispatch
def make_config(body, chain: Sequence[str], value) -> Dict:
    """
    inject config to a nested dict
    Args:
        body (dict):
        chain ():
        value ():

    Returns:

    """
    # indicating the given chain will override some other value in the config
    # normally, re-register a config value is allowed
    raise KeyError("The chain is conflicting")


@make_config.register(dict)
def _(body, chain: Sequence[str], value) -> Dict:
    if len(chain) == 1:
        # Store the value
        body[chain[0]] = value
        return body
    else:
        # recursive call util the chain is empty

        # here is to deal with two different situations
        # first is the situation,
        # in which the body doesn't contain the key named chain[0],indicating that
        # there is no existed nested Dict.For that here parse a None as the body,
        # which prevents body[chain[0]] raise the KeyError

        # second is the situation, in which the body does contain the key named chain[0],indicating that
        # there should be a nested Dict.For that here parse the nested Dict as the Body,
        # which may contain other configurations
        body[chain[0]] = make_config(
            body[chain[0]] if chain[0] in body else None, chain[1:], value
        )
        return body


@make_config.register(type(None))
def _(body, chain: Sequence[str], value) -> Dict:
    if len(chain) == 1:
        # Store the value
        return {chain[0]: value}
    else:
        # recursive call util the chain is empty
        return {chain[0]: make_config(None, chain[1:], value)}


# endregion


# TODO to deal with object that may not support serializing, consider add a save rule to remove those
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
            with open(self._cache_file_path, "rb") as f:
                return load(f)
        except FileNotFoundError:
            warnings.warn("No existing CacheFile", stacklevel=4)
            return {}
        except EOFError:
            warnings.warn("Bad CacheFile, executing removal", stacklevel=4)
            os.remove(self._cache_file_path)
            return {}

    def save_cache(self) -> None:
        # 保存缓存到文件
        with open(self._cache_file_path, "wb") as f:
            dump(self.content, f)

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
    """
    Abc class to build a child class which can load config form json

    Notes:
        DO NOT USE null as value in the json,the loader will not load that, instead, it will apply
        the default value defined in the child class
    """

    def __init__(self, config_path: Optional[str]):
        self._config_path = config_path
        self._config: Dict = {}
        self._config_registry: Set[str] = set()
        self.register_all_config()
        if config_path:
            warnings.warn(f"\nLoading config at: {config_path}", stacklevel=3)
        else:
            warnings.warn(
                "\nConfig path is not specified, default config will be applied",
                stacklevel=3,
            )
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
    def register_config(
            self, config_registry_path: str, value: Optional[Any] = None
    ) -> None:
        """
        Registers the value at the specified location in the nested dictionary _config.
        The operation will override the original value
        :param config_registry_path:  list of keys representing the nested location in the dictionary.
        :param value: The value to be registered.
        :return: None
        """

        self._config_registry.add(config_registry_path)
        # TODO may refactor this chain maker to a named def
        config_registry_path_chain: List[str] = re.split(
            pattern=CONFIG_PATH_PATTERN, string=config_registry_path
        )

        self._config = make_config(self._config, config_registry_path_chain, value)

    @staticmethod
    def export_config(config_body: Dict, config_registry_path: str) -> Optional[Any]:
        """
        Exports the value at the specified location in the nested dictionary _config.

        Args:
            config_body: the nested dictionary that contains the value.
            config_registry_path: A list of keys representing the nested location in the dictionary.
        :return: The value at the specified location.
        """
        config_registry_path_chain: List[str] = re.split(
            pattern=CONFIG_PATH_PATTERN, string=config_registry_path
        )

        return get_config(config_body, config_registry_path_chain)

    @final
    def save_config(self, save_path: Optional[str] = None) -> None:
        """
        Saves the configuration to a file.
        Will execute override save on origin file when the config path is not specified

        :param save_path: The path to the file.
        :return: None
        """

        with open(save_path if save_path else self._config_path, mode="w") as f:
            json.dump(self._config, f, indent=2)

    @final
    def load_config(self, config_path: Optional[str]) -> None:
        """
        used to load the important configurations.
        will override the default configuration in the self._config.
        :param config_path:
        :return:
        """
        if config_path:
            with open(config_path, mode="r") as f:
                temp_config = json.load(f)
        else:
            temp_config = {}
        for config_registry_path in self._config_registry:
            config = self.export_config(temp_config, config_registry_path)
            self.register_config(
                config_registry_path, config
            ) if config is not None else None

    @final
    def inject_config(self):
        """
        inject the self._config into the instance
        :return:
        """
        for config_registry_path in self._config_registry:
            if hasattr(self, config_registry_path):
                raise AttributeError(
                    f"CONF: {config_registry_path} is already in the instance"
                )
            setattr(
                self,
                config_registry_path,
                self.export_config(
                    config_body=self._config, config_registry_path=config_registry_path
                ),
            )


def format_json_file(file_path):
    with open(file_path) as file:
        try:
            json_data = json.load(file)
            formatted_json = json.dumps(json_data, indent=4, ensure_ascii=False)
            return formatted_json
        except json.JSONDecodeError as e:
            return f"Failed to parse JSON: {e}"


@lru_cache(maxsize=None)
def load_lib(libname: str) -> CDLL:
    """Load a shared library, with caching"""
    lib_file_name = f"{LIB_DIR_PATH}/{libname}"
    print(f"Loading [{lib_file_name}]")
    return cdll.LoadLibrary(lib_file_name)
