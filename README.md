# Simple JSON Storage

A simple JSON file storage with REST API. Allows you to store and retrieve JSON data by path.

## Launch

```bash
docker-compose up -d
```

## API Endpoints

### PUT /store/{path} 
Stores JSON data at the specified path.

### GET /store/{path}
Retrieves JSON data from the specified path.

## Usage Examples

### Storing data:
```bash
# Store a simple JSON with UUID name
UUID=$(uuidgen | tr '[:upper:]' '[:lower:]')
curl -X PUT "http://localhost:8000/store/$UUID" \
  -H "Content-Type: application/json" \
  -d '{"key": "value"}'

# Store with UUID and save the path
UUID=$(uuidgen | tr '[:upper:]' '[:lower:]')
echo "Storing data at: $UUID"
curl -X PUT "http://localhost:8000/store/$UUID" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "John",
    "age": 30,
    "items": ["item1", "item2"],
    "details": {
      "city": "Moscow",
      "country": "Russia"
    }
  }'

# Store with UUID and prefix
UUID="users_$(uuidgen | tr '[:upper:]' '[:lower:]')"
curl -X PUT "http://localhost:8000/store/$UUID" \
  -H "Content-Type: application/json" \
  -d '{"key": "value"}'
```

### Retrieving data:
```bash
# Get data by UUID (replace UUID with actual value)
curl "http://localhost:8000/store/$UUID"

# Get formatted data
curl "http://localhost:8000/store/$UUID" | jq '.'

# Get nested data from complex JSON
curl "http://localhost:8000/store/$UUID" | jq '.details.city'

# Store and immediately retrieve data
UUID=$(uuidgen | tr '[:upper:]' '[:lower:]')
curl -X PUT "http://localhost:8000/store/$UUID" \
  -H "Content-Type: application/json" \
  -d '{"test": "data"}' && \
curl "http://localhost:8000/store/$UUID" | jq '.'
```

## Limitations
- Maximum total storage size: 50MB
- JSON data only
- File names can only contain letters, numbers, and ._- characters