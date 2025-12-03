#!/usr/bin/env python3
"""
Example usage of the Triones controller module

This script demonstrates various ways to control Triones RGBW LED controllers.
"""

import asyncio
import logging
from triones import (
    discover_controllers, 
    connect_by_name, 
    TrionesController, 
    TrionesMode,
    TrionesScanner
)

# Enable debug logging to see what's happening
logging.basicConfig(level=logging.INFO)

async def basic_usage_example():
    """Basic usage example - discover and control controllers"""
    print("🔍 Basic Usage Example")
    print("=" * 50)
    
    # Discover all Triones controllers
    controllers = await discover_controllers(timeout=10.0)
    
    if not controllers:
        print("❌ No Triones controllers found!")
        return
    
    print(f"✅ Found {len(controllers)} controller(s)")
    
    # Use the first controller
    controller = controllers[0]
    
    try:
        # Connect to the controller
        print(f"\n🔗 Connecting to {controller.name}...")
        if await controller.connect():
            print("✅ Connected successfully!")
            
            # Get current status
            print("\n📊 Getting current status...")
            status = await controller.get_status()
            if status:
                print(f"  Power: {'ON' if status.is_on else 'OFF'}")
                print(f"  RGB: {status.rgb_tuple} ({status.rgb_hex})")
                print(f"  White: {status.white}")
                print(f"  Mode: {status.mode}")
            
            # Turn on the controller
            print("\n🔌 Turning on...")
            await controller.power_on()
            await asyncio.sleep(1)
            
            # Set some colors
            colors = [
                (255, 0, 0, "Red"),
                (0, 255, 0, "Green"), 
                (0, 0, 255, "Blue"),
                (255, 255, 0, "Yellow"),
                (255, 0, 255, "Magenta"),
                (0, 255, 255, "Cyan"),
                (255, 255, 255, "White")
            ]
            
            print("\n🎨 Cycling through colors...")
            for r, g, b, color_name in colors:
                print(f"  Setting to {color_name} RGB({r}, {g}, {b})")
                await controller.set_rgb(r, g, b)
                await asyncio.sleep(2)
            
            # Set using hex colors
            print("\n🎨 Setting colors using hex...")
            hex_colors = ["#FF6B6B", "#4ECDC4", "#45B7D1", "#96CEB4", "#FFEAA7"]
            for hex_color in hex_colors:
                print(f"  Setting to {hex_color}")
                await controller.set_color_hex(hex_color)
                await asyncio.sleep(2)
            
            # Test white mode
            print("\n⚪ Testing white mode...")
            for intensity in [50, 100, 150, 200, 255]:
                print(f"  White intensity: {intensity}")
                await controller.set_white(intensity)
                await asyncio.sleep(1)
            
            # Test built-in modes
            print("\n✨ Testing built-in modes...")
            modes = [
                (TrionesMode.SEVEN_COLOR_CROSS_FADE, "Seven Color Cross Fade"),
                (TrionesMode.RED_STROBE, "Red Strobe"),
                (TrionesMode.SEVEN_COLOR_JUMPING, "Seven Color Jumping")
            ]
            
            for mode, mode_name in modes:
                print(f"  Mode: {mode_name}")
                await controller.set_built_in_mode(mode, speed=50)
                await asyncio.sleep(3)
            
            # Return to static color
            print("\n🎨 Returning to static green...")
            await controller.set_rgb(0, 255, 0)
            
        else:
            print("❌ Failed to connect!")
    
    except Exception as e:
        print(f"❌ Error: {e}")
    
    finally:
        # Always disconnect
        await controller.disconnect()

async def multiple_controllers_example():
    """Example of controlling multiple controllers simultaneously"""
    print("\n🔍 Multiple Controllers Example")
    print("=" * 50)
    
    # Discover controllers
    controllers = await discover_controllers()
    
    if len(controllers) < 2:
        print("⚠️  Need at least 2 controllers for this example")
        return
    
    print(f"✅ Found {len(controllers)} controllers")
    
    try:
        # Connect to all controllers
        print("\n🔗 Connecting to all controllers...")
        connected_controllers = []
        
        for controller in controllers:
            if await controller.connect():
                connected_controllers.append(controller)
                print(f"  ✅ Connected to {controller.name}")
            else:
                print(f"  ❌ Failed to connect to {controller.name}")
        
        if len(connected_controllers) < 2:
            print("❌ Need at least 2 connected controllers")
            return
        
        # Turn all on
        print("\n🔌 Turning all controllers on...")
        for controller in connected_controllers:
            await controller.power_on()
        
        await asyncio.sleep(1)
        
        # Set different colors simultaneously
        print("\n🌈 Setting different colors simultaneously...")
        colors = [
            (255, 0, 0),    # Red
            (0, 255, 0),    # Green  
            (0, 0, 255),    # Blue
            (255, 255, 0),  # Yellow
            (255, 0, 255),  # Magenta
        ]
        
        tasks = []
        for i, controller in enumerate(connected_controllers):
            color = colors[i % len(colors)]
            task = controller.set_rgb(*color)
            tasks.append(task)
        
        # Execute all color changes simultaneously
        await asyncio.gather(*tasks)
        
        print("🎉 All controllers set to different colors!")
        await asyncio.sleep(3)
        
        # Synchronized color cycling
        print("\n🔄 Synchronized color cycling...")
        for r, g, b, name in [(255,0,0,"Red"), (0,255,0,"Green"), (0,0,255,"Blue")]:
            print(f"  All controllers -> {name}")
            tasks = [controller.set_rgb(r, g, b) for controller in connected_controllers]
            await asyncio.gather(*tasks)
            await asyncio.sleep(2)
    
    except Exception as e:
        print(f"❌ Error: {e}")
    
    finally:
        # Disconnect all controllers
        print("\n🔌 Disconnecting all controllers...")
        for controller in connected_controllers:
            await controller.disconnect()

async def specific_controller_example():
    """Example of connecting to a specific controller by name"""
    print("\n🔍 Specific Controller Example")
    print("=" * 50)
    
    # Try to connect to a specific controller
    # Replace with your actual controller name
    target_names = ["Triones:1205110001A0", "Triones:2205110002B3"]
    
    controller = None
    for name in target_names:
        print(f"🔍 Looking for controller: {name}")
        controller = await connect_by_name(name, timeout=5.0)
        if controller:
            print(f"✅ Found and connected to {name}")
            break
        else:
            print(f"❌ Controller {name} not found")
    
    if not controller:
        print("❌ No target controllers found")
        return
    
    try:
        # Get status
        status = await controller.get_status()
        if status:
            print(f"\n📊 Controller Status:")
            print(f"  Name: {controller.name}")
            print(f"  Address: {controller.address}")
            print(f"  Power: {'ON' if status.is_on else 'OFF'}")
            print(f"  RGB: {status.rgb_tuple} ({status.rgb_hex})")
            print(f"  RGBW: {status.rgbw_tuple}")
            print(f"  Mode: {status.mode}")
            print(f"  Speed: {status.speed}")
        
        # Set to a nice purple color
        print(f"\n🟣 Setting to purple...")
        await controller.set_rgb(128, 0, 128)
        
        # Verify the change
        await asyncio.sleep(1)
        new_status = await controller.get_status()
        if new_status:
            print(f"✅ New color: {new_status.rgb_tuple} ({new_status.rgb_hex})")
    
    except Exception as e:
        print(f"❌ Error: {e}")
    
    finally:
        await controller.disconnect()

async def main():
    """Run all examples"""
    print("🎮 Triones Controller Module Examples")
    print("=" * 60)
    
    # Run examples
    await basic_usage_example()
    await asyncio.sleep(2)
    
    await multiple_controllers_example()
    await asyncio.sleep(2)
    
    await specific_controller_example()
    
    print("\n🎉 All examples completed!")

if __name__ == "__main__":
    asyncio.run(main())