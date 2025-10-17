"""
Pydantic models for Order Gateway API
Implements FR-3.1: Order submission request/response schemas
"""

from decimal import Decimal
from enum import Enum
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field, field_validator, model_validator


class OrderType(str, Enum):
    """Order type enumeration (FR-2.1 through FR-2.4)"""
    MARKET = "market"
    LIMIT = "limit"
    IOC = "ioc"  # Immediate-Or-Cancel
    FOK = "fok"  # Fill-Or-Kill


class Side(str, Enum):
    """Order side enumeration"""
    BUY = "buy"
    SELL = "sell"


class OrderRequest(BaseModel):
    """
    Order submission request schema
    
    Validates incoming orders per FR-3.1
    Uses Decimal for price/quantity to avoid floating-point errors
    """
    symbol: str = Field(..., description="Trading symbol (e.g., BTC-USDT)")
    order_type: OrderType = Field(..., description="Order type")
    side: Side = Field(..., description="Buy or sell")
    quantity: Decimal = Field(..., gt=0, description="Order quantity (must be > 0)")
    price: Optional[Decimal] = Field(None, gt=0, description="Limit price (required for LIMIT/IOC/FOK)")
    
    @model_validator(mode='after')
    def validate_price_for_order_type(self):
        """
        Validation rules:
        - MARKET orders: price must be None
        - LIMIT/IOC/FOK orders: price is required
        """
        if self.order_type == OrderType.MARKET:
            if self.price is not None:
                raise ValueError("Market orders cannot have a price")
        elif self.order_type in (OrderType.LIMIT, OrderType.IOC, OrderType.FOK):
            if self.price is None:
                raise ValueError(f"{self.order_type.value.upper()} orders require a price")
        
        return self
    
    class Config:
        json_schema_extra = {
            "example": {
                "symbol": "BTC-USDT",
                "order_type": "limit",
                "side": "buy",
                "quantity": "1.5",
                "price": "60000.00"
            }
        }


class OrderResponse(BaseModel):
    """
    Order submission response schema
    
    Returns confirmation per FR-3.1
    """
    order_id: str = Field(..., description="Unique order identifier (UUID)")
    status: str = Field("accepted", description="Order status")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Submission timestamp (UTC)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "order_id": "550e8400-e29b-41d4-a716-446655440000",
                "status": "accepted",
                "timestamp": "2025-10-15T14:30:00.123456"
            }
        }


class ErrorResponse(BaseModel):
    """Error response schema"""
    detail: str = Field(..., description="Error message")
    error_type: str = Field(..., description="Error type classification")

