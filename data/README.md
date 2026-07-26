# SentinelAML Dataset Directory

This directory stores transaction datasets and exported investigation artifacts for SentinelAML.

## Expected CSV Schema

| Column | Type | Description | Example |
| :--- | :--- | :--- | :--- |
| `transaction_id` | String | Unique transaction identifier | `TX0000001` |
| `customer_id` | String | Unique customer identifier | `C0001` |
| `timestamp` | String | Transaction timestamp (`YYYY-MM-DD HH:MM:SS`) | `2026-01-15 14:30:00` |
| `amount` | Float | Transaction amount in USD | `9500.00` |
| `transaction_type` | String | Channel (`cash_deposit`, `cash_withdrawal`, `bank_transfer`, `card_payment`) | `cash_deposit` |
| `country` | String | ISO 2-letter country jurisdiction code | `US` |

## Column Name Tolerance

SentinelAML automatically maps common variations such as `tx_id`, `client_id`, `date`, `val`, `type`, and `location`.
