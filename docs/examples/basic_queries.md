# Basic Query Examples

This guide shows common query patterns using the SQL Agent.

## Simple Queries

### Basic SELECT Query

```python
request = QueryRequest(
    question="Show me all customers"
)
```

Generated SQL:
```sql
SELECT * FROM customers;
```

### Filtered Query

```python
request = QueryRequest(
    question="Show me customers from New York"
)
```

Generated SQL:
```sql
SELECT * FROM customers WHERE city = 'New York';
```

## Time-Based Queries

### Last Month's Data

```python
request = QueryRequest(
    question="Show me orders from last month"
)
```

Generated SQL:
```sql
SELECT * 
FROM orders 
WHERE order_date >= CURRENT_DATE - INTERVAL '1 month';
```

## Aggregation Queries

### Simple Count

```python
request = QueryRequest(
    question="How many customers do we have?"
)
```

Generated SQL:
```sql
SELECT COUNT(*) as customer_count FROM customers;
```

### Group By with Aggregation

```python
request = QueryRequest(
    question="Show me total sales by customer"
)
```

Generated SQL:
```sql
SELECT 
    c.name,
    SUM(o.amount) as total_sales
FROM customers c
JOIN orders o ON c.id = o.customer_id
GROUP BY c.name;
``` 