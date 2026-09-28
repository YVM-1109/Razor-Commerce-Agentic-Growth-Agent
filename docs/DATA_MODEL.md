# Data Model & Migration Specification

## Database
PostgreSQL. Use UTC `TIMESTAMPTZ`. Use exact `NUMERIC(12,2)` for authoritative monetary values.

## Core Tables

### merchants
`id UUID PK, email UNIQUE, password_hash, is_active, created_at, updated_at`

### merchant_configs
`id UUID PK, merchant_id UNIQUE FK, maximum_discount_pct, maximum_interventions, minimum_cart_value, timestamps`

Only these three merchant controls exist.

### categories
`id, name UNIQUE, slug UNIQUE, is_active`

Seed all 11 required categories, including Motherboards.

### products
`id, merchant_id, category_id, sku, name, slug, description, brand, price, currency, is_active, specifications JSONB, pc_attributes JSONB, timestamps`

### inventory
`id, product_id UNIQUE, quantity, reserved_qty, updated_at`
Available = quantity - reserved_qty.

### product_compatibility
`id, product_id, compatible_product_id, compatibility_type, rules JSONB`
Use normalized `pc_attributes` where simpler; document the final implementation choice.

### customer_sessions
`id UUID PK, phone_number nullable, status, last_activity_at, created_at, updated_at, expires_at`
No customer name/email/profile.

### carts
`id, customer_session_id, status, currency, subtotal, discount_total, total, last_activity_at, timestamps`

### cart_items
`id, cart_id, product_id, quantity, unit_price, timestamps`

### recovery_sessions
`id, cart_id, customer_session_id, status, eligible_at, started_at, last_meaningful_agent_interaction_at, intervention_count, whatsapp_sent, customer_opted_out, customer_rejected, ended_at, timestamps`

### interventions
`id, recovery_session_id, sequence_number, status, reason, authorized_at, sent_at, completed_at, created_at`
Unique `(recovery_session_id, sequence_number)`.

### agent_conversations
`id, customer_session_id, recovery_session_id nullable, agent_type, status, timestamps`

### agent_messages
`id, conversation_id, sender_type, content, created_at, metadata JSONB`
Never store chain-of-thought.

### agent_events
Structured activity: agent type, event type, tool name, success, metadata, timestamps.

### recovery_events
Recovery lifecycle event, timestamp, metadata.

### pc_builder_sessions
`id, customer_session_id, status, budget_max, requirements JSONB, current_build_version, timestamps`

### pc_build_versions
`id, pc_builder_session_id, version_number, status, budget_max, total_price, compatibility_valid, inventory_valid, budget_valid, customer_approved, approved_at, created_at`
Unique `(pc_builder_session_id, version_number)`.

### pc_build_components
`id, build_version_id, product_id, component_role, quantity, unit_price, is_reused_from_cart, created_at`

Roles: CPU, GPU, MOTHERBOARD, RAM, STORAGE, PSU, CASE, MONITOR, KEYBOARD, MOUSE, HEADPHONES.

### orders
`id, merchant_id, customer_session_id, cart_id, status, currency, subtotal, discount_total, total, timestamps`

### order_items
`id, order_id, product_id, product_name, quantity, unit_price, discount_amount, line_total`

Historical snapshots are intentional.

### payments
`id, order_id UNIQUE, provider, provider_order_id, provider_payment_id, amount, currency, status, timestamps`

### payment_webhook_events
`id, provider, provider_event_id UNIQUE, event_type, signature_verified, payload JSONB, processed, processed_at, created_at`

### attributions
`id, order_id UNIQUE, recovery_session_id nullable, attribution_type, meaningful_interaction_at, attribution_window_ends_at, calculated_at`

Allowed attribution types: `RECOVERED`, `ORGANIC`.

## State
Use application enums/constants for lifecycle states.

## Migration
Use Alembic. Migrations must be reproducible and version controlled.

## Seed Data
One demo merchant, all 11 categories, representative products, compatible/incompatible PC fixtures, inventory edge cases, and demo merchant configuration.

## Data Authority
Commerce truth is PostgreSQL/application services. LangGraph state is not commerce truth.

## Retention
Retain commerce/payment/attribution/recovery records. No elaborate archival system for MVP.
