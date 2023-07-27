from abc import abstractmethod
from typing import Dict, Any, Hashable, final, Tuple, Optional, Callable, Union, Sequence
from .actions import ActionFrame, ActionPlayer
from .db_tools import Configurable
from .sensors import SensorHub

DEFAULT_REACTION = tuple()

ComplexAction = Sequence[Optional[ActionFrame]]
ActionFactory = Callable[[Any, ...], ComplexAction]
Reaction = Union[ComplexAction, ActionFactory, Any]


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
    def exc_action(self, *args, **kwargs) -> Any:
        raise NotImplementedError

    @abstractmethod
    def infer(self, *args, **kwargs) -> Tuple[Hashable, ...]:
        raise NotImplementedError

    @abstractmethod
    def react(self, *args, **kwargs) -> Any:
        """

        :param args: will be parsed into the inferring section
        :param kwargs: will be parsed into the inferring section
        :return:
        """
        raise NotImplementedError

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
