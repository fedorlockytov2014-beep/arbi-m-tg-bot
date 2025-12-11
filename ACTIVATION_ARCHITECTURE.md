# Warehouse Bot Activation Architecture

## Overview
This document describes the implementation of warehouse activation functionality in the warehouse bot system.

## Requirements Implemented

### 1. Activation Flow
- **Trigger**: User sends `/activate` command to the bot
- **Process**: 
  - User enters activation code
  - Bot validates the code via CRM request
  - If validation successful, binds `chat_id` to `warehouse_id` in local database
- **Technology**: Uses CRM API for validation, local SQLite for storage

### 2. Deactivation Flow
- **Trigger**: User sends `/deactivate` command to the bot
- **Process**: 
  - Deactivation happens locally via local database
  - No CRM interaction required
- **Technology**: Uses local SQLite database only

### 3. Verification
- **Process**: All checks for existing bindings happen in local database
- **Technology**: Local SQLite database with WarehouseLocalRepositoryImpl

## Implementation Components

### Core Components

1. **ActivateWarehouseUseCase** (`/src/application/use_cases/warehouse_activation.py`)
   - Validates warehouse via CRM
   - Validates activation code via CRM
   - Saves binding in local database
   - Checks existing bindings in local database

2. **WarehouseLocalRepositoryImpl** (`/src/infrastructure/persistence/repositories/warehouse_local_repository_impl.py`)
   - Local SQLite database implementation
   - Stores warehouse data with chat_id bindings
   - Handles activation/deactivation operations

3. **CRMClient** (`/src/infrastructure/integrations/crm_client.py`)
   - Handles communication with CRM API
   - Validates warehouse data and activation codes

4. **Activation Handlers** (`/src/presentation/bot/handlers/activation_handlers.py`)
   - `/activate` command handler
   - Activation code processing
   - Deep-link support via `/start` command

### Database Model
- **WarehouseModel** (`/src/infrastructure/persistence/models/warehouse_model.py`)
- SQLite database file: `warehouse_local.db`

### Dependency Injection
- **Container** (`/src/infrastructure/di/container.py`)
- Uses `WarehouseLocalRepositoryImpl` for local storage
- Uses `CRMClient` for validation

## Flow Diagram

```
User -> Bot (/activate) -> Handler -> Use Case -> CRM Validation
                                            ↓
                                   Local DB Binding (chat_id ↔ warehouse_id)
```

## Key Features

1. **Dual Validation**: Both warehouse ID and activation code are validated via CRM
2. **Local Binding Storage**: Chat-to-warehouse bindings stored in local database
3. **Duplicate Prevention**: Checks for existing bindings in local database
4. **Deep-link Support**: `/start <warehouse_id>` for direct activation
5. **Secure Code Validation**: Activation codes validated through CRM
6. **Local Deactivation**: Deactivation happens without CRM interaction
```