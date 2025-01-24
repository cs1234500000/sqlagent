from setuptools import setup, find_packages

setup(
    name="sqlagent",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        "openai>=1.0.0",
        "sqlalchemy>=2.0.0",
        "psycopg2-binary>=2.9.0",
        "python-dotenv>=1.0.0",
        "plotly>=5.18.0",
        "dash>=2.14.2",
        "pandas>=2.1.4",
        "numpy>=1.24.0"
    ]
) 