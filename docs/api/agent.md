# SQL Agent API Reference

## SQLAgent

The main class that handles natural language to SQL conversion.

### Constructor

```python
def __init__(self, config: Config, db_schema: Optional[str] = None)
```

Parameters:
- `config`: Configuration object containing API keys and settings
- `db_schema`: Optional database schema string

### Methods

#### process_request

```python
async def process_request(self, request: QueryRequest) -> QueryResult
```

Process a natural language query request.

Parameters:
- `request`: QueryRequest object containing the question and options

Returns:
- `QueryResult`: Object containing the query, results, and metadata

#### generate_query

```python
async def generate_query(self, request: QueryRequest) -> QueryResult
```

Generate SQL query from natural language using OpenAI.

Parameters:
- `request`: QueryRequest object
Returns:
- `QueryResult`: Generated query and metadata

## Examples

```python
from src.core.agent import SQLAgent
from src.utils.config import Config
from src.models.query import QueryRequest

# Initialize agent
config = Config()
agent = SQLAgent(config, db_schema="your_schema")

# Create request
request = QueryRequest(
    question="Show me all customers who made purchases over $1000 last month"
)

# Process request
result = await agent.process_request(request)
print(result.query)
``` 