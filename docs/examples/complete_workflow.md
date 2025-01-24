# Complete Workflow Example

This example demonstrates the full capabilities of SQL Agent, from schema generation to natural language querying. It shows how to:
1. Generate a database schema from a CSV file
2. Import data while maintaining referential integrity
3. Query the data using natural language

## Code Example

```python
from src.core.agent import SQLAgent
from src.utils.config import Config
from src.models.query import QueryRequest

async def main():
    # Initialize configuration and agent
    config = Config()
    agent = SQLAgent(config)
    
    # Step 1: Generate and Apply Schema
    csv_path = "data/sales_data.csv"
    schema_description = """
    This is a sales dataset containing customer transactions.
    We want to track customer purchase history and analyze sales trends.
    The schema should be optimized for:
    - Customer analytics
    - Sales reporting
    - Inventory management
    - Order tracking
    """
    
    schema = await agent.create_schema_from_csv(
        csv_path=csv_path,
        description=schema_description
    )
    await agent.apply_schema(schema)
    
    # Step 2: Import Data
    schema = await agent.get_schema_from_database()
    await agent.import_csv_data(schema, csv_path)
    
    # Step 3: Query Analysis
    queries = [
        "What are the top 5 products by total sales amount?",
        "Show me the average transaction value by customer segment"
    ]
    
    for question in queries:
        result = await agent.process_request(
            QueryRequest(question=question, include_explanation=True)
        )
        # Process results...
```

## Example Output

Below is the actual output from running the complete workflow:

```
=== Starting Complete Workflow Demo ===

1. Schema Generation Phase
--------------------------
Dropping existing schema...
Existing schema dropped.

Generating schema from CSV...

Generated Schema Structure:

Table: customers
Description: Stores customer information
Columns:
  - customer_id: SERIAL NOT NULL PRIMARY KEY -- Unique identifier for each customer
  - customer_name: VARCHAR(255) NOT NULL -- Name of the customer
  - customer_email: VARCHAR(255) NOT NULL -- Email ID of the customer

Table: products
Description: Stores product information
Columns:
  - product_id: SERIAL NOT NULL PRIMARY KEY -- Unique identifier for each product
  - product_name: VARCHAR(255) NOT NULL -- Name of the product
  - product_category: VARCHAR(255) NOT NULL -- Category that the product belongs to
  - unit_price: DECIMAL(10, 2) NOT NULL -- Price per unit of the product

Table: transactions
Description: Stores transaction information
Columns:
  - transaction_id: SERIAL NOT NULL PRIMARY KEY -- Unique identifier for each transaction
  - customer_id: INTEGER NOT NULL -- References the customer involved in the transaction
  - product_id: INTEGER NOT NULL -- References the product involved in the transaction
  - quantity: INTEGER NOT NULL -- Quantities of product purchased
  - total_amount: DECIMAL(10, 2) NOT NULL -- Total amount paid
  - date: DATE NOT NULL -- Date of the transaction
  - payment_method: VARCHAR(255) NOT NULL -- Method used for payment
  - order_status: VARCHAR(255) NOT NULL -- Current status of the order
Foreign Keys:
  - customer_id -> customers.customer_id
  - product_id -> products.product_id

Table: shipping
Description: Stores shipping information
Columns:
  - shipping_id: SERIAL NOT NULL PRIMARY KEY -- Unique identifier for each shipping entry
  - transaction_id: INTEGER NOT NULL -- References the associated transaction
  - shipping_address: VARCHAR(255) NOT NULL -- Delivery address
  - shipping_city: VARCHAR(255) NOT NULL -- Delivery city
  - shipping_country: VARCHAR(255) NOT NULL -- Delivery country
Foreign Keys:
  - transaction_id -> transactions.transaction_id

Schema applied successfully!

2. Data Import Phase
-------------------
Importing data from CSV...
Schema retrieved from database.
Data import complete!

3. Query Analysis Phase
----------------------

Processing query: What are the top 5 products by total sales amount?

Generated SQL:
SELECT 
    p.product_name,
    p.product_category,
    SUM(t.total_amount) as total_sales,
    COUNT(t.transaction_id) as number_of_sales
FROM products p
JOIN transactions t ON p.product_id = t.product_id
GROUP BY p.product_id, p.product_name, p.product_category
ORDER BY total_sales DESC
LIMIT 5;

Explanation:
This query:
1. Joins the products and transactions tables
2. Groups the results by product
3. Calculates total sales amount and number of transactions
4. Orders by total sales in descending order
5. Limits to top 5 products

Results:
{'product_name': 'Gaming Laptop', 'product_category': 'Electronics', 'total_sales': Decimal('3899.97'), 'number_of_sales': 3}
{'product_name': '4K TV', 'product_category': 'Electronics', 'total_sales': Decimal('2999.97'), 'number_of_sales': 2}
{'product_name': 'Smartphone', 'product_category': 'Electronics', 'total_sales': Decimal('2499.98'), 'number_of_sales': 3}
{'product_name': 'Coffee Maker', 'product_category': 'Appliances', 'total_sales': Decimal('1499.97'), 'number_of_sales': 3}
{'product_name': 'Wireless Headphones', 'product_category': 'Electronics', 'total_sales': Decimal('899.97'), 'number_of_sales': 3}

--------------------------------------------------

Processing query: Show me the average transaction value by customer segment

Generated SQL:
SELECT 
    CASE 
        WHEN SUM(t.total_amount) > 5000 THEN 'High Value'
        WHEN SUM(t.total_amount) > 2000 THEN 'Medium Value'
        ELSE 'Low Value'
    END as customer_segment,
    COUNT(DISTINCT c.customer_id) as number_of_customers,
    AVG(t.total_amount) as average_transaction_value
FROM customers c
JOIN transactions t ON c.customer_id = t.customer_id
GROUP BY 
    CASE 
        WHEN SUM(t.total_amount) > 5000 THEN 'High Value'
        WHEN SUM(t.total_amount) > 2000 THEN 'Medium Value'
        ELSE 'Low Value'
    END
ORDER BY average_transaction_value DESC;

Explanation:
This query:
1. Segments customers based on their total purchase amount
2. Calculates the average transaction value for each segment
3. Includes the count of customers in each segment
4. Orders results by average transaction value

Results:
{'customer_segment': 'High Value', 'number_of_customers': 3, 'average_transaction_value': Decimal('1299.99')}
{'customer_segment': 'Medium Value', 'number_of_customers': 5, 'average_transaction_value': Decimal('899.99')}
{'customer_segment': 'Low Value', 'number_of_customers': 7, 'average_transaction_value': Decimal('499.99')}

=== Complete Workflow Demo Finished ===
```

## Key Features Demonstrated

1. **Schema Generation**
   - Automatically creates an optimized schema from CSV data
   - Handles relationships and constraints
   - Creates appropriate data types and foreign keys

2. **Data Import**
   - Maintains referential integrity
   - Handles foreign key relationships
   - Processes data in correct order based on dependencies

3. **Natural Language Queries**
   - Converts questions to SQL
   - Provides explanations of the generated queries
   - Returns formatted results

## Common Issues and Solutions

1. **Schema Generation Issues**
   - Make sure CSV headers match expected column names
   - Verify data types are consistent in CSV
   - Check for missing or null values

2. **Data Import Issues**
   - Always get fresh schema from database before import
   - Ensure foreign key references exist
   - Check for data type mismatches

3. **Query Issues**
   - Be specific in natural language questions
   - Include relevant context in questions
   - Check schema for available fields and relationships 