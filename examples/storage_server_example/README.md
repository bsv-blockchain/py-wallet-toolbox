# Django JSON-RPC Server for py-wallet-toolbox

This Django project provides a JSON-RPC HTTP server for BRC-100 wallet operations using py-wallet-toolbox.

## Features

- **JSON-RPC 2.0 API**: Standard JSON-RPC protocol for wallet operations
- **StorageProvider Integration**: Auto-registered StorageProvider methods (28 methods)
- **TypeScript Compatibility**: Compatible with ts-wallet-toolbox StorageClient
- **Django Integration**: Full Django middleware and configuration support
- **BRC-104 Authentication**: Optional authentication via py-middleware package

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

Note: BRC-100 Wallet methods like `getVersion` are not available via JSON-RPC.
They are implemented in the Wallet class but not exposed through the StorageProvider interface.

## BRC-104 Authentication (py-middleware)

This server supports BRC-104 authentication using the `py-middleware` package, which is equivalent to:
- `go-bsv-middleware` (Go)
- `@bsv/auth-express-middleware` (TypeScript)

### Enabling Authentication

1. **Edit `wallet_server/settings.py`**:

```python
MIDDLEWARE = [
    # ... other middleware ...
    
    # Enable BSV Authentication
    'adapter.auth_middleware.BSVAuthMiddleware',
    
    # Optional: Enable Payment (monetization)
    # 'adapter.payment_middleware_complete.BSVPaymentMiddleware',
]

# Configure BSV Middleware
BSV_MIDDLEWARE = {
    # Required: Wallet instance for authentication
    'WALLET': your_wallet_instance,
    
    # Allow unauthenticated requests (development only)
    'ALLOW_UNAUTHENTICATED': False,
    
    # Optional: Certificate requirements
    'CERTIFICATE_REQUESTS': None,
    
    # Logging level
    'LOG_LEVEL': 'info',
}
```

2. **Create a wallet instance** (in services.py or settings.py):

```python
from bsv_wallet_toolbox import Wallet
from bsv.keys import PrivateKey

# For development/testing
private_key = PrivateKey()
wallet = Wallet(
    chain='test',
    key_deriver=KeyDeriver(private_key),
)
```

### Authentication Flow

When authentication is enabled:

1. Client sends request with BRC-104 auth headers (`x-bsv-auth-*`)
2. `BSVAuthMiddleware` validates the authentication
3. Authenticated identity is stored in `request.auth.identity_key`
4. Views verify that `params.auth.identityKey` matches authenticated identity
5. This prevents clients from accessing other clients' data

### Payment (Monetization)

To enable payment for API access:

```python
# In settings.py
def calculate_price(request):
    """Calculate price in satoshis based on request."""
    import json
    try:
        body = json.loads(request.body)
        method = body.get('method', '')
        if method == 'createAction':
            return 100  # 100 satoshis
        elif method == 'processAction':
            return 50   # 50 satoshis
    except:
        pass
    return 0  # Free

# Add to MIDDLEWARE
MIDDLEWARE = [
    # ... auth middleware first ...
    'adapter.payment_middleware_complete.BSVPaymentMiddleware',
]
```

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

Then add to settings:

```python
INSTALLED_APPS = [
    ...
    'corsheaders',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    ...
]

CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
]
```

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
│   ├── views.py      # JSON-RPC endpoint with identity verification
│   ├── services.py   # StorageServer integration
│   └── urls.py       # URL configuration
├── settings.py       # Django + BSV middleware configuration
└── urls.py          # Main URL routing

# py-middleware package (external)
py-middleware/
├── bsv_middleware/           # Core library
│   ├── types.py              # Type definitions
│   ├── exceptions.py         # Exception classes
│   └── py_sdk_bridge.py      # py-sdk integration
└── examples/django_example/
    └── adapter/              # Django-specific adapters
        ├── auth_middleware.py
        ├── payment_middleware_complete.py
        ├── transport.py
        └── session_manager.py
```

## Comparison with Other Implementations

| Feature | TypeScript (wallet-infra) | Go (go-wallet-toolbox) | Python Django |
|---------|--------------------------|------------------------|---------------|
| JSON-RPC 2.0 | ✅ | ✅ | ✅ |
| BRC-104 Auth | ✅ `@bsv/auth-express-middleware` | ✅ `go-bsv-middleware` | ✅ `py-middleware` |
| Payment (402) | ✅ `@bsv/payment-express-middleware` | ✅ `middleware.NewPayment()` | ✅ `py-middleware` |
| CORS | ✅ | ✅ | ✅ (django-cors-headers) |
| Identity Verification | ✅ | ✅ | ✅ |

## TypeScript Compatibility

This server is designed to be compatible with `ts-wallet-toolbox` StorageClient:

- Same JSON-RPC method names (camelCase)
- Compatible request/response formats
- TypeScript StorageServer.ts equivalent functionality

## License

Same as py-wallet-toolbox project.
