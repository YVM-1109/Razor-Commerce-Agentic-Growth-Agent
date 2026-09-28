import uuid
from sqlalchemy import Column, String, Boolean, Numeric, DateTime, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from app.database import Base


def now_col():
    return Column(DateTime(timezone=True), server_default=func.now())


class Merchant(Base):
    __tablename__ = "merchants"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = now_col(); updated_at = now_col()


class MerchantConfig(Base):
    __tablename__ = "merchant_configs"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    merchant_id = Column(UUID(as_uuid=True), ForeignKey("merchants.id"), unique=True, nullable=False)
    maximum_discount_pct = Column(Numeric(5, 2), default=15.0, nullable=False)
    maximum_interventions = Column(Integer, default=2, nullable=False)
    minimum_cart_value = Column(Numeric(12, 2), default=500.0, nullable=False)
    created_at = now_col(); updated_at = now_col()


class Category(Base):
    __tablename__ = "categories"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, unique=True, nullable=False)
    slug = Column(String, unique=True, nullable=False, index=True)
    is_active = Column(Boolean, default=True, nullable=False)


class Product(Base):
    __tablename__ = "products"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    merchant_id = Column(UUID(as_uuid=True), ForeignKey("merchants.id"), nullable=False)
    category_id = Column(UUID(as_uuid=True), ForeignKey("categories.id"), nullable=False)
    sku = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    slug = Column(String, unique=True, index=True, nullable=False)
    description = Column(String, nullable=False)
    brand = Column(String, nullable=False)
    price = Column(Numeric(12, 2), nullable=False)
    currency = Column(String, default="INR", nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    specifications = Column(JSONB, default=dict, nullable=False)
    pc_attributes = Column(JSONB, default=dict, nullable=False)
    created_at = now_col(); updated_at = now_col()


class Inventory(Base):
    __tablename__ = "inventory"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id"), unique=True, nullable=False)
    quantity = Column(Integer, default=0, nullable=False)
    reserved_qty = Column(Integer, default=0, nullable=False)
    updated_at = now_col()


class ProductCompatibility(Base):
    __tablename__ = "product_compatibility"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id"), nullable=False)
    compatible_product_id = Column(UUID(as_uuid=True), ForeignKey("products.id"), nullable=False)
    compatibility_type = Column(String, nullable=False)
    rules = Column(JSONB, default=dict, nullable=False)


class CustomerSession(Base):
    __tablename__ = "customer_sessions"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    phone_number = Column(String, nullable=True)
    status = Column(String, default="ACTIVE", nullable=False)
    last_activity_at = now_col(); created_at = now_col(); updated_at = now_col()
    expires_at = Column(DateTime(timezone=True), nullable=True)


class Cart(Base):
    __tablename__ = "carts"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_session_id = Column(UUID(as_uuid=True), ForeignKey("customer_sessions.id"), nullable=False)
    status = Column(String, default="ACTIVE", nullable=False)
    currency = Column(String, default="INR", nullable=False)
    subtotal = Column(Numeric(12, 2), default=0, nullable=False)
    discount_total = Column(Numeric(12, 2), default=0, nullable=False)
    total = Column(Numeric(12, 2), default=0, nullable=False)
    last_activity_at = now_col(); created_at = now_col(); updated_at = now_col()


class CartItem(Base):
    __tablename__ = "cart_items"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    cart_id = Column(UUID(as_uuid=True), ForeignKey("carts.id"), nullable=False)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id"), nullable=False)
    quantity = Column(Integer, default=1, nullable=False)
    unit_price = Column(Numeric(12, 2), nullable=False)
    created_at = now_col(); updated_at = now_col()
    __table_args__ = (UniqueConstraint("cart_id", "product_id", name="uq_cart_product"),)


class RecoverySession(Base):
    __tablename__ = "recovery_sessions"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    cart_id = Column(UUID(as_uuid=True), ForeignKey("carts.id"), nullable=False)
    customer_session_id = Column(UUID(as_uuid=True), ForeignKey("customer_sessions.id"), nullable=False)
    status = Column(String, default="ACTIVE", nullable=False)
    eligible_at = Column(DateTime(timezone=True)); started_at = Column(DateTime(timezone=True))
    last_meaningful_agent_interaction_at = Column(DateTime(timezone=True))
    intervention_count = Column(Integer, default=0, nullable=False)
    whatsapp_sent = Column(Integer, default=0, nullable=False)
    customer_opted_out = Column(Boolean, default=False, nullable=False)
    customer_rejected = Column(Boolean, default=False, nullable=False)
    ended_at = Column(DateTime(timezone=True)); created_at = now_col(); updated_at = now_col()


class Intervention(Base):
    __tablename__ = "interventions"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    recovery_session_id = Column(UUID(as_uuid=True), ForeignKey("recovery_sessions.id"), nullable=False)
    sequence_number = Column(Integer, nullable=False)
    status = Column(String, nullable=False)
    reason = Column(String)
    authorized_at = Column(DateTime(timezone=True)); sent_at = Column(DateTime(timezone=True)); completed_at = Column(DateTime(timezone=True))
    created_at = now_col()
    __table_args__ = (UniqueConstraint("recovery_session_id", "sequence_number", name="uq_intervention_sequence"),)


class AgentConversation(Base):
    __tablename__ = "agent_conversations"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_session_id = Column(UUID(as_uuid=True), ForeignKey("customer_sessions.id"), nullable=False)
    recovery_session_id = Column(UUID(as_uuid=True), ForeignKey("recovery_sessions.id"), nullable=True)
    agent_type = Column(String, nullable=False)
    status = Column(String, default="ACTIVE", nullable=False)
    created_at = now_col(); updated_at = now_col()


class AgentMessage(Base):
    __tablename__ = "agent_messages"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("agent_conversations.id"), nullable=False)
    sender_type = Column(String, nullable=False)
    content = Column(String, nullable=False)
    created_at = now_col()
    metadata_ = Column("metadata", JSONB, default=dict, nullable=False)


class AgentEvent(Base):
    __tablename__ = "agent_events"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    agent_type = Column(String, nullable=False)
    event_type = Column(String, nullable=False)
    tool_name = Column(String)
    success = Column(Boolean)
    metadata_ = Column("metadata", JSONB, default=dict, nullable=False)
    created_at = now_col()


class RecoveryEvent(Base):
    __tablename__ = "recovery_events"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    recovery_session_id = Column(UUID(as_uuid=True), ForeignKey("recovery_sessions.id"), nullable=False)
    event_type = Column(String, nullable=False)
    metadata_ = Column("metadata", JSONB, default=dict, nullable=False)
    created_at = now_col()


class PcBuilderSession(Base):
    __tablename__ = "pc_builder_sessions"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_session_id = Column(UUID(as_uuid=True), ForeignKey("customer_sessions.id"), nullable=False)
    status = Column(String, default="REQUIREMENTS", nullable=False)
    budget_max = Column(Numeric(12, 2)); requirements = Column(JSONB, default=dict, nullable=False)
    current_build_version = Column(Integer); created_at = now_col(); updated_at = now_col()


class PcBuildVersion(Base):
    __tablename__ = "pc_build_versions"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    pc_builder_session_id = Column(UUID(as_uuid=True), ForeignKey("pc_builder_sessions.id"), nullable=False)
    version_number = Column(Integer, nullable=False)
    status = Column(String, nullable=False)
    budget_max = Column(Numeric(12, 2)); total_price = Column(Numeric(12, 2))
    compatibility_valid = Column(Boolean, default=False, nullable=False)
    inventory_valid = Column(Boolean, default=False, nullable=False)
    budget_valid = Column(Boolean, default=False, nullable=False)
    customer_approved = Column(Boolean, default=False, nullable=False)
    approved_at = Column(DateTime(timezone=True)); created_at = now_col()
    __table_args__ = (UniqueConstraint("pc_builder_session_id", "version_number", name="uq_build_version"),)


class PcBuildComponent(Base):
    __tablename__ = "pc_build_components"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    build_version_id = Column(UUID(as_uuid=True), ForeignKey("pc_build_versions.id"), nullable=False)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id"), nullable=False)
    component_role = Column(String, nullable=False)
    quantity = Column(Integer, default=1, nullable=False)
    unit_price = Column(Numeric(12, 2), nullable=False)
    is_reused_from_cart = Column(Boolean, default=False, nullable=False)
    created_at = now_col()


class Order(Base):
    __tablename__ = "orders"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    merchant_id = Column(UUID(as_uuid=True), ForeignKey("merchants.id"), nullable=True)
    customer_session_id = Column(UUID(as_uuid=True), ForeignKey("customer_sessions.id"), nullable=False)
    cart_id = Column(UUID(as_uuid=True), ForeignKey("carts.id"), nullable=False)
    status = Column(String, default="CREATED", nullable=False)
    currency = Column(String, default="INR", nullable=False)
    subtotal = Column(Numeric(12, 2), nullable=False)
    discount_total = Column(Numeric(12, 2), default=0, nullable=False)
    total = Column(Numeric(12, 2), nullable=False)
    created_at = now_col(); updated_at = now_col()


class OrderItem(Base):
    __tablename__ = "order_items"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_id = Column(UUID(as_uuid=True), ForeignKey("orders.id"), nullable=False)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id"), nullable=False)
    product_name = Column(String, nullable=False)
    quantity = Column(Integer, nullable=False)
    unit_price = Column(Numeric(12, 2), nullable=False)
    discount_amount = Column(Numeric(12, 2), default=0, nullable=False)
    line_total = Column(Numeric(12, 2), nullable=False)


class Payment(Base):
    __tablename__ = "payments"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_id = Column(UUID(as_uuid=True), ForeignKey("orders.id"), unique=True, nullable=False)
    provider = Column(String, default="razorpay", nullable=False)
    provider_order_id = Column(String, nullable=False)
    provider_payment_id = Column(String)
    amount = Column(Numeric(12, 2), nullable=False)
    currency = Column(String, default="INR", nullable=False)
    status = Column(String, default="CREATED", nullable=False)
    created_at = now_col(); updated_at = now_col()


class PaymentWebhookEvent(Base):
    __tablename__ = "payment_webhook_events"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    provider = Column(String, nullable=False)
    provider_event_id = Column(String, unique=True, nullable=False)
    event_type = Column(String, nullable=False)
    signature_verified = Column(Boolean, default=False, nullable=False)
    payload = Column(JSONB, nullable=False)
    processed = Column(Boolean, default=False, nullable=False)
    processed_at = Column(DateTime(timezone=True)); created_at = now_col()


class Attribution(Base):
    __tablename__ = "attributions"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_id = Column(UUID(as_uuid=True), ForeignKey("orders.id"), unique=True, nullable=False)
    recovery_session_id = Column(UUID(as_uuid=True), ForeignKey("recovery_sessions.id"), nullable=True)
    attribution_type = Column(String, nullable=False)
    meaningful_interaction_at = Column(DateTime(timezone=True)); attribution_window_ends_at = Column(DateTime(timezone=True))
    calculated_at = now_col()
