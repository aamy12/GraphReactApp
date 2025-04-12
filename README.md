# Knowledge Graph Application

A web application for creating, querying, and visualizing knowledge graphs with natural language processing capabilities.

## Features

- User authentication system
- File upload and parsing
- Knowledge graph extraction from text
- Graph database storage using Neo4j
- Natural language query processing
- Interactive graph visualization
- User history management
- LLM integration for reasoning and response generation

## Technology Stack

### Frontend
- React.js
- D3.js for graph visualization
- Tailwind CSS for styling
- React Router for navigation
- Axios for API requests

### Backend
- Flask for API endpoints
- Neo4j for graph database storage
- OpenAI API for natural language processing
- JWT for authentication
- SQLite for user management

## Setup Instructions

### Prerequisites
- Node.js and npm
- Python 3.8+ and pip
- Neo4j database (local or cloud instance)
- OpenAI API key

### Environment Setup

1. Clone the repository
2. Copy `.env.example` to `.env` and fill in your configuration details
3. Install backend dependencies:
   ```
   pip install -r requirements.txt
   ```
4. Install frontend dependencies:
   ```
   npm install
   ```

### Running the Application

1. Start the backend server:
   ```
   python server/app.py
   ```
2. Start the frontend development server:
   ```
   npm run dev
   ```
3. Access the application at http://localhost:5000

### Setting Up Neo4j

1. Install Neo4j or use Neo4j AuraDB (cloud version)
2. Create a new database
3. Update the `.env` file with your Neo4j connection details

## Usage Guide

### Authentication
1. Register a new account or log in with existing credentials
2. All operations require authentication

### Adding Knowledge
1. Upload text files to extract knowledge
2. The system will automatically parse the content and build the knowledge graph

### Querying
1. Enter natural language queries on the dashboard
2. View graphical representation of relevant knowledge subgraphs
3. Get AI-generated responses with reasoning

### Visualization
1. Explore your knowledge graph visually
2. Zoom, pan, and interact with nodes and relationships
3. View properties and details of entities

### History
1. Access your query history
2. Review previous questions and answers
3. Revisit visualizations from past queries

## Development

### Project Structure
- `/client`: React frontend code
- `/server`: Flask backend code
- `/shared`: Shared TypeScript definitions

### Key Files
- `server/app.py`: Main Flask application
- `server/graph_db.py`: Neo4j database interface
- `server/llm_service.py`: LLM integration for NLP tasks
- `client/src/App.tsx`: Main React application
- `client/src/components/GraphVisualization.tsx`: D3.js visualization

## License
MIT
