#!/usr/bin/env python3
"""
Demo script to show how the warehouse activation functionality works
"""

import asyncio
from warehouse_bot.src.application.dto.incoming_orders import ActivateWarehouseDTO
from warehouse_bot.src.application.use_cases.warehouse_activation import ActivateWarehouseUseCase
from warehouse_bot.src.infrastructure.di.container import Container
from warehouse_bot.config.settings import settings


async def demo_activation():
    """
    Demonstrate the warehouse activation flow
    """
    print("=== Warehouse Activation Demo ===\n")
    
    # Initialize DI container
    container = Container()
    container.config.from_dict(settings.model_dump())
    
    # Get the use case
    activate_use_case = container.activate_warehouse_use_case()
    
    print("1. Creating activation request...")
    dto = ActivateWarehouseDTO(
        warehouse_id="warehouse_123",
        activation_code="ABC123",
        chat_id=123456789
    )
    
    print(f"   - Warehouse ID: {dto.warehouse_id}")
    print(f"   - Activation Code: {dto.activation_code}")
    print(f"   - Chat ID: {dto.chat_id}")
    
    print("\n2. Executing activation use case...")
    print("   - Validating warehouse via CRM...")
    print("   - Validating activation code via CRM...") 
    print("   - Checking for existing bindings in local database...")
    print("   - Creating chat-to-warehouse binding in local database...")
    
    try:
        # In real usage, this would make actual CRM calls and database operations
        # For demo, we'll just show the flow
        success = True  # This would be the result of the actual execution
        print(f"\n3. Activation result: {'SUCCESS' if success else 'FAILED'}")
        
        if success:
            print("   - Warehouse successfully activated!")
            print("   - Chat ID is now bound to Warehouse ID in local database")
            print("   - All future verifications happen in local database")
    
    except Exception as e:
        print(f"\n3. Activation failed: {str(e)}")
    
    print("\n=== Deactivation Demo ===")
    print("1. User sends /deactivate command...")
    print("2. Deactivation happens locally in database (no CRM needed)")
    print("3. Chat-to-warehouse binding removed from local database")
    
    print("\n=== Verification Process ===")
    print("1. When checking if chat is bound to warehouse:")
    print("   - System queries local database")
    print("   - No CRM interaction required")
    print("   - Fast local verification")


if __name__ == "__main__":
    asyncio.run(demo_activation())