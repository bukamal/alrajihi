# Restaurant Bill Adjustments — Phase 33

Implemented touch/checkout support for restaurant bill adjustments:

- Discount amount.
- Service charge amount.
- Tax amount.
- Adjustment notes.
- Balance breakdown: subtotal, discount, service charge, tax, total, paid, remaining.
- Checkout now posts adjustment lines into the generated invoice.

Architecture remains intact: UI -> RestaurantService -> RestaurantGateway -> repository/SQLite boundary.
