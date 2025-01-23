# SQL Agent Best Practices

## Query Writing

### 1. Be Specific
Instead of:
```
"Show me orders"
```
Better:
```
"Show me orders from last month with amount over $1000"
```

### 2. Use Natural Language
Instead of:
```
"SELECT * FROM orders WHERE amount > 1000"
```
Better:
```
"Find all orders with amount greater than $1000"
```

## Performance Optimization

### 1. Limit Results
For large tables, specify limits:
```python
request = QueryRequest(
    question="Show me recent orders",
    max_results=100
)
```

### 2. Use Appropriate Timeframes
Specify reasonable time ranges:
```python
request = QueryRequest(
    question="Show me orders from the last 30 days"
)
```

## Error Handling

### 1. Validate Input
Always validate user input before processing:
```python
if not question.strip():
    raise ValueError("Question cannot be empty")
```

### 2. Handle Timeouts
Set appropriate timeouts for long-running queries:
```python
request = QueryRequest(
    question="Complex analysis query",
    timeout=60.0  # 60 seconds timeout
)
```

## Security

### 1. Use Query Validation
Always validate generated queries:
```python
is_valid, error = validator.validate(query)
if not is_valid:
    raise ValidationError(error)
```

### 2. Sanitize Input
Never pass raw user input to queries:
```python
# Bad
f"SELECT * FROM users WHERE name = '{user_input}'"

# Good
query = "SELECT * FROM users WHERE name = :name"
params = {"name": user_input}
```

## Feedback Collection

### 1. Track Query Performance
```python
feedback_collector.add_feedback(
    query_result=result,
    feedback_type="performance",
    feedback_text=f"Query took {result.execution_time:.2f} seconds"
)
```

### 2. Learn from Failures
```python
feedback_collector.add_feedback(
    query_result=result,
    feedback_type="failure",
    feedback_text="Query timeout - needs optimization"
)
``` 