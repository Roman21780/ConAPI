from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
from datetime import datetime

class ProductPrice(BaseModel):
    price: float = Field(..., gt=0, description="Цена товара")
    currency: str = Field("RUB", description="Валюта цены")
    discount: Optional[float] = Field(None, ge=0, le=100, description="Размер скидки в процентах")

    @validator('price')
    def round_price(cls, v):
        return round(v, 2)

class ProductStock(BaseModel):
    warehouse_id: int = Field(..., alias="warehouseId", description="ID склада")
    amount: int = Field(..., ge=0, description="Доступное количество товара")

class ProductModel(BaseModel):
    model_id: str = Field(..., alias="modelId", min_length=1, description="ID модели")
    sizes: List[str] = Field(default_factory=list, description="Доступные размеры")
    colors: List[str] = Field(default_factory=list, description="Доступные цвета")

class ProductAttribute(BaseModel):
    name: str
    value: str
    unit: Optional[str]

class ProductSchema(BaseModel):
    product_id: str = Field(..., alias="productId", min_length=1, description="Уникальный ID товара")
    name: str = Field(..., min_length=1, max_length=255, description="Название товара")
    prices: List[ProductPrice] = Field(..., min_items=1, description="Список цен")
    stocks: List[ProductStock] = Field(default_factory=list, description="Наличие на складах")
    models: List[ProductModel] = Field(default_factory=list, description="Модели товара")
    attributes: List[ProductAttribute] = Field(default_factory=list, description="Атрибуты товара")
    created_at: datetime = Field(..., alias="createdAt", description="Дата создания")
    updated_at: datetime = Field(..., alias="updatedAt", description="Дата последнего обновления")
    category_id: Optional[int] = Field(None, alias="categoryId", description="ID категории")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class ProductListSchema(BaseModel):
    items: List[ProductSchema] = Field(default_factory=list, description="Список товаров")
    total: int = Field(..., ge=0, description="Общее количество товаров")
    limit: Optional[int] = Field(None, ge=1, description="Лимит на страницу")
    offset: Optional[int] = Field(None, ge=0, description="Смещение")

class CategorySchema(BaseModel):
    id: int = Field(..., description="ID категории")
    name: str = Field(..., min_length=1, max_length=255, description="Название категории")
    parent_id: Optional[int] = Field(None, alias="parentId", description="ID родительской категории")
    children: List['CategorySchema'] = Field(default_factory=list, description="Дочерние категории")
    is_visible: bool = Field(True, alias="isVisible", description="Видимость категории")

    class Config:
        populate_by_name = True

class CategoryListSchema(BaseModel):
    items: List[CategorySchema] = Field(default_factory=list, description="Список категорий")
    total: int = Field(..., ge=0, description="Общее количество категорий")

class OrderItem(BaseModel):
    item_id: str = Field(..., alias="itemId", description="ID позиции заказа")
    product_id: str = Field(..., alias="productId", description="ID товара")
    quantity: int = Field(..., ge=1, description="Количество товара")
    price: float = Field(..., gt=0, description="Цена за единицу")
    discount: Optional[float] = Field(None, ge=0, le=100, description="Скидка на позицию")

class OrderCustomer(BaseModel):
    name: str = Field(..., min_length=1, description="Имя покупателя")
    phone: Optional[str] = Field(None, description="Телефон покупателя")
    email: Optional[str] = Field(None, description="Email покупателя")

class OrderDelivery(BaseModel):
    address: str = Field(..., description="Адрес доставки")
    city: str = Field(..., description="Город доставки")
    region: Optional[str] = Field(None, description="Регион доставки")

class OrderSchema(BaseModel):
    order_id: str = Field(..., alias="orderId", description="Уникальный ID заказа")
    status: str = Field(..., description="Статус заказа")
    items: List[OrderItem] = Field(..., min_items=1, description="Позиции заказа")
    customer: OrderCustomer = Field(..., description="Информация о покупателе")
    delivery: OrderDelivery = Field(..., description="Информация о доставке")
    created_at: datetime = Field(..., alias="createdAt", description="Дата создания заказа")
    updated_at: datetime = Field(..., alias="updatedAt", description="Дата обновления заказа")
    total_amount: float = Field(..., alias="totalAmount", gt=0, description="Общая сумма заказа")

class OrderListSchema(BaseModel):
    items: List[OrderSchema] = Field(default_factory=list, description="Список заказов")
    total: int = Field(..., ge=0, description="Общее количество заказов")