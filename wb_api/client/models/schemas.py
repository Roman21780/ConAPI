from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class ProductPrice(BaseModel):
    price: float
    currency: str = "RUB"
    discount: Optional[float]

class ProductStock(BaseModel):
    warehouse_id: int = Field(..., alias="warehouseId")
    amount: int

class ProductModel(BaseModel):
    model_id: str = Field(..., alias="modelId")
    sizes: List[str]
    colors: List[str]

class ProductSchema(BaseModel):
    product_id: str = Field(..., alias="productId")
    name: str
    prices: List[ProductPrice]
    stocks: List[ProductStock]
    models: List[ProductModel]
    attributes: dict
    created_at: datetime = Field(..., alias="createdAt")
    updated_at: datetime = Field(..., alias="updatedAt")

class ProductListSchema(BaseModel):
    items: List[ProductSchema]
    total: int

class CategorySchema(BaseModel):
    category_id: int = Field(..., alias="categoryId")
    name: str
    parent_id: Optional[int] = Field(None, alias="parentId")
    children_count: int = Field(..., alias="childrenCount")

class CategoryListSchema(BaseModel):
    items: List[CategorySchema]

class OrderItem(BaseModel):
    item_id: str = Field(..., alias="itemId")
    product_id: str = Field(..., alias="productId")
    quantity: int
    price: float

class OrderSchema(BaseModel):
    order_id: str = Field(..., alias="orderId")
    status: str
    items: List[OrderItem]
    created_at: datetime = Field(..., alias="createdAt")
    total_amount: float = Field(..., alias="totalAmount")

class OrderListSchema(BaseModel):
    items: List[OrderSchema]
    total: int