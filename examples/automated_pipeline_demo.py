import asyncio
from src.agents.orchestrator_agent import OrchestratorAgent
from src.config import Config

async def main():
    """Demo the automated data pipeline."""
    config = Config()
    orchestrator = OrchestratorAgent(config)
    
    # Define requirements
    requirements = """
    Create a sales analytics pipeline that:
    1. Imports daily sales data from CSV files
    2. Tracks customer purchases and behavior
    3. Generates daily sales reports
    4. Visualizes key metrics like revenue, products, and customer segments
    
    Data source: data/sales_data.csv
    """
    
    # Set up complete pipeline
    pipeline = await orchestrator.setup_data_pipeline(requirements)
    
    # Monitor and optimize
    status = await orchestrator.monitor_pipeline()
    if status.needs_optimization:
        optimization = await orchestrator.optimize_pipeline(status.metrics)
        await optimization.apply()

if __name__ == "__main__":
    asyncio.run(main()) 