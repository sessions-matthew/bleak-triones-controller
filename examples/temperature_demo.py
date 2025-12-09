#!/usr/bin/env python3
"""
Triones Temperature Demo

A demonstration of the color temperature functionality in the Triones controller module.
This script will cycle through various color temperatures to show the RGBW temperature control.
"""

import asyncio
import logging
from triones import discover_controllers

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

async def temperature_demo():
    """Demonstrate the Triones temperature functionality"""
    print("🌡️  Triones Color Temperature Demo")
    print("=" * 50)
    print("This demo will cycle through various color temperatures")
    print("using both RGB and white LEDs for maximum brightness and accurate reproduction")
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
        
        # Turn all controllers on
        print(f"\n🔌 Ensuring all controllers are powered on...")
        for controller in connected:
            await controller.power_on()
        
        await asyncio.sleep(1)
        
        # Define temperature demonstrations
        temperatures = [
            (1000, "🕯️  Deep warm amber (candlelight)"),
            (2000, "🕯️  Candlelight"),
            (2700, "💡 Warm white (incandescent)"),
            (3000, "💡 Warm white (halogen)"),
            (4000, "🏠 Cool white (office)"),
            (5000, "☀️  Daylight"),
            (6500, "☀️  Cool daylight"),
            (8000, "🌤️  Overcast sky"),
            (10000, "🔵 Blue sky")
        ]
        
        print(f"\n🌡️  Cycling through color temperatures...")
        print(f"Each temperature will be shown for 4 seconds")
        print()
        
        for temp, description in temperatures:
            print(f"Setting to {temp}K - {description}")
            
            # Send temperature commands simultaneously to all controllers
            tasks = []
            for controller in connected:
                task = controller.set_temperature(temp, brightness=0.8)
                tasks.append(task)
            
            # Execute all commands at once for synchronization
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Check results
            success_count = sum(1 for result in results if result is True)
            print(f"   ✅ {success_count}/{len(connected)} controllers updated")
            
            # Wait to observe the temperature
            await asyncio.sleep(4)
        
        # Demonstrate brightness control at different temperatures
        print(f"\n💡 Demonstrating brightness control...")
        test_temps = [2700, 6500]  # Warm and cool
        brightnesses = [0.2, 0.5, 1.0]
        
        for temp in test_temps:
            temp_name = "Warm white" if temp == 2700 else "Cool daylight"
            print(f"\n{temp}K ({temp_name}) at different brightness levels:")
            
            for brightness in brightnesses:
                print(f"   Setting brightness to {int(brightness * 100)}%...")
                
                tasks = []
                for controller in connected:
                    task = controller.set_temperature(temp, brightness=brightness)
                    tasks.append(task)
                
                await asyncio.gather(*tasks, return_exceptions=True)
                await asyncio.sleep(2)
        
        # Final demonstration - smooth temperature transition
        print(f"\n🌈 Smooth temperature transition (warm to cool)...")
        temp_range = list(range(2000, 8001, 500))  # 2000K to 8000K in 500K steps
        
        for temp in temp_range:
            print(f"   {temp}K...")
            
            tasks = []
            for controller in connected:
                task = controller.set_temperature(temp, brightness=0.7)
                tasks.append(task)
            
            await asyncio.gather(*tasks, return_exceptions=True)
            await asyncio.sleep(1.5)
        
        # End with a pleasant daylight temperature
        print(f"\n✨ Finishing with comfortable 5000K daylight...")
        tasks = []
        for controller in connected:
            task = controller.set_temperature(5000, brightness=0.6)
            tasks.append(task)
        
        await asyncio.gather(*tasks, return_exceptions=True)
        
        print(f"\n🎉 Temperature demo completed successfully!")
        print(f"💡 Your controllers are now set to 5000K daylight at 60% brightness")
        
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
        
        print(f"✅ Temperature demo finished!")

def main():
    """Entry point for console script"""
    print("Starting Triones Color Temperature Demo...")
    asyncio.run(temperature_demo())

if __name__ == "__main__":
    main()