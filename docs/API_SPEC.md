# API Specification

Base path: `/api`

## Customer Sessions
`POST /sessions`
`PATCH /sessions/{sessionId}`

Anonymous session. Backend generates session ID.

## Products
`GET /products`
`GET /products/{productId}`

## Inventory
`GET /inventory/{productId}`
`POST /inventory/validate`

## Cart
`GET /cart`
`POST /cart/items`
`PATCH /cart/items/{itemId}`
`DELETE /cart/items/{itemId}`
`POST /cart/activity`

## Recovery
`POST /recovery/evaluate`
`POST /recovery/sessions`
`GET /recovery/sessions/{id}`
`POST /recovery/interventions/authorize`

## Agent WebSocket
`/ws/agent/{sessionId}`

Client event:
```json
{"type":"user_message","message":"..."}
```

Server event types:
`connection.ready`, `agent.typing`, `agent.message`, `agent.product_card`, `agent.build_proposal`, `agent.error`, `conversation.ended`, `connection.error`.

## PC Builder
`POST /pc-builder/sessions`
`POST /pc-builder/sessions/{id}/requirements`
`POST /pc-builder/sessions/{id}/generate`
`POST /pc-builder/sessions/{id}/validate`
`POST /pc-builder/sessions/{id}/rebuild`
`POST /pc-builder/sessions/{id}/approve`
`POST /pc-builder/sessions/{id}/commit`

Approval is bound to exact build version.

## Checkout
`POST /orders`
`POST /payments/razorpay/order`
`POST /payments/webhook`

Webhook receives raw body and verifies signature before JSON processing.

## Merchant
`POST /merchant/auth/login`
`GET /merchant/dashboard`
`GET /merchant/analytics/products`
`GET /merchant/daily-summary`
`GET /merchant/config`
`PATCH /merchant/config`

Merchant endpoints require JWT and tenant scope.

## Error Taxonomy
`UNAUTHORIZED`
`FORBIDDEN`
`SESSION_NOT_FOUND`
`PRODUCT_NOT_FOUND`
`PRODUCT_INACTIVE`
`PRODUCT_OUT_OF_STOCK`
`CART_NOT_FOUND`
`CART_NOT_ELIGIBLE`
`RECOVERY_NOT_ELIGIBLE`
`INTERVENTION_LIMIT_REACHED`
`CUSTOMER_OPTED_OUT`
`DISCOUNT_NOT_ALLOWED`
`DISCOUNT_LIMIT_EXCEEDED`
`BUILD_NOT_FOUND`
`BUILD_INVALID`
`BUILD_NOT_APPROVED`
`BUILD_VERSION_STALE`
`BUILD_OUT_OF_STOCK`
`BUILD_OVER_BUDGET`
`BUILD_INCOMPATIBLE`
`ORDER_NOT_FOUND`
`PAYMENT_PENDING`
`PAYMENT_FAILED`
`WEBHOOK_INVALID`
`WEBHOOK_ALREADY_PROCESSED`
`INTERNAL_SERVICE_ERROR`

## API Rules
Client-provided price, total, discount, inventory, payment state, intervention count, and attribution are never authoritative.
