from abc import ABC, abstractmethod

# 工具仓库
tools_registry = {}

class BaseTool(ABC):
    description = ''
    parameters = []

    @abstractmethod
    def call(self, params, **kwargs):
        raise NotImplementedError("Subclasses should implement this!")
    

def register_tool(name):
    def decorator(cls):
        tools_registry[name] = cls
        return cls
    return decorator