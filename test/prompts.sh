#!/bin/bash

# Generate test prompts and schemas for AI Manager testing
# Usage: ./generate_test_files.sh [prompts_dir] [schemas_dir] [data_file]

# Default directories and files (can be overridden by command line arguments)
PROMPTS_DIR="${1:-./test_data/prompts}"
SCHEMAS_DIR="${2:-./test_data/schemas}"
DATA_FILE="${3:-./test_data/test_data.json}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}AI Manager Test File Generator${NC}"
echo -e "Prompts directory: ${YELLOW}${PROMPTS_DIR}${NC}"
echo -e "Schemas directory: ${YELLOW}${SCHEMAS_DIR}${NC}"
echo -e "Test data file: ${YELLOW}${DATA_FILE}${NC}"
echo ""

# Create directories
mkdir -p "$PROMPTS_DIR"
mkdir -p "$SCHEMAS_DIR"
mkdir -p "$(dirname "$DATA_FILE")"

# Generate comprehensive test data JSON
cat > "$DATA_FILE" << 'EOF'
{
  "simple_prompts": {
    "simple_greeting": {
      "content": "Say hello to {name}",
      "test_data": {"name": "Alice"},
      "expected_contains": ["hello", "Alice"]
    },
    "get_weather": {
      "content": "Get weather for {city}",
      "test_data": {"city": "Boston"},
      "expected_contains": ["weather", "Boston"]
    },
    "translate_text": {
      "content": "Translate the following text from {source_lang} to {target_lang}: {text}",
      "test_data": {"source_lang": "English", "target_lang": "Spanish", "text": "Hello world"},
      "expected_contains": ["translate", "English", "Spanish"]
    },
    "summarize_content": {
      "content": "Summarize the following content in {word_count} words: {content}",
      "test_data": {"word_count": 50, "content": "Long article content here..."},
      "expected_contains": ["summarize", "50"]
    },
    "code_review": {
      "content": "Review the following {language} code and provide suggestions for improvement:\n\n{code}",
      "test_data": {"language": "Python", "code": "def hello():\n    print('world')"},
      "expected_contains": ["review", "Python"]
    }
  },
  "structured_prompts": {
    "create_user": {
      "content": "Create a user with name {name} and email {email}",
      "schema": {
        "id": 12345,
        "name": "John Doe", 
        "email": "john@example.com",
        "active": true,
        "created_at": "2025-05-30T12:00:00Z"
      },
      "test_data": {"name": "Alice", "email": "alice@test.com"},
      "mock_response": "{\"id\": 123, \"name\": \"Alice\", \"email\": \"alice@test.com\", \"active\": true, \"created_at\": \"2025-05-30T12:00:00Z\"}",
      "expected_fields": ["id", "name", "email", "active"]
    },
    "create_task": {
      "content": "Create a task with title '{title}' and priority {priority}",
      "schema": {
        "id": "task_12345",
        "title": "Example Task",
        "priority": 3,
        "status": "pending",
        "created_at": "2025-05-30T12:00:00Z",
        "assignee": null,
        "tags": ["work", "urgent"]
      },
      "test_data": {"title": "Test Task", "priority": 1},
      "mock_response": "{\"id\": \"task_999\", \"title\": \"Test Task\", \"priority\": 1, \"status\": \"pending\", \"created_at\": \"2025-05-30T12:00:00Z\", \"assignee\": null, \"tags\": [\"test\"]}",
      "expected_fields": ["id", "title", "priority", "status"]
    },
    "analyze_product": {
      "content": "Analyze the product {product_name} in the {category} market",
      "schema": {
        "analysis": {
          "product_name": "Example Product",
          "category": "Technology", 
          "strengths": [
            "High quality build",
            "Competitive pricing"
          ],
          "weaknesses": [
            "Limited market presence",
            "Outdated design"
          ],
          "opportunities": [
            "Growing market demand",
            "Partnership potential"
          ],
          "threats": [
            "Strong competition",
            "Economic uncertainty"
          ],
          "score": 7.5,
          "recommendation": "Proceed with caution"
        }
      },
      "test_data": {"product_name": "Widget Pro", "category": "Technology"},
      "mock_response": "{\"analysis\": {\"product_name\": \"Widget Pro\", \"category\": \"Technology\", \"strengths\": [\"Innovative design\"], \"weaknesses\": [\"High cost\"], \"opportunities\": [\"Market growth\"], \"threats\": [\"Competition\"], \"score\": 8.0, \"recommendation\": \"Recommended\"}}",
      "expected_fields": ["analysis"]
    },
    "generate_report": {
      "content": "Generate a comprehensive {report_type} report covering {timeframe} with focus on {focus_areas}",
      "schema": {
        "report": {
          "title": "Monthly Sales Report",
          "type": "sales",
          "period": "2025-05",
          "summary": "Executive summary of findings",
          "sections": [
            {
              "title": "Overview",
              "content": "Section content here",
              "charts": ["revenue_chart", "growth_chart"]
            },
            {
              "title": "Key Metrics", 
              "content": "Metrics and analysis",
              "charts": ["performance_chart"]
            }
          ],
          "metrics": {
            "total_revenue": 125000,
            "growth_rate": 15.5,
            "customer_count": 450,
            "avg_order_value": 277.78
          },
          "recommendations": [
            "Increase marketing spend in Q2",
            "Focus on customer retention programs"
          ],
          "next_actions": [
            {
              "action": "Review pricing strategy",
              "owner": "Product Team",
              "due_date": "2025-06-15"
            }
          ]
        }
      },
      "test_data": {"report_type": "sales", "timeframe": "Q1 2025", "focus_areas": "revenue and growth"},
      "mock_response": "{\"report\": {\"title\": \"Q1 Sales Report\", \"type\": \"sales\", \"period\": \"Q1 2025\", \"summary\": \"Strong performance\", \"sections\": [], \"metrics\": {\"total_revenue\": 150000}, \"recommendations\": [\"Continue growth strategy\"], \"next_actions\": []}}",
      "expected_fields": ["report"]
    },
    "design_api": {
      "content": "Design a REST API for {service_name} that handles {functionality}",
      "schema": {
        "api_design": {
          "service_name": "User Management Service",
          "base_url": "https://api.example.com/v1",
          "endpoints": [
            {
              "method": "GET",
              "path": "/users",
              "description": "List all users",
              "parameters": [
                {
                  "name": "limit",
                  "type": "integer",
                  "required": false
                }
              ],
              "response_schema": {
                "type": "array",
                "items": {"$ref": "#/definitions/User"}
              }
            },
            {
              "method": "POST", 
              "path": "/users",
              "description": "Create new user",
              "request_schema": {"$ref": "#/definitions/CreateUser"},
              "response_schema": {"$ref": "#/definitions/User"}
            }
          ],
          "definitions": {
            "User": {
              "type": "object",
              "properties": {
                "id": {"type": "integer"},
                "name": {"type": "string"},
                "email": {"type": "string"}
              }
            }
          }
        }
      },
      "test_data": {"service_name": "Task Manager", "functionality": "CRUD operations"},
      "mock_response": "{\"api_design\": {\"service_name\": \"Task Manager\", \"base_url\": \"https://api.tasks.com/v1\", \"endpoints\": [], \"definitions\": {}}}",
      "expected_fields": ["api_design"]
    },
    "generate_test_data": {
      "content": "Generate {count} test records for {entity_type} with fields: {fields}",
      "schema": {
        "test_data": [
          {
            "id": 1,
            "name": "John Doe",
            "email": "john.doe@example.com",
            "age": 30,
            "department": "Engineering",
            "active": true
          },
          {
            "id": 2, 
            "name": "Jane Smith",
            "email": "jane.smith@example.com",
            "age": 28,
            "department": "Marketing",
            "active": true
          }
        ],
        "metadata": {
          "count": 2,
          "generated_at": "2025-05-30T12:00:00Z",
          "schema_version": "1.0"
        }
      },
      "test_data": {"count": 5, "entity_type": "users", "fields": "name, email, age"},
      "mock_response": "{\"test_data\": [{\"id\": 1, \"name\": \"Test User\", \"email\": \"test@example.com\", \"age\": 25, \"active\": true}], \"metadata\": {\"count\": 1}}",
      "expected_fields": ["test_data", "metadata"]
    }
  },
  "system_user_prompts": {
    "analyze_data": {
      "system": "You are a data analyst assistant specializing in business intelligence and statistical analysis.",
      "user": "Analyze the following data and provide insights: {data}",
      "schema_yaml": "analysis:\n  summary: \"Data shows positive trend\"\n  metrics:\n    - name: \"average\"\n      value: 42.5\n    - name: \"count\" \n      value: 100\n    - name: \"growth_rate\"\n      value: 15.2\n  insights:\n    - \"Key finding 1\"\n    - \"Key finding 2\"\n    - \"Important trend identified\"\n  recommendations:\n    - \"Action item 1\"\n    - \"Action item 2\"",
      "test_data": {"data": "Q1 sales figures"},
      "mock_response": "analysis:\n  summary: \"Q1 performance exceeded expectations\"\n  metrics:\n    - name: \"revenue\"\n      value: 185000\n    - name: \"customers\"\n      value: 520\n  insights:\n    - \"Strong customer acquisition\"\n    - \"Premium sales increased\"\n  recommendations:\n    - \"Expand premium line\"",
      "expected_fields": ["analysis"]
    },
    "complex_task": {
      "system": "You are a helpful assistant specialized in complex task management and project planning.",
      "user": "Complete the following complex task: {task}. Provide detailed steps and considerations.",
      "test_data": {"task": "Launch new product"},
      "expected_contains": ["steps", "task", "launch"]
    },
    "creative_writing": {
      "system": "You are a creative writing assistant that helps users craft engaging stories and content.",
      "user": "Write a {genre} story about {topic} with approximately {word_count} words.",
      "test_data": {"genre": "mystery", "topic": "lost treasure", "word_count": 500},
      "expected_contains": ["mystery", "treasure"]
    },
    "tech_docs": {
      "system": "You are a technical documentation specialist who creates clear, comprehensive documentation.",
      "user": "Create documentation for {component_type} called {component_name} with the following specifications: {specs}",
      "test_data": {"component_type": "API", "component_name": "UserService", "specs": "CRUD operations for users"},
      "expected_contains": ["documentation", "UserService", "CRUD"]
    },
    "meeting_notes": {
      "system": "You are an assistant that creates structured meeting notes and action items.",
      "user": "Create meeting notes for {meeting_type} on {date} with participants: {participants}",
      "schema_yaml": "meeting:\n  title: \"Weekly Team Standup\"\n  date: \"2025-05-30\"\n  duration_minutes: 30\n  participants:\n    - name: \"John Doe\"\n      role: \"Lead Developer\"\n    - name: \"Jane Smith\" \n      role: \"Product Manager\"\n  agenda_items:\n    - topic: \"Sprint Review\"\n      duration_minutes: 10\n      notes: \"Completed 8 out of 10 story points\"\n    - topic: \"Blockers Discussion\"\n      duration_minutes: 15\n      notes: \"API integration issues identified\"\n  action_items:\n    - task: \"Fix API integration\"\n      assignee: \"John Doe\"\n      due_date: \"2025-06-01\"\n    - task: \"Update documentation\"\n      assignee: \"Jane Smith\"\n      due_date: \"2025-06-03\"\n  next_meeting: \"2025-06-06T10:00:00Z\"",
      "test_data": {"meeting_type": "standup", "date": "2025-05-30", "participants": "John, Jane, Bob"},
      "mock_response": "meeting:\n  title: \"Daily Standup\"\n  date: \"2025-05-30\"\n  participants:\n    - name: \"John\"\n    - name: \"Jane\"\n  action_items:\n    - task: \"Review code\"\n      assignee: \"John\"",
      "expected_fields": ["meeting"]
    }
  },
  "test_scenarios": {
    "validation_success": {
      "prompt": "create_user",
      "data": {"name": "Test User", "email": "test@example.com"},
      "expected_result": "valid_json"
    },
    "validation_failure": {
      "prompt": "create_user", 
      "data": {"name": "Test User", "email": "test@example.com"},
      "mock_invalid_response": "This is not valid JSON or YAML",
      "expected_result": "error_with_retries"
    },
    "yaml_validation": {
      "prompt": "analyze_data",
      "data": {"data": "test metrics"},
      "expected_result": "valid_yaml"
    },
    "missing_schema": {
      "prompt": "simple_greeting",
      "data": {"name": "Test"},
      "validate": true,
      "expected_result": "no_schema_error"
    },
    "missing_prompt": {
      "prompt": "nonexistent_prompt",
      "data": {},
      "expected_result": "prompt_not_found"
    },
    "missing_data_keys": {
      "prompt": "simple_greeting",
      "data": {},
      "expected_result": "missing_keys_error"
    }
  }
}
EOF

echo -e "${GREEN}✓ Test data JSON created: ${DATA_FILE}${NC}"

# Function to create files from JSON data
create_files_from_json() {
    python3 << EOF
import json
import os

# Load test data
with open('$DATA_FILE', 'r') as f:
    data = json.load(f)

prompts_dir = '$PROMPTS_DIR'
schemas_dir = '$SCHEMAS_DIR'

file_count = 0

# Create simple prompts
for name, info in data['simple_prompts'].items():
    with open(f'{prompts_dir}/{name}.txt', 'w') as f:
        f.write(info['content'])
    file_count += 1
    print(f"Created: {name}.txt")

# Create structured prompts and their schemas
for name, info in data['structured_prompts'].items():
    # Create prompt file
    with open(f'{prompts_dir}/{name}.txt', 'w') as f:
        f.write(info['content'])
    file_count += 1
    
    # Create schema file
    with open(f'{schemas_dir}/{name}.schema.txt', 'w') as f:
        f.write(json.dumps(info['schema'], indent=2))
    file_count += 1
    print(f"Created: {name}.txt + {name}.schema.txt")

# Create system/user prompt pairs
for name, info in data['system_user_prompts'].items():
    # Create system file
    with open(f'{prompts_dir}/{name}.system.txt', 'w') as f:
        f.write(info['system'])
    file_count += 1
    
    # Create user file  
    with open(f'{prompts_dir}/{name}.user.txt', 'w') as f:
        f.write(info['user'])
    file_count += 1
    
    # Create schema file if it exists
    if 'schema_yaml' in info:
        with open(f'{schemas_dir}/{name}.schema.txt', 'w') as f:
            f.write(info['schema_yaml'])
        file_count += 1
        print(f"Created: {name}.system.txt + {name}.user.txt + {name}.schema.txt")
    else:
        print(f"Created: {name}.system.txt + {name}.user.txt")

print(f"\nTotal files created: {file_count}")
EOF
}

echo ""
echo -e "${BLUE}Creating prompt and schema files from JSON data...${NC}"
create_files_from_json

echo ""
echo -e "${GREEN}✓ File generation complete!${NC}"
echo ""
echo -e "${BLUE}Summary:${NC}"
echo -e "Test data file: ${YELLOW}${DATA_FILE}${NC}"
echo -e "Total prompts created: ${YELLOW}$(find "$PROMPTS_DIR" -name "*.txt" | wc -l)${NC}"
echo -e "Total schemas created: ${YELLOW}$(find "$SCHEMAS_DIR" -name "*.schema.txt" | wc -l)${NC}"
echo ""
echo -e "${BLUE}File structure:${NC}"
echo -e "${YELLOW}Prompts:${NC}"
find "$PROMPTS_DIR" -name "*.txt" | sort | sed 's/^/  /'
echo ""
echo -e "${YELLOW}Schemas:${NC}"
find "$SCHEMAS_DIR" -name "*.schema.txt" | sort | sed 's/^/  /'
echo ""
echo -e "${GREEN}Test files and data are ready for use!${NC}"