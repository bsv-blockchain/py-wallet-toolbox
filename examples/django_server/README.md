# Django JSON-RPC Server for py-wallet-toolbox

This Django project provides a JSON-RPC HTTP server for BRC-100 wallet operations using py-wallet-toolbox.

## Features

- **JSON-RPC 2.0 API**: Standard JSON-RPC protocol for wallet operations
- **StorageProvider Integration**: Auto-registered StorageProvider methods (28 methods)
- **TypeScript Compatibility**: Compatible with ts-wallet-toolbox StorageClient
- **Django Integration**: Full Django middleware and configuration support

## Quick Start

### 1. Install Dependencies

```bash
# Install core dependencies
pip install -r requirements.txt

# Optional: Install development dependencies
pip install -r requirements-dev.txt

# Optional: Install database backends
pip install -r requirements-db.txt
```

### 2. Run Migrations

```bash
python manage.py migrate
```

### 3. Start Development Server

```bash
python manage.py runserver
```

The server will start at `http://127.0.0.1:8000/`

## API Endpoints

### JSON-RPC Endpoint
- **URL**: `POST /` (TypeScript StorageServer parity)
- **Content-Type**: `application/json`
- **Protocol**: JSON-RPC 2.0
- **Admin**: `GET /admin/` (Django admin interface)

### Available Methods

The server exposes all StorageProvider methods as JSON-RPC endpoints:

- `createAction`, `internalizeAction`, `findCertificatesAuth`
- `setActive`, `getSyncChunk`, `processSyncChunk`
- And 22 other StorageProvider methods

## Usage Examples

### Create Action

```bash
curl -X POST http://127.0.0.1:8000/ \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "createAction",
    "params": {
      "auth": {"identityKey": "your-identity-key"},
      "args": {
        "description": "Test transaction",
        "outputs": [
          {
            "satoshis": 1000,
            "lockingScript": "76a914000000000000000000000000000000000000000088ac"
          }
        ],
        "options": {
          "returnTXIDOnly": false
        }
      }
    },
    "id": 1
  }'
```

### Available Methods

The server exposes all StorageProvider methods as JSON-RPC endpoints:

- `createAction`, `internalizeAction`, `findCertificatesAuth`
- `setActive`, `getSyncChunk`, `processSyncChunk`
- And 22 other StorageProvider methods

Note: BRC-100 Wallet methods like `getVersion` are not available via JSON-RPC.
They are implemented in the Wallet class but not exposed through the StorageProvider interface.

## Configuration

### Settings

The Django settings are configured in `wallet_server/settings.py`:

- **DEBUG**: Development mode enabled
- **ALLOWED_HOSTS**: Localhost access allowed
- **INSTALLED_APPS**: `wallet_app` and `rest_framework` included
- **REST_FRAMEWORK**: JSON-only configuration

### CORS Support

For cross-origin requests, install `django-cors-headers`:

```bash
pip install django-cors-headers
```

Then uncomment CORS settings in `settings.py`.

## Development

### Running Tests

```bash
# Install test dependencies
pip install -r requirements-dev.txt

# Run Django tests
python manage.py test

# Run with pytest
pytest
```

### Code Quality

```bash
# Format code
black .

# Lint code
ruff check .

# Type check
mypy .
```

## Architecture

```
wallet_server/
├── wallet_app/
│   ├── views.py      # JSON-RPC endpoint
│   ├── services.py   # JsonRpcServer integration
│   └── urls.py       # URL configuration
├── settings.py       # Django configuration
└── urls.py          # Main URL routing
```

## TypeScript Compatibility

This server is designed to be compatible with `ts-wallet-toolbox` StorageClient:

- Same JSON-RPC method names (camelCase)
- Compatible request/response formats
- TypeScript StorageServer.ts equivalent functionality

## License

Same as py-wallet-toolbox project.
