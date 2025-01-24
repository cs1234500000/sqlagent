import asyncio
from src.core.agent import SQLAgent
from src.utils.config import Config
from src.models.schema import DatabaseSchema

async def setup_sales_database(agent):
    """Set up sales database with required tables."""
    try:
        # Create tables
        await agent.execute_query("""
            DROP TABLE IF EXISTS transactions CASCADE;
            DROP TABLE IF EXISTS customers CASCADE;
            
            CREATE TABLE customers (
                customer_id SERIAL PRIMARY KEY,
                customer_name VARCHAR(255) NOT NULL,
                customer_email VARCHAR(255) NOT NULL,
                shipping_address VARCHAR(255) NOT NULL,
                shipping_city VARCHAR(100) NOT NULL,
                shipping_country VARCHAR(50) NOT NULL
            );
            
            CREATE TABLE transactions (
                transaction_id SERIAL PRIMARY KEY,
                customer_id INTEGER NOT NULL,
                date DATE NOT NULL,
                product_name VARCHAR(255) NOT NULL,
                product_category VARCHAR(100) NOT NULL,
                quantity INTEGER NOT NULL,
                unit_price DECIMAL(10,2) NOT NULL,
                total_amount DECIMAL(10,2) NOT NULL,
                payment_method VARCHAR(50) NOT NULL,
                order_status VARCHAR(50) NOT NULL,
                FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
            );
        """)
        print("Database setup completed successfully")
        
    except Exception as e:
        print(f"Error setting up database: {str(e)}")
        raise

async def main():
    """Demo the dashboard functionality with sales analytics."""
    try:
        config = Config()
        agent = SQLAgent(config)
        
        # First set up the database
        print("\nSetting up database...")
        schema = await agent.get_schema_from_database()
        
        # Import sample data
        print("\nImporting sales data...")
        await agent.import_csv_data(schema, "data/sales_data.csv")
        print("Data import complete!")
        
        # Get query from user or show different analytics views
        print("\nSelect an analysis (press Enter to cycle through all):")
        print("1. Sales Trends")
        print("2. Product Performance")
        print("3. Geographic Analysis")
        print("4. Payment & Order Status")
        print("5. Custom Query")
        
        choice = input("\nEnter choice (1-5): ").strip()
        
        analytics_queries = {
            "1": {
                "name": "Sales Trends",
                "query": """
                    SELECT 
                        DATE_TRUNC('day', date) as sale_date,
                        product_category,
                        COUNT(*) as num_transactions,
                        SUM(total_amount) as daily_revenue,
                        AVG(total_amount) as avg_transaction_value
                    FROM transactions
                    GROUP BY DATE_TRUNC('day', date), product_category
                    ORDER BY sale_date;
                """
            },
            "2": {
                "name": "Product Performance",
                "query": """
                    SELECT 
                        product_category,
                        product_name,
                        COUNT(*) as times_sold,
                        SUM(quantity) as units_sold,
                        SUM(total_amount) as total_revenue,
                        AVG(unit_price) as avg_unit_price
                    FROM transactions
                    GROUP BY product_category, product_name
                    ORDER BY total_revenue DESC;
                """
            },
            "3": {
                "name": "Customer Geographic Analysis",
                "query": """
                    SELECT 
                        c.shipping_city,
                        c.shipping_country,
                        COUNT(DISTINCT c.customer_id) as num_customers,
                        COUNT(*) as num_transactions,
                        SUM(t.total_amount) as total_revenue,
                        AVG(t.total_amount) as avg_transaction_value
                    FROM customers c
                    JOIN transactions t ON c.customer_id = t.customer_id
                    GROUP BY c.shipping_city, c.shipping_country
                    ORDER BY total_revenue DESC;
                """
            },
            "4": {
                "name": "Payment & Order Status",
                "query": """
                    SELECT 
                        payment_method,
                        order_status,
                        COUNT(*) as num_transactions,
                        SUM(total_amount) as total_revenue,
                        AVG(total_amount) as avg_transaction_value,
                        COUNT(DISTINCT customer_id) as unique_customers
                    FROM transactions
                    GROUP BY payment_method, order_status
                    ORDER BY num_transactions DESC;
                """
            }
        }
        
        if choice == "5":
            # Custom query input
            query = input("\nEnter your SQL query: ").strip()
            analysis_name = "Custom Analysis"
        elif choice in analytics_queries:
            # Use selected pre-defined analysis
            analysis = analytics_queries[choice]
            query = analysis["query"]
            analysis_name = analysis["name"]
        else:
            # Show all analyses
            for analysis in analytics_queries.values():
                print(f"\n=== Generating {analysis['name']} Dashboard ===")
                results = await agent.execute_query(analysis["query"])
                
                if results:
                    print(f"Analysis returned {len(results)} rows")
                    print("\nGenerating interactive dashboard...")
                    await agent.generate_dashboard(results, analysis["query"])
                    input("\nPress Enter to continue to next analysis...")
                else:
                    print("No results returned from analysis")
            return
        
        # Execute single analysis
        print(f"\n=== Generating {analysis_name} Dashboard ===")
        print("\nExecuting query...")
        results = await agent.execute_query(query)
        
        if not results:
            print("No results returned from query")
            return
            
        print(f"\nQuery returned {len(results)} rows")
        print("Sample result:", results[0] if results else "No results")
        
        # Generate and display dashboard
        print("\nGenerating dashboard...")
        await agent.generate_dashboard(results, query)
        
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main()) 