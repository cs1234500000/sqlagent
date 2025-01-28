# SQL AI Agent

An intelligent multi-agent system for database operations, analytics, and visualization, powered by OpenAI GPT.

## Key Features

### Multi-Agent Architecture
- **Database Agent**: Schema management and evolution
- **ETL Agent**: Data import and transformation
- **Analytics Agent**: Business intelligence and visualization
- **Orchestrator Agent**: Pipeline coordination

### Core Capabilities
- Natural language to SQL conversion
- Automated schema generation and management
- Intelligent data import with referential integrity
- Interactive business analytics dashboards
- Query validation and execution
- Async support

## Prerequisites

- Python 3.8+
- PostgreSQL 12+
- OpenAI API key
- pip (Python package manager)

## Setup

1. Install PostgreSQL:
   ```bash
   # Ubuntu/Debian
   sudo apt-get update
   sudo apt-get install postgresql postgresql-contrib

   # macOS using Homebrew
   brew install postgresql@14
   ```

2. Create a database and user:
   ```bash
   # Connect to PostgreSQL
   psql postgres

   # In psql console:
   CREATE DATABASE your_database_name;
   CREATE USER your_username WITH PASSWORD 'your_password';
   GRANT ALL PRIVILEGES ON DATABASE your_database_name TO your_username;
   ```

3. Clone and install:
   ```bash
   git clone https://github.com/yourusername/sqlagent
   cd sqlagent
   python -m venv venv
   source venv/bin/activate  # or .\venv\Scripts\activate on Windows
   pip install -e .
   ```

4. Configure environment:
   ```bash
   # Create .env file
   echo "OPENAI_API_KEY=your_openai_api_key" >> .env
   echo "DB_CONNECTION_STRING=postgresql://your_username:your_password@localhost:5432/your_database_name" >> .env
   ```

## Usage Examples

### 1. Basic Schema and Data Import
```python
from src.core.agent import SQLAgent
from src.utils.config import Config

async def main():
    config = Config()
    agent = SQLAgent(config)
    
    # Get schema
    schema = await agent.get_schema()
    
    # Import data
    await agent.import_csv_data(schema, "data/sales_data.csv")
```

### 2. Interactive Analytics Dashboard
```python
# Generate sales analytics dashboard
await agent.generate_dashboard(results, query)
```

### 3. Natural Language Queries
```python
request = QueryRequest(
    question="What are the top 5 products by total sales?",
    include_explanation=True
)
result = await agent.process_request(request)
```

## Example Dashboards

The system provides several pre-built analytics views:
1. Sales Trends Analysis
2. Product Performance Metrics
3. Geographic Distribution
4. Payment and Order Status Analysis

Access the interactive dashboard at `http://localhost:8050` after running the dashboard demo.

## Project Structure

```
sqlagent/
├── src/
│   ├── agents/           # Specialized AI agents
│   ├── core/             # Core functionality
│   ├── database/         # Database operations
│   ├── visualization/    # Dashboard generation
│   └── utils/            # Utilities
├── examples/             # Usage examples
└── tests/               # Test suite
```

## Running Examples

```bash
# Basic usage
python examples/basic_usage.py

# Dashboard demo
python examples/dashboard_demo.py

# Complete workflow
python examples/complete_workflow.py
```

## Contributing

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## Troubleshooting

### Common Issues

1. Dashboard not showing:
   - Ensure you're accessing http://localhost:8050
   - Check if the port is available
   - Verify data was imported successfully

2. Data import errors:
   - Verify CSV format matches schema
   - Check database permissions
   - Ensure referential integrity

3. Environment issues:
   - Verify .env file exists and is properly formatted
   - Check OpenAI API key is valid
   - Confirm database connection string is correct

## License

MIT License - see LICENSE file for details