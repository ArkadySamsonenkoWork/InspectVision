from abc import ABC, abstractmethod

class Notificator(ABC):
    def __init__(self, controlled_objects):
        self.controlled_objects = controlled_objects

    @abstractmethod
    def check_conditions(self) -> list[tuple[bool, str]]:
        pass

    def aware(self):
        awareness: list[str] = []
        for condition, message in self.check_conditions():
            if condition:
                awareness.append(message)
        return "\n".join(awareness)