# Health Check System - Usage Guide

## Overview

The Skyy Facial Recognition MCP server includes a comprehensive health check system that monitors critical components and enables graceful degradation when dependencies are unavailable.

## Monitored Components

### 1. InsightFace
- **Purpose:** Face detection and recognition model
- **States:**
  - `healthy`: Model loaded and operational
  - `unavailable`: Model failed to load or initialize
- **Impact when unavailable:** All face operations disabled

### 2. ChromaDB
- **Purpose:** Vector database for face embeddings
- **States:**
  - `healthy`: Database operational
  - `degraded`: Database unavailable but system can queue operations
  - `unavailable`: Complete database failure
- **Impact when unavailable:** System enters degraded mode with registration queuing

### 3. OAuth
- **Purpose:** Authentication and authorization system
- **States:**
  - `healthy`: OAuth keys and config available
  - `unavailable`: OAuth system not initialized
- **Impact when unavailable:** All operations require authentication, blocking all access

## System States

### Healthy
All components operational, all features available:
- User registration: Immediate
- Face recognition: Active
- Database queries: Active
- Similar face search: Active

### Degraded Mode
ChromaDB unavailable but core services operational:
- User registration: Queued for later processing
- Face recognition: Disabled
- Database queries: Disabled
- Similar face search: Disabled

**Important:** Queued registrations are automatically processed when ChromaDB recovers.

### Unavailable
Critical components (InsightFace or OAuth) unavailable:
- All operations disabled
- System requires intervention

## Using the Health Check Tool

### Get Health Status

**MCP Tool:** `skyy_get_health_status`

**Example JSON Response:**
```json
{
  "overall_status": "healthy",
  "components": {
    "insightface": {
      "status": "healthy",
      "message": "InsightFace model loaded successfully",
      "last_checked": "2025-11-19T20:40:42.123456",
      "error": null
    },
    "chromadb": {
      "status": "healthy",
      "message": "ChromaDB operational",
      "last_checked": "2025-11-19T20:40:42.234567",
      "error": null
    },
    "oauth": {
      "status": "healthy",
      "message": "OAuth system operational",
      "last_checked": "2025-11-19T20:40:42.345678",
      "error": null
    }
  },
  "capabilities": {
    "register_user": true,
    "recognize_face": true,
    "get_user_profile": true,
    "list_users": true,
    "delete_user": true,
    "get_database_stats": true,
    "search_similar_faces": true,
    "queue_registration": false
  },
  "degraded_mode": {
    "active": false,
    "queued_registrations": 0
  }
}
```

### Programmatic Usage

**Python Example:**
```python
from health_checker import health_checker, ComponentType

# Check if system is ready for registration
if health_checker.is_healthy(ComponentType.INSIGHTFACE):
    if health_checker.is_healthy(ComponentType.CHROMADB):
        # Normal registration
        result = register_user_immediate(name, image)
    elif health_checker.is_available(ComponentType.CHROMADB):
        # Queue registration for later
        health_checker.queue_registration(name, image, metadata)
        result = {"status": "queued", "queue_position": len(health_checker.registration_queue)}
    else:
        result = {"status": "error", "message": "Database unavailable"}
else:
    result = {"status": "error", "message": "Face recognition unavailable"}

# Get comprehensive health summary
summary = health_checker.get_health_summary()
print(f"System status: {summary['overall_status']}")

# Check specific capabilities
capabilities = health_checker.get_available_capabilities()
if capabilities['recognize_face']:
    # Safe to perform recognition
    pass
```

## Degraded Mode Behavior

### Registration Queuing

When ChromaDB is unavailable:

1. **User Registration Attempt:**
   ```python
   result = await session.call_tool(
       "skyy_register_user",
       arguments={
           "params": {
               "access_token": token,
               "name": "John Doe",
               "image_data": image_base64,
               "metadata": {"department": "Engineering"}
           }
       }
   )
   ```

2. **Response in Degraded Mode:**
   ```json
   {
     "status": "queued",
     "message": "Registration queued - ChromaDB unavailable",
     "user": {
       "name": "John Doe",
       "queue_position": 3
     }
   }
   ```

3. **Automatic Processing on Recovery:**
   - When ChromaDB becomes healthy, queued registrations are available via `get_queued_registrations()`
   - System administrator or automated process can process the queue
   - Each registration is processed with original parameters

### Queue Management

**Get Queued Registrations:**
```python
queued = health_checker.get_queued_registrations()
for registration in queued:
    print(f"Name: {registration.name}")
    print(f"Queued at: {registration.timestamp}")
    print(f"Metadata: {registration.metadata}")
```

**Clear Queue After Processing:**
```python
# After successfully processing all queued registrations
health_checker.clear_registration_queue()
```

## Health State Monitoring

### Register State Change Callback

```python
def on_health_change(component, old_status, new_status):
    print(f"Component {component.value} changed from {old_status.value} to {new_status.value}")

    if component == ComponentType.CHROMADB:
        if new_status == HealthStatus.HEALTHY and old_status == HealthStatus.DEGRADED:
            # ChromaDB recovered - process queue
            process_registration_queue()

health_checker.register_state_change_callback(on_health_change)
```

### Manual Health Checks

```python
# Check InsightFace
async def check_face_model():
    is_healthy = await health_checker.check_insightface(
        lambda: initialize_face_app()
    )
    return is_healthy

# Check ChromaDB
async def check_database():
    is_available = await health_checker.check_chromadb(
        lambda: initialize_chromadb()
    )
    return is_available

# Check OAuth
async def check_auth():
    is_healthy = await health_checker.check_oauth(oauth_config)
    return is_healthy
```

## Capability-Based Operations

The health check system provides capability flags for each operation:

```python
capabilities = health_checker.get_available_capabilities()

# Check before operation
if capabilities['recognize_face']:
    result = recognize_face(image)
else:
    result = {"error": "Face recognition unavailable"}

if capabilities['register_user']:
    # ChromaDB is available (healthy or degraded)
    result = register_user(name, image)
elif capabilities['queue_registration']:
    # Can queue even if ChromaDB degraded
    health_checker.queue_registration(name, image, metadata)
    result = {"status": "queued"}
```

## Testing

### Run Health Check Tests

```bash
cd "C:\Users\Fritz\Documents\MDC\Advanced NLP\PROJECT\FACIAL_RECOGNITION_MCP"
facial_mcp_py311\Scripts\python.exe tests/integration/test_health_checks.py
```

### Test Scenarios Covered

1. **Normal Operations:**
   - All components healthy
   - All capabilities available
   - Standard registration and recognition

2. **Degraded Mode:**
   - ChromaDB unavailable
   - Registration queuing active
   - Recognition disabled

3. **Component Failures:**
   - InsightFace unavailable
   - OAuth system failure
   - Recovery from failures

## Best Practices

### 1. Check Health Before Critical Operations
```python
# Always check health before batch operations
summary = health_checker.get_health_summary()
if summary['overall_status'] != 'healthy':
    print(f"Warning: System in {summary['overall_status']} state")
    print(f"Queued registrations: {summary['degraded_mode']['queued_registrations']}")
```

### 2. Handle Degraded Mode Gracefully
```python
if health_checker.is_healthy(ComponentType.CHROMADB):
    # Normal path
    result = immediate_registration(user)
else:
    # Degraded path
    health_checker.queue_registration(user.name, user.image, user.metadata)
    result = {"status": "queued", "message": "Will be processed when database recovers"}
```

### 3. Monitor Queue Size
```python
summary = health_checker.get_health_summary()
queue_size = summary['degraded_mode']['queued_registrations']
if queue_size > 100:
    alert_admin(f"Large registration queue: {queue_size} pending")
```

### 4. Implement Auto-Recovery
```python
def on_chromadb_recovery(component, old_status, new_status):
    if component == ComponentType.CHROMADB and new_status == HealthStatus.HEALTHY:
        queued = health_checker.get_queued_registrations()
        logger.info(f"Processing {len(queued)} queued registrations")

        for registration in queued:
            try:
                process_registration(registration)
            except Exception as e:
                logger.error(f"Failed to process {registration.name}: {e}")

        health_checker.clear_registration_queue()
        logger.info("Queue processing complete")

health_checker.register_state_change_callback(on_chromadb_recovery)
```

## Troubleshooting

### Issue: All Operations Return "Unavailable"
**Check:** Health status of all components
```python
summary = health_checker.get_health_summary()
for component, health in summary['components'].items():
    if health['status'] == 'unavailable':
        print(f"Problem: {component} - {health['message']}")
```

### Issue: Registrations Stuck in Queue
**Check:** ChromaDB health and recovery status
```python
if not health_checker.is_healthy(ComponentType.CHROMADB):
    print("ChromaDB still unavailable")
    print(f"Queue size: {len(health_checker.registration_queue)}")
    # Investigate ChromaDB connectivity
```

### Issue: Health Check Takes Too Long
**Note:** Initial health checks include:
- InsightFace model loading (~200MB download on first run)
- ChromaDB initialization and connectivity test
- OAuth key verification

Subsequent checks are much faster as models are cached.

## API Reference

### HealthChecker Methods

- `update_health(component, status, message, error=None)` - Update component health
- `get_health(component)` - Get health status for component
- `is_healthy(component)` - Check if component is healthy
- `is_available(component)` - Check if component is available (healthy or degraded)
- `queue_registration(name, image_data, metadata)` - Queue a registration
- `get_queued_registrations()` - Get all queued registrations
- `clear_registration_queue()` - Clear the queue
- `get_available_capabilities()` - Get capability availability map
- `get_health_summary()` - Get comprehensive health summary
- `register_state_change_callback(callback)` - Register state change handler

### Health Status Enum

- `HealthStatus.HEALTHY` - Component fully operational
- `HealthStatus.DEGRADED` - Component partially operational
- `HealthStatus.UNAVAILABLE` - Component not operational

### Component Type Enum

- `ComponentType.INSIGHTFACE` - Face recognition model
- `ComponentType.CHROMADB` - Vector database
- `ComponentType.OAUTH` - Authentication system

---

For more information, see:
- `src/health_checker.py` - Health checker implementation
- `tests/integration/test_health_checks.py` - Test examples
- `HEALTH_CHECK_DEBUG_SUMMARY.md` - Debug and fix history
