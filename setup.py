from setuptools import setup, find_packages

setup(
    name="sqlagent",
    version="0.1.0",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    install_requires=[
        "openai>=1.0.0",
        "python-dotenv>=0.19.0",
        "sqlalchemy>=1.4.0",
        "psycopg2-binary>=2.9.0",
        "pydantic>=2.0.0",
        "pydantic-settings>=2.0.0",
    ],
    python_requires=">=3.8",
) 