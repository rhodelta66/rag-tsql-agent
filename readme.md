# RAG T-SQL Agent

A Retrieval-Augmented Generation (RAG) agent that helps create T-SQL code based on existing stored procedures in TSQL.APP Framework database. This agent is specifically designed to work with UI-related stored procedures that use `sp_api_*` procedures for creating interactive user interfaces directly from T-SQL.

## Features

- Connects to SQL Server Express with Windows authentication
- Analyzes existing UI-related stored procedures
- Creates embeddings of procedures for semantic search
- Retrieves relevant procedures based on natural language queries
- Generates new T-SQL code based on similar existing procedures
- Modifies existing procedures based on natural language requests

## Requirements

- Python 3.8 or newer
- SQL Server Express with Windows authentication
- OpenAI API key for code generation

## Installation

1. Clone this repository:
