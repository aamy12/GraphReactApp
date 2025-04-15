# Knowledge Graph Application

A web application for creating, querying, and visualizing knowledge graphs with natural language processing capabilities.

## Local Development Setup

### Prerequisites
- Node.js (v20+)
- Python (v3.11+)
- NPM or Yarn
- Neo4j database instance
- OpenAI API key

### Installation

1. Clone the repository
2. Install Node.js dependencies:
```bash
npm install
```

3. Install Python dependencies:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file in the root directory:
```env
# Flask configuration
SECRET_KEY=your-secret-key
FLASK_ENV=development

# JWT configuration
JWT_SECRET_KEY=your-jwt-secret-key

# Neo4j configuration
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password

# OpenAI configuration
OPENAI_API_KEY=your-openai-api-key

# File upload configuration
UPLOAD_FOLDER=./uploads
```

### Running the Application

1. Start the backend server:
```bash
python run.py
```

2. In a separate terminal, start the frontend development server:
```bash
npm run dev
```

3. Access the application at http://localhost:5000

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


## Setting Up Neo4j

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