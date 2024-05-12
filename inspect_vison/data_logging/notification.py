from abc import ABC, abstractmethod
import typing as tp
import warnings

class Notificator(ABC):
    def __init__(self, update_values: dict[str, tp.Any] | None = None):
        self.__update_values = update_values
        self.updated_flag = False

    def update(self, update_values):
        self.update_values = update_values
        self.updated_flag = True

    @property
    def value(self):
        return self.__update_values

    @abstractmethod
    def check_conditions(self) -> list[tuple[bool, str]]:
        pass

    def aware(self):
        if not self.updated_flag:
            warnings.warn("You haven't update values from the last call of aware")
        awareness: list[str] = []
        for condition, message in self.check_conditions():
            if condition:
                awareness.append(message)
        self.updated_flag = False
        return "\n".join(awareness)