# Order Status
{% docs order_status_description %}

Order status are one of the following values:

| status        | definition                                          |
|---------------|-----------------------------------------------------|
| approved      | Order approved, not yet created                     |
| delivered     | Order received by Customer                          |
| unavailable   | Order out of stock                                  |
| created       | Order approved and created for delivery to Customer |
| processing    | Order placed, not yet received for approval         |
| canceled      | Order canceled by customer                          |
| invoiced      | Order created and invoice paid by Customer          |
| shipped       | Order shipped, not yet delivered                    |

{% enddocs %}



# Payment type
{% docs payment_type_description %}

Payment types are one of the following values:

| payment_type  | definition                        |
|---------------|-----------------------------------|
| boleto        | payment by ticket                 |
| debit_card    | debit card payment                |
| not_defined   | payment type unknown              |
| credit_card   | credit card payment               |
| voucher       | payment by voucher                |

{% enddocs %}