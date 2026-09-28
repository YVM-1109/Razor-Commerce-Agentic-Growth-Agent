# pyrefly: ignore [missing-import]
from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional
from uuid import UUID

class SessionCreate(BaseModel):
    phone_number: Optional[str] = None

class ProductOut(BaseModel):
    id: UUID; category_id: UUID; name: str; slug: str; sku: str; brand: str
    description: str; price: float; currency: str; specifications: Dict[str, Any] = {}; pc_attributes: Dict[str, Any] = {}
    available: int = 0

class CategoryOut(BaseModel):
    id: UUID; name: str; slug: str

class CartItemIn(BaseModel):
    product_id: UUID; quantity: int = Field(1, ge=1, le=10)

class CartUpdate(BaseModel):
    quantity: int = Field(..., ge=0, le=10)

class ChatIn(BaseModel):
    message: str
    session_id: UUID
    cart_id: Optional[UUID] = None

class ChatOut(BaseModel):
    response: str
    handoff_to_pc_builder: bool = False
    product_suggestions: List[Dict[str, Any]] = []
    discount_offered: Optional[float] = None
    recovery_session_id: Optional[UUID] = None

class BuilderRequirements(BaseModel):
    prompt: Optional[str] = None
    budget: float = Field(..., gt=0)
    use_case: str = "gaming"
    resolution: Optional[str] = "1440p"
    include_peripherals: bool = False

class ApproveBuild(BaseModel):
    version_number: int

class MerchantLogin(BaseModel):
    email: str; password: str

class MerchantConfigIn(BaseModel):
    maximum_discount_pct: float = Field(..., ge=0, le=50)
    maximum_interventions: int = Field(..., ge=1, le=5)
    minimum_cart_value: float = Field(..., ge=0)
