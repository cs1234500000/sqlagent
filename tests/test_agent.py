import pytest
from sqlagent.core.agent import SQLAgent
from sqlagent.utils.config import Config
from sqlagent.models.query import QueryRequest

@pytest.fixture
def agent():
    config = Config()
    return SQLAgent(config)

@pytest.mark.asyncio
async def test_query_generation(agent):
    request = QueryRequest(
        question="Show me all customers who made purchases over $1000 last month"
    )
    result = await agent.process_request(request)
    assert result.query is not None
    assert result.results is not None

@pytest.mark.asyncio
async def test_query_validation(agent):
    # Test valid queries
    valid_query = """
        SELECT c.id, c.name, c.email
        FROM customers c
        WHERE EXISTS (
            SELECT 1 FROM orders o
            WHERE o.customer_id = c.id
            AND EXTRACT(MONTH FROM o.order_date) = EXTRACT(MONTH FROM CURRENT_DATE - INTERVAL '1 month')
        )
    """
    is_valid, _ = agent.validator.validate(valid_query)
    assert is_valid

    # Test invalid queries
    invalid_queries = [
        "DROP TABLE customers;",
        "SELECT * FROM users; DROP TABLE users;",
        "SELECT * FROM users -- drop table",
        "SELECT * FROM users WHERE date > '2023-01-01' - 1"
    ]
    for query in invalid_queries:
        is_valid, _ = agent.validator.validate(query)
        assert not is_valid 