from abc import ABC, abstractmethod
from pydantic import BaseModel
from typing import Dict, List, Any, Optional, Type

class Table(BaseModel):
    name: str

class TableColumn(BaseModel):
    name: str

class Filter(BaseModel):
    key: str
    value: str

class DataEntity[T: BaseModel](ABC):
    def __init__(self, model_class: Type[T]):
        self.model_class = model_class

    @abstractmethod
    def list(
        self,
        filters: Optional[list[Filter]] = None,
        max: Optional[int] = None,
    ) -> list[T]:
        ...

    @abstractmethod
    def get(
        self,
        id: int,
    ) -> Optional[T]:
        ...

    @abstractmethod
    def get_bulk(
        self,
        ids: list[int],
    ) -> list[T]:
        ...

class TestData[T](DataEntity[T]):
    def __init__(self, model_class: Type[T], data: Dict[str, T]):
        super().__init__(model_class)
        self.data = data

    def list(
        self,
        filters: Optional[list[Filter]] = None,
        max: Optional[int] = None,
    ) -> list[T]:
        return list(self.data.values())

    def get(
        self,
        id: int,
    ) -> Optional[T]:
        return self.data.get(id)

    def get_bulk(
        self,
        ids: list[int],
    ) -> list[T]:
        return [self.data[id] for id in ids if id in self.data]