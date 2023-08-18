from abc import ABC, abstractmethod


class FuzzyController(ABC):
    """
    Abstract base class for a single-input fuzzy controller.

    Attributes:
        input_range (tuple): The range of valid input values.
        output_range (tuple): The range of valid output values.
    """

    def __init__(self, input_range, output_range):
        """
        Initializes the FuzzyController with input and output ranges.

        Args:
            input_range (tuple): The range of valid input values.
            output_range (tuple): The range of valid output values.
        """
        self.input_range = input_range
        self.output_range = output_range

    @abstractmethod
    def fuzzify(self, input_value):
        """
        Converts the crisp input value into fuzzy sets.

        Args:
            input_value (float): The crisp input value.

        Returns:
            dict: A dictionary of fuzzy sets with their membership degrees.
        """
        pass

    @abstractmethod
    def defuzzify(self, fuzzy_output):
        """
        Converts the fuzzy output into a crisp output value.

        Args:
            fuzzy_output (dict): A dictionary of fuzzy sets with their membership degrees.

        Returns:
            float: The crisp output value.
        """
        pass

    @abstractmethod
    def rule_evaluation(self, fuzzy_input):
        """
        Evaluates the fuzzy rules and generates fuzzy output.

        Args:
            fuzzy_input (dict): A dictionary of fuzzy sets with their membership degrees.

        Returns:
            dict: A dictionary of fuzzy sets with their membership degrees.
        """
        pass

    def execute(self, input_value):
        """
        Executes the fuzzy control system.

        Args:
            input_value (float): The crisp input value.

        Returns:
            float: The crisp output value.
        """
        fuzzy_input = self.fuzzify(input_value)
        fuzzy_output = self.rule_evaluation(fuzzy_input)
        crisp_output = self.defuzzify(fuzzy_output)
        return crisp_output
