#!/usr/bin/env python3
"""
Triones Controller Module Demo

A demonstration of the Triones controller module capabilities.
This script will discover your controllers and set them to green at 50%.
"""

import asyncio
import logging
from triones import discover_controllers

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

async def demo():
    """Demonstrate the Triones module by setting controllers to green"""
    print("🎮 Triones Controller Module Demo")
    print("=" * 50)
    print("This demo will set all your Triones controllers to green at 50%")
    print()
    
    try:
        # Discover controllers
        print("🔍 Discovering Triones controllers...")
        controllers = await discover_controllers(timeout=8.0)
        
        if not controllers:
            print("❌ No Triones controllers found!")
            print("💡 Make sure your controllers are:")
            print("   - Powered on")
            print("   - Not connected to other devices")
            print("   - Within Bluetooth range")
            return
        
        print(f"✅ Found {len(controllers)} controller(s):")
        for i, controller in enumerate(controllers, 1):
            print(f"   {i}. {controller.name} ({controller.address})")
        
        # Connect to all controllers
        print(f"\n🔗 Connecting to controllers...")
        connected = []
        for controller in controllers:
            print(f"   Connecting to {controller.name}...")
            if await controller.connect():
                connected.append(controller)
                print(f"   ✅ Connected!")
            else:
                print(f"   ❌ Failed to connect")
        
        if not connected:
            print("❌ Could not connect to any controllers")
            return
        
        print(f"✅ Connected to {len(connected)} controller(s)")
        
        # Get current status
        print(f"\n📊 Current controller status:")
        for controller in connected:
            status = await controller.get_status()
            if status:
                print(f"   {controller.name}:")
                print(f"     Power: {'ON' if status.is_on else 'OFF'}")
                print(f"     RGB: {status.rgb_tuple} ({status.rgb_hex})")
                print(f"     Mode: {status.mode}")
        
        # Turn all controllers on
        print(f"\n🔌 Ensuring all controllers are powered on...")
        for controller in connected:
            await controller.power_on()
        
        await asyncio.sleep(1)
        
        # Set all controllers to green at 50% (RGB: 0, 127, 0)
        print(f"\n🟢 Setting all controllers to GREEN at 50%...")
        print(f"   Target RGB: (0, 127, 0) = #007F00")
        
        # Send commands simultaneously for synchronization
        tasks = []
        for controller in connected:
            task = controller.set_rgb(0, 127, 0)
            tasks.append(task)
        
        # Execute all commands at once
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Check results
        success_count = sum(1 for result in results if result is True)
        print(f"   ✅ {success_count}/{len(connected)} controllers updated successfully")
        
        # Wait and verify the changes
        await asyncio.sleep(2)
        
        print(f"\n✅ Verifying color changes...")
        all_correct = True
        for controller in connected:
            status = await controller.get_status()
            if status:
                if status.red == 0 and status.green == 127 and status.blue == 0:
                    print(f"   ✅ {controller.name}: {status.rgb_hex} - Correct!")
                else:
                    print(f"   ⚠️  {controller.name}: {status.rgb_hex} - Different color")
                    all_correct = False
        
        if all_correct:
            print(f"\n🎉 SUCCESS! All controllers are now GREEN at 50%")
        else:
            print(f"\n⚠️  Some controllers may not have changed (could be in special mode)")
        
        # Demonstrate a few more colors
        print(f"\n🌈 Bonus: Cycling through a few more colors...")
        colors = [
            (255, 100, 0, "Orange"),
            (100, 0, 255, "Purple"), 
            (255, 255, 0, "Yellow"),
            (0, 255, 255, "Cyan")
        ]
        
        for r, g, b, name in colors:
            print(f"   Setting to {name}...")
            tasks = [controller.set_rgb(r, g, b) for controller in connected]
            await asyncio.gather(*tasks)
            await asyncio.sleep(2)
        
        # Return to green
        print(f"   Returning to GREEN...")
        tasks = [controller.set_rgb(0, 127, 0) for controller in connected]
        await asyncio.gather(*tasks)
        
        print(f"\n🎉 Demo completed successfully!")
        
    except KeyboardInterrupt:
        print(f"\n⏹️  Demo interrupted by user")
    
    except Exception as e:
        print(f"\n❌ Demo failed with error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Cleanup - disconnect all controllers
        print(f"\n🔌 Disconnecting controllers...")
        if 'connected' in locals():
            for controller in connected:
                try:
                    await controller.disconnect()
                    print(f"   Disconnected from {controller.name}")
                except:
                    pass
        
        print(f"✅ Demo finished!")

def main():
    """Entry point for console script"""
    print("Starting Triones Controller Demo...")
    asyncio.run(demo())

if __name__ == "__main__":
    main()