from abc import abstractmethod
from typing import Dict, Any, Hashable, final, Optional, Callable, Union, Sequence

from .actions import ActionFrame, ActionPlayer
from .os_tools import Configurable
from .sensors import SensorHub

DEFAULT_REACTION = tuple()

ComplexAction = Sequence[Optional[ActionFrame]]
ActionFactory = Callable[[Any, ...], ComplexAction]
FlexActionFactory = Callable[[int], ComplexAction]

Reaction = Union[ComplexAction, ActionFactory, Any]


class ReactorBase(Configurable):
    """
    this class provides a way to build a key-value-based robot reacting system
    """

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
        """
        execute the action in the action table
        Args:
            *args:
            **kwargs:

        Returns:

        """
        raise NotImplementedError

    @abstractmethod
    def infer(self, *args, **kwargs) -> Hashable:
        """
        infer form the environment to get a key, which corresponds to the action in the action table
        Args:
            *args:
            **kwargs:

        Returns:

        """
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
        """
        Register the action in the action table
        Args:
            case: the case that the action is for
            complex_action: the action to be registered

        Returns:
            None

        """
        self.__action_table[case] = complex_action

    @final
    @property
    def action_table(self) -> Dict:
        """
        action table that contains all case and actions
        Returns:

        """
        return self.__action_table
