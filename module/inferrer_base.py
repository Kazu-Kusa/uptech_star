import json
import os
import re
from abc import ABCMeta, abstractmethod
from functools import singledispatch
from typing import Dict, Any, Hashable, final, Tuple, Optional, Callable, Union, List, Sequence
from .actions import ActionFrame, ActionPlayer
from .sensors import SensorHub

CONFIG_PATH_PATTERN = '\\|/'

DEFAULT_REACTION = tuple()

ComplexAction = Sequence[Optional[ActionFrame], ...]
ActionFactory = Callable[[Any, ...], ComplexAction]
Reaction = Union[ComplexAction, ActionFactory, Any]


class Configurable(metaclass=ABCMeta):
    def __init__(self, config_path: str):
        self._config: Dict = {}
        self._config_registry: List[str] = []
        self.register_all_config()
        self.load_config(config_path)

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

    @final
    def export_config(self, config_registry_path: str) -> Optional[Any]:
        """
        Exports the value at the specified location in the nested dictionary _config.

        :param config_registry_path: A list of keys representing the nested location in the dictionary.
        :return: The value at the specified location.
        """
        config_registry_path_chain: List[str] = re.split(pattern=CONFIG_PATH_PATTERN, string=config_registry_path)

        @singledispatch
        def get_config(body, chain: Sequence[str]) -> Any:
            raise KeyError('The chain is conflicting')

        @get_config.register(dict)
        def _(body, chain: Sequence[str]) -> Any:
            if len(chain) == 1:
                # Store the value
                return body[chain[0]]
            else:
                return get_config(body[chain[0]], chain[1:])

        @get_config.register(type(None))
        def _(body, chain: Sequence[str]) -> Any:
            return None

        return get_config(self._config, config_registry_path_chain)

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
        inject the configurations into the instance
        :param config_path:
        :return:
        """

        with open(config_path, mode='r') as f:
            self._config = json.load(f)
        for config_registry_path in self._config_registry:

            formatted_path = re.sub(pattern=CONFIG_PATH_PATTERN, repl='_', string=config_registry_path)

            if not hasattr(self, formatted_path):
                setattr(self, formatted_path, self.export_config(config_registry_path=config_registry_path))


class InferrerBase(Configurable):
    __action_table: Dict[Hashable, Reaction] = {}

    def __init__(self, sensor_hub: SensorHub, player: ActionPlayer, config_path: str):
        """
        load config into self._config, initiate self._action_table, parse device handle
        :param sensor_hub:
        :param player:
        :param config_path:
        """

        super().__init__(config_path=config_path)
        self._action_table_init()
        self._player: ActionPlayer = player
        self._sensors: SensorHub = sensor_hub

    @abstractmethod
    def _action_table_init(self):
        """
        init the method table
        :return:
        """
        raise NotImplementedError

    @abstractmethod
    def exc_action(self, reaction: Reaction, *args, **kwargs) -> Any:
        raise NotImplementedError

    @abstractmethod
    def infer(self, *args, **kwargs) -> Tuple[Hashable, ...]:
        raise NotImplementedError

    def react(self, *args, **kwargs) -> Any:
        """

        :param args: will be parsed into the inferring section
        :param kwargs: will be parsed into the inferring section
        :return:
        """
        reaction = self.get_action(self.infer(*args, **kwargs))
        return self.exc_action(reaction)

    @final
    def register_action(self, case: Hashable, complex_action: Reaction) -> None:
        self.__action_table[case] = complex_action

    @final
    def get_action(self, case: Hashable) -> Reaction:
        return self.__action_table.get(case, DEFAULT_REACTION)

    @final
    @property
    def action_table(self) -> Dict:
        return self.__action_table
