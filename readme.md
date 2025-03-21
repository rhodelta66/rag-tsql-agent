# RAG T-SQL Agent

A Retrieval-Augmented Generation (RAG) agent that helps create T-SQL code based on existing stored procedures in TSQL.APP Framework database. This agent is specifically designed to work with UI-related stored procedures that use `sp_api_*` procedures for creating interactive user interfaces directly from T-SQL.

![](https://250.tracy.nu/239/storage/xwicmhl59xgikt59parqtogersokc1eh)

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

```
git clone https://github.com/rhodelta66/rag-tsql-agent.git
cd rag-tsql-agent
```

2. Install the required dependencies:
```
pip install -r requirements.txt
```

3. Set up the agent with your SQL Server information:
```
python main.py setup --server "your-server\SQLEXPRESS" --database "your-database" --api-key "your-openai-api-key"
```

## Usage

### Indexing Your Stored Procedures

Before you can generate new code, you need to index your existing stored procedures:

```
python main.py index
```

By default, this will only index UI-related stored procedures (those that use `sp_api_*` procedures) . If you want to index all stored procedures, use:

```
python main.py index --all
```

### Generating New T-SQL Code

To generate a new UI-related stored procedure based on a description:
```
python main.py generate "Create a form with name and email fields, and a submit button that displays a confirmation message" --output new_procedure.sql
```
The `--similar` parameter controls how many similar procedures to use as reference (default is 3):
```
python main.py generate "Create a login form with username and password" --similar 5 --output login_procedure.sql
```

### Modifying Existing Procedures

To modify an existing procedure based on a natural language request:
```
python main.py modify "dbo.YourProcedure" "Add a cancel button that clears the form" --output modified_procedure.sql
```
## Testing and Validation

To test the RAG T-SQL agent:

1. First, ensure you have some UI-related stored procedures in your database that use `sp_api_*` procedures.

2. Set up the agent with your SQL Server information:
```
python main.py setup --server "your-server\SQLEXPRESS" --database "your-database" --api-key "your-openai-api-key"
```

3. Index your stored procedures:
python main.py index

4. Verify the indexing was successful by checking the `data/index` directory for the index files.

5. Test generating a simple UI procedure:
```
python main.py generate "Create a simple form with a text field and a submit button" --output test_procedure.sql
```

6. Examine the generated code in `test_procedure.sql` to ensure it:
- Contains proper variable declarations
- Uses `sp_api_modal_*` procedures for UI components
- Implements appropriate control flow for button clicks
- Follows T-SQL best practices

7. If you have an existing procedure, test the modification functionality:
```
python main.py modify "dbo.ExistingProcedure" "Add a cancel button" --output modified_procedure.sql
```

8. Compare the original and modified procedures to ensure the changes are appropriate.

## Troubleshooting

### Database Connection Issues

- Ensure SQL Server Express is running
- Verify Windows authentication is enabled
- Check that the server name and database name are correct
- Make sure you have appropriate permissions to access the database

### Embedding Generation Issues

- Ensure you have sufficient disk space for the embedding models
- The first run may take longer as it downloads the sentence-transformers model

### Code Generation Issues

- Verify your OpenAI API key is valid and has sufficient credits
- Check your internet connection
- Ensure you have indexed some procedures before attempting to generate code

## License

This project is licensed under the MIT License - see the LICENSE file for details.
