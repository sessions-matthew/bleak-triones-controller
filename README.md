# Triones Controller Module

A Python module for controlling Triones RGBW Bluetooth LED controllers using the official Triones protocol.

## Features

- ✅ **Full RGB Control** - Set any RGB color (0-255 per channel)
- ✅ **White Channel Support** - Control dedicated white LEDs
- ✅ **Power Management** - Turn controllers on/off
- ✅ **Built-in Modes** - Access all 20 built-in lighting effects
- ✅ **Multiple Controllers** - Control multiple controllers simultaneously
- ✅ **Auto-Discovery** - Automatically find Triones controllers
- ✅ **Status Reading** - Get current color and state
- ✅ **Protocol Compliant** - Based on official Triones protocol specification
- ✅ **Async Support** - Full asyncio support for non-blocking operation

## Installation

### Requirements

- Python 3.7+
- `bleak` library for Bluetooth communication

### Option 1: Install from Source (Recommended)

```bash
# Clone or download this repository
git clone https://github.com/sessions-matthew/bleak-triones-controller
cd bleak-triones-controller

# Install in development mode
pip install -e .

# Run the demo
triones-demo
```

### Option 2: Install Dependencies Only

```bash
pip install -r requirements.txt
```

Then copy `triones.py` to your project directory.

### Option 3: Manual Installation

```bash
pip install bleak>=0.21.0
```

Copy `triones.py` to your project directory or install it in your Python path.

## Quick Start

```python
import asyncio
from triones import discover_controllers

async def main():
    # Discover all Triones controllers
    controllers = await discover_controllers()
    
    if controllers:
        controller = controllers[0]
        
        # Connect and set color
        await controller.connect()
        await controller.power_on()
        await controller.set_rgb(255, 0, 0)  # Red
        await controller.disconnect()

asyncio.run(main())
```

## Demo Script

Run the included demo to see the module in action:

```bash
# If installed with pip install -e .
triones-demo

# Or run directly
python examples/demo.py
```

The demo will:
1. Discover all Triones controllers
2. Set them to green at 50% brightness
3. Verify the color change
4. Cycle through some colors
5. Properly disconnect

## Usage Examples

### Basic Color Control

```python
import asyncio
from triones import connect_by_name

async def set_colors():
    # Connect to specific controller
    controller = await connect_by_name("Triones:1205110001A0")
    
    if controller:
        # Set RGB colors
        await controller.set_rgb(255, 0, 0)     # Red
        await controller.set_rgb(0, 255, 0)     # Green
        await controller.set_rgb(0, 0, 255)     # Blue
        
        # Set using hex colors
        await controller.set_color_hex("#FF6B6B")  # Coral
        await controller.set_color_hex("#4ECDC4")  # Turquoise
        
        # Set white mode
        await controller.set_white(255)         # Full white
        
        await controller.disconnect()

asyncio.run(set_colors())
```

### Built-in Lighting Effects

```python
import asyncio
from triones import discover_controllers, TrionesMode

async def lighting_effects():
    controllers = await discover_controllers()
    
    if controllers:
        controller = controllers[0]
        await controller.connect()
        
        # Built-in effects
        await controller.set_built_in_mode(TrionesMode.SEVEN_COLOR_CROSS_FADE, speed=50)
        await controller.set_built_in_mode(TrionesMode.RED_STROBE, speed=100)
        await controller.set_built_in_mode(TrionesMode.RAINBOW_JUMPING, speed=25)
        
        await controller.disconnect()

asyncio.run(lighting_effects())
```

### Multiple Controllers

```python
import asyncio
from triones import discover_controllers

async def sync_multiple():
    controllers = await discover_controllers()
    
    # Connect to all
    for controller in controllers:
        await controller.connect()
        await controller.power_on()
    
    # Set all to same color simultaneously
    tasks = [controller.set_rgb(0, 255, 0) for controller in controllers]
    await asyncio.gather(*tasks)
    
    # Disconnect all
    for controller in controllers:
        await controller.disconnect()

asyncio.run(sync_multiple())
```

### Get Controller Status

```python
import asyncio
from triones import connect_by_name

async def check_status():
    controller = await connect_by_name("Triones:1205110001A0")
    
    if controller:
        status = await controller.get_status()
        
        print(f"Power: {'ON' if status.is_on else 'OFF'}")
        print(f"RGB: {status.rgb_tuple}")
        print(f"RGB Hex: {status.rgb_hex}")
        print(f"White: {status.white}")
        print(f"Mode: {status.mode}")
        
        await controller.disconnect()

asyncio.run(check_status())
```

## API Reference

### TrionesController

Main controller class for individual devices.

#### Methods

- `connect()` - Connect to the controller
- `disconnect()` - Disconnect from the controller
- `get_status()` - Get current controller status
- `power_on()` - Turn controller on
- `power_off()` - Turn controller off
- `set_rgb(r, g, b)` - Set RGB color (0-255 each)
- `set_white(intensity)` - Set white mode (0-255)
- `set_color_hex(hex_string)` - Set color using hex string
- `set_built_in_mode(mode, speed)` - Activate built-in lighting effect

### TrionesScanner

Utility class for discovering controllers.

#### Methods

- `discover(timeout, device_names)` - Discover all controllers
- `find_by_name(name, timeout)` - Find controller by name
- `find_by_address(address, timeout)` - Find controller by MAC address

### TrionesStatus

Status information returned by `get_status()`.

#### Properties

- `is_on` - Power state (bool)
- `rgb_tuple` - RGB values as (r, g, b)
- `rgbw_tuple` - RGBW values as (r, g, b, w)
- `rgb_hex` - RGB as hex string (e.g., "#FF0000")
- `red`, `green`, `blue`, `white` - Individual channel values
- `mode` - Current lighting mode
- `speed` - Current speed setting

### TrionesMode (Enum)

Built-in lighting modes:

- `STATIC_COLOR` - Static color mode
- `SEVEN_COLOR_CROSS_FADE` - Rainbow cross fade
- `RED_GRADUAL`, `GREEN_GRADUAL`, `BLUE_GRADUAL` - Single color gradual
- `SEVEN_COLOR_STROBE` - Rainbow strobe
- `RED_STROBE`, `GREEN_STROBE`, `BLUE_STROBE` - Single color strobe
- And more...

## Protocol Information

This module implements the official Triones protocol specification:
- Based on reverse engineering by [madhead](https://github.com/madhead/saberlight/blob/master/protocols/Triones/protocol.md)
- Uses correct GATT characteristics and command formats
- Supports both RGB and RGBW controllers
- Handles status responses according to specification

### Command Formats

- **RGB Color**: `[0x56, R, G, B, 0x00, 0xF0, 0xAA]`
- **White Mode**: `[0x56, 0x00, 0x00, 0x00, W, 0x0F, 0xAA]`
- **Power On/Off**: `[0xCC, 0x23/0x24, 0x33]`
- **Built-in Mode**: `[0xBB, MODE, SPEED, 0x44]`
- **Status Request**: `[0xEF, 0x01, 0x77]`

## Troubleshooting

### Controller Not Found
- Ensure controller is powered on
- Check that Bluetooth is enabled
- Try increasing discovery timeout
- Verify controller is in pairing mode

### Connection Failed
- Controller might be connected to another device
- Try power cycling the controller
- Check Bluetooth permissions
- Ensure no other apps are using the controller

### Commands Not Working
- Verify controller is connected
- Check that controller supports the command
- Some controllers may have firmware differences

## License

MIT License - Feel free to use in your projects!

## Contributing

Contributions welcome! Please test with your specific Triones controllers and report any issues.