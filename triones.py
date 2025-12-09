"""
Triones Controller Module

A Python module for controlling Triones RGBW Bluetooth LED controllers.
Based on the official Triones protocol specification and reverse engineering.

Author: GitHub Copilot & User
License: MIT
"""

import asyncio
import math
import platform
from typing import List, Tuple, Optional, Dict, Any
from bleak import BleakScanner, BleakClient
from bleak.backends.device import BLEDevice
import logging
from dataclasses import dataclass
from enum import Enum

# Configure logging
logger = logging.getLogger(__name__)

class TrionesMode(Enum):
    """Triones controller modes"""
    STATIC_COLOR = 0x41
    SEVEN_COLOR_CROSS_FADE = 0x25
    RED_GRADUAL = 0x26
    GREEN_GRADUAL = 0x27
    BLUE_GRADUAL = 0x28
    YELLOW_GRADUAL = 0x29
    CYAN_GRADUAL = 0x2A
    PURPLE_GRADUAL = 0x2B
    WHITE_GRADUAL = 0x2C
    RED_GREEN_CROSS_FADE = 0x2D
    RED_BLUE_CROSS_FADE = 0x2E
    GREEN_BLUE_CROSS_FADE = 0x2F
    SEVEN_COLOR_STROBE = 0x30
    RED_STROBE = 0x31
    GREEN_STROBE = 0x32
    BLUE_STROBE = 0x33
    YELLOW_STROBE = 0x34
    CYAN_STROBE = 0x35
    PURPLE_STROBE = 0x36
    WHITE_STROBE = 0x37
    SEVEN_COLOR_JUMPING = 0x38

@dataclass
class TrionesStatus:
    """Triones controller status information"""
    is_on: bool
    mode: int
    speed: int
    red: int
    green: int
    blue: int
    white: int
    raw_response: bytes
    
    @property
    def rgb_hex(self) -> str:
        """RGB color as hex string"""
        return f"#{self.red:02x}{self.green:02x}{self.blue:02x}"
    
    @property
    def rgb_tuple(self) -> Tuple[int, int, int]:
        """RGB values as tuple"""
        return (self.red, self.green, self.blue)
    
    @property
    def rgbw_tuple(self) -> Tuple[int, int, int, int]:
        """RGBW values as tuple"""
        return (self.red, self.green, self.blue, self.white)

class TrionesController:
    """
    Triones RGBW Bluetooth LED Controller
    
    Supports RGB and White color control, power management, and built-in lighting modes.
    Based on the official Triones protocol specification.
    """
    
    # Protocol constants
    SERVICE_UUID = "0000ffd5-0000-1000-8000-00805f9b34fb"
    WRITE_CHARACTERISTIC = "0000ffd9-0000-1000-8000-00805f9b34fb"
    NOTIFY_CHARACTERISTIC_1 = "0000ffda-0000-1000-8000-00805f9b34fb"
    NOTIFY_CHARACTERISTIC_2 = "0000ffd4-0000-1000-8000-00805f9b34fb"
    
    # Magic constants
    HEADER_MAGIC = 0x66
    FOOTER_MAGIC = 0x99
    POWER_ON = 0x23
    POWER_OFF = 0x24
    
    def __init__(self, device: BLEDevice, auto_connect: bool = True):
        """
        Initialize Triones controller
        
        Args:
            device: BleakDevice object for the controller
            auto_connect: Whether to automatically connect when needed
        """
        self.device = device
        self.auto_connect = auto_connect
        self._client: Optional[BleakClient] = None
        self._connected = False
        
    @property
    def name(self) -> str:
        """Controller device name"""
        return self.device.name or "Unknown Triones"
    
    @property
    def address(self) -> str:
        """Controller MAC address"""
        return self.device.address
    
    @property
    def is_connected(self) -> bool:
        """Check if controller is connected"""
        return self._connected and self._client is not None
    
    async def connect(self) -> bool:
        """
        Connect to the controller
        
        Returns:
            bool: True if connection successful
        """
        if self.is_connected:
            return True
            
        try:
            self._client = BleakClient(self.device.address)
            await self._client.connect()
            
            # Force service discovery - especially important on Windows
            # Wait a moment for connection to stabilize
            await asyncio.sleep(0.5)
            
            # Access services to ensure discovery has happened
            # On Windows, this might trigger service discovery if not already done
            try:
                services = self._client.services
                if services:
                    service_count = len([s for s in services])
                    logger.debug(f"Services discovered: {service_count}")
                    
                    # Check if our required service exists
                    service_found = any(
                        str(service.uuid).lower() == self.SERVICE_UUID.lower() 
                        for service in services
                    )
                    
                    if not service_found:
                        logger.warning(f"Required service {self.SERVICE_UUID} not found")
                        # Try to find any services that might work
                        for service in services:
                            logger.debug(f"Available service: {service.uuid}")
                else:
                    logger.warning("No services discovered - this may cause write failures")
                    
            except Exception as service_error:
                logger.warning(f"Service discovery issue: {service_error}")
            
            # Additional wait for Windows stability
            await asyncio.sleep(0.2)
            
            self._connected = True
            logger.info(f"Connected to {self.name} ({self.address})")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to {self.name}: {e}")
            self._connected = False
            if self._client:
                try:
                    await self._client.disconnect()
                except:
                    pass
                self._client = None
            return False
    
    async def _force_reconnect(self):
        """Force disconnect and clear connection state for reconnection"""
        self._connected = False
        if self._client:
            try:
                await self._client.disconnect()
            except:
                pass
            self._client = None
    
    async def disconnect(self):
        """Disconnect from the controller"""
        if self._client and self._connected:
            try:
                await self._client.disconnect()
                logger.info(f"Disconnected from {self.name}")
            except Exception as e:
                logger.error(f"Error disconnecting from {self.name}: {e}")
            finally:
                self._connected = False
                self._client = None
    
    async def _ensure_connected(self) -> bool:
        """Ensure controller is connected"""
        if not self.is_connected and self.auto_connect:
            return await self.connect()
        return self.is_connected
    
    async def _write_command(self, command: bytes) -> bool:
        """
        Write command to controller
        
        Args:
            command: Command bytes to send
            
        Returns:
            bool: True if command sent successfully
        """
        if not await self._ensure_connected():
            return False
            
        try:
            await self._client.write_gatt_char(self.WRITE_CHARACTERISTIC, command)
            logger.debug(f"Sent command: {command.hex()}")
            
            # On Windows, add small delay after longer commands for processing
            if platform.system() == "Windows" and len(command) > 4:
                await asyncio.sleep(0.05)
            
            return True
        except Exception as e:
            logger.error(f"Failed to write command {command.hex()}: {e}")
            
            # On Windows, try reconnecting once if write fails
            if platform.system() == "Windows" and "not connected" in str(e).lower():
                logger.info("Attempting reconnection after write failure")
                await self._force_reconnect()
                if await self._ensure_connected():
                    try:
                        await self._client.write_gatt_char(self.WRITE_CHARACTERISTIC, command)
                        logger.debug(f"Sent command after reconnection: {command.hex()}")
                        return True
                    except Exception as retry_e:
                        logger.error(f"Retry write failed: {retry_e}")
            
            return False
    
    async def _get_status_response(self) -> Optional[bytes]:
        """
        Get status response from controller
        
        Returns:
            bytes: Response data or None if failed
        """
        if not await self._ensure_connected():
            return None
            
        response_data = None
        
        def notification_handler(sender, data):
            nonlocal response_data
            response_data = data
            logger.debug(f"Received response: {data.hex()}")
        
        try:
            # Subscribe to notifications
            for char in [self.NOTIFY_CHARACTERISTIC_1, self.NOTIFY_CHARACTERISTIC_2]:
                try:
                    await self._client.start_notify(char, notification_handler)
                except Exception as e:
                    logger.debug(f"Could not start notify on {char}: {e}")
            
            # Send status request
            status_command = bytes([0xEF, 0x01, 0x77])
            if await self._write_command(status_command):
                # Wait for response
                await asyncio.sleep(1.5)
            
            # Stop notifications
            for char in [self.NOTIFY_CHARACTERISTIC_1, self.NOTIFY_CHARACTERISTIC_2]:
                try:
                    await self._client.stop_notify(char)
                except:
                    pass
                    
            return response_data
            
        except Exception as e:
            logger.error(f"Failed to get status response: {e}")
            return None
    
    def _parse_status_response(self, response: bytes) -> Optional[TrionesStatus]:
        """
        Parse status response according to Triones protocol
        
        Args:
            response: Raw response bytes
            
        Returns:
            TrionesStatus: Parsed status or None if invalid
        """
        if not response or len(response) != 12:
            logger.error(f"Invalid response length: {len(response) if response else 0}")
            return None
        
        if response[0] != self.HEADER_MAGIC or response[11] != self.FOOTER_MAGIC:
            logger.error("Invalid response magic constants")
            return None
        
        # Parse according to official protocol
        power_status = response[2]  # 0x23=ON, 0x24=OFF
        mode = response[3]          # Mode value
        speed = response[5]         # Speed parameter
        red = response[6]           # Red component
        green = response[7]         # Green component  
        blue = response[8]          # Blue component
        white = response[9]         # White component
        
        is_on = power_status == self.POWER_ON
        
        return TrionesStatus(
            is_on=is_on,
            mode=mode,
            speed=speed,
            red=red,
            green=green,
            blue=blue,
            white=white,
            raw_response=response
        )
    
    async def get_status(self) -> Optional[TrionesStatus]:
        """
        Get current controller status
        
        Returns:
            TrionesStatus: Current status or None if failed
        """
        response = await self._get_status_response()
        if response:
            return self._parse_status_response(response)
        return None
    
    async def power_on(self) -> bool:
        """
        Turn controller on
        
        Returns:
            bool: True if command sent successfully
        """
        command = bytes([0xCC, self.POWER_ON, 0x33])
        return await self._write_command(command)
    
    async def power_off(self) -> bool:
        """
        Turn controller off
        
        Returns:
            bool: True if command sent successfully
        """
        command = bytes([0xCC, self.POWER_OFF, 0x33])
        return await self._write_command(command)
    
    async def set_rgb(self, red: int, green: int, blue: int) -> bool:
        """
        Set RGB color (static color mode)
        
        Args:
            red: Red component (0-255)
            green: Green component (0-255)
            blue: Blue component (0-255)
            
        Returns:
            bool: True if command sent successfully
        """
        # Validate input
        for val in [red, green, blue]:
            if not 0 <= val <= 255:
                raise ValueError(f"RGB values must be 0-255, got: {red}, {green}, {blue}")
        
        # Official Triones RGB command format
        command = bytes([0x56, red, green, blue, 0x00, 0xF0, 0xAA])
        return await self._write_command(command)
    
    async def set_white(self, intensity: int) -> bool:
        """
        Set white color mode
        
        Args:
            intensity: White intensity (0-255)
            
        Returns:
            bool: True if command sent successfully
        """
        if not 0 <= intensity <= 255:
            raise ValueError(f"White intensity must be 0-255, got: {intensity}")
        
        # Official Triones white command format
        command = bytes([0x56, 0x00, 0x00, 0x00, intensity, 0x0F, 0xAA])
        return await self._write_command(command)
    
    async def set_built_in_mode(self, mode: int, speed: int = 1) -> bool:
        """
        Set built-in lighting mode
        
        Args:
            mode: Built-in mode (37-56 decimal, or use TrionesMode enum)
            speed: Animation speed (1=fastest, 255=slowest)
            
        Returns:
            bool: True if command sent successfully
        """
        if isinstance(mode, TrionesMode):
            mode = mode.value
            
        if not (0x25 <= mode <= 0x38 or mode == 0x41):
            raise ValueError(f"Mode must be 0x25-0x38 (built-in animations) or 0x41 (static color), got: {mode}")
        
        if not 1 <= speed <= 255:
            raise ValueError(f"Speed must be 1-255, got: {speed}")
        
        # Official Triones built-in mode command format
        command = bytes([0xBB, mode, speed, 0x44])
        return await self._write_command(command)
    
    async def set_color_hex(self, hex_color: str) -> bool:
        """
        Set color using hex string
        
        Args:
            hex_color: Hex color string (e.g., "#FF0000" or "FF0000")
            
        Returns:
            bool: True if command sent successfully
        """
        # Clean hex string
        hex_color = hex_color.lstrip('#')
        if len(hex_color) != 6:
            raise ValueError(f"Invalid hex color format: {hex_color}")
        
        try:
            red = int(hex_color[0:2], 16)
            green = int(hex_color[2:4], 16)
            blue = int(hex_color[4:6], 16)
            return await self.set_rgb(red, green, blue)
        except ValueError as e:
            raise ValueError(f"Invalid hex color: {hex_color}") from e

    async def set_rgbw(self, red: int, green: int, blue: int, white: int) -> bool:
        """
        Set RGBW color (combines RGB and white channels)
        
        This method tries multiple approaches to set RGBW colors since different
        Triones controllers may have different command formats.
        
        Args:
            red: Red component (0-255)
            green: Green component (0-255)
            blue: Blue component (0-255)
            white: White component (0-255)
            
        Returns:
            bool: True if command(s) sent successfully
        """
        # Validate input
        for val in [red, green, blue, white]:
            if not 0 <= val <= 255:
                raise ValueError(f"RGBW values must be 0-255, got: {red}, {green}, {blue}, {white}")
        
        # This controller doesn't support combined RGBW commands properly
        # (combined commands only activate the white channel and ignore RGB)
        # So we always use separate RGB and White commands for reliable operation
        logger.debug("Using separate RGB + White commands for better compatibility")
        success = True
        
        # Handle the case where both RGB and White are 0 (turn off)
        if red == 0 and green == 0 and blue == 0 and white == 0:
            off_command = bytes([0x56, 0x00, 0x00, 0x00, 0x00, 0xF0, 0xAA])
            logger.debug(f"Sending OFF command: {off_command.hex()}")
            return await self._write_command(off_command)
        
        # Send RGB command first if we have RGB values
        if red > 0 or green > 0 or blue > 0:
            rgb_command = bytes([0x56, red, green, blue, 0x00, 0xF0, 0xAA])
            logger.debug(f"Sending RGB command: {rgb_command.hex()}")
            if not await self._write_command(rgb_command):
                success = False
                
            # Small delay after RGB command
            await asyncio.sleep(0.1)
        
        # Send white command if we have white value
        if white > 0:
            white_command = bytes([0x56, 0x00, 0x00, 0x00, white, 0x0F, 0xAA])
            logger.debug(f"Sending White command: {white_command.hex()}")
            if not await self._write_command(white_command):
                success = False
        
        return success

    def _kelvin_to_rgb(self, temperature: int) -> Tuple[int, int, int]:
        """
        Convert color temperature in Kelvin to RGB values
        Based on Tanner Helland's algorithm: https://tannerhelland.com/2012/09/18/convert-temperature-rgb-algorithm.html
        
        Args:
            temperature: Color temperature in Kelvin (1000-40000)
            
        Returns:
            Tuple[int, int, int]: RGB values (0-255)
        """
        # Clamp temperature to valid range
        temperature = max(1000, min(40000, temperature))
        
        # Convert to temperature / 100 for calculations
        temp = temperature / 100.0
        
        # Calculate red
        if temp <= 66:
            red = 255
        else:
            red = temp - 60
            red = 329.698727446 * (red ** -0.1332047592)
            red = max(0, min(255, red))
        
        # Calculate green
        if temp <= 66:
            green = temp
            green = 99.4708025861 * math.log(green) - 161.1195681661
        else:
            green = temp - 60
            green = 288.1221695283 * (green ** -0.0755148492)
        green = max(0, min(255, green))
        
        # Calculate blue
        if temp >= 66:
            blue = 255
        elif temp <= 19:
            blue = 0
        else:
            blue = temp - 10
            blue = 138.5177312231 * math.log(blue) - 305.0447927307
            blue = max(0, min(255, blue))
        
        return (int(red), int(green), int(blue))

    async def set_temperature(self, temperature: int, brightness: float = 1.0, use_white_leds: bool = True) -> bool:
        """
        Set color temperature using RGB LEDs and optionally white LEDs for accurate color reproduction
        
        Args:
            temperature: Color temperature in Kelvin (1000-40000)
                        Common values:
                        - 1000K: Deep warm amber
                        - 2000K: Candlelight
                        - 2700K: Warm white (incandescent)
                        - 3000K: Warm white (halogen)
                        - 4000K: Cool white
                        - 5000K: Daylight
                        - 6500K: Cool daylight
                        - 10000K: Blue sky
            brightness: Overall brightness multiplier (0.0-1.0)
            use_white_leds: If True, use white LEDs for neutral/cool temps. If False, use RGB only.
            
        Returns:
            bool: True if command sent successfully
        """
        if not 1000 <= temperature <= 40000:
            raise ValueError(f"Temperature must be 1000-40000K, got: {temperature}")
        
        if not 0.0 <= brightness <= 1.0:
            raise ValueError(f"Brightness must be 0.0-1.0, got: {brightness}")
        
        # Get RGB values for the temperature
        rgb_r, rgb_g, rgb_b = self._kelvin_to_rgb(temperature)
        
        # Decide whether to use RGB or White LEDs based on temperature and hardware limitations
        # Since this controller can't use RGB+White simultaneously, we choose the best option
        
        if use_white_leds and temperature >= 4000:
            # For neutral and cool temperatures, white LEDs are more efficient and accurate
            # Use white LEDs with slight RGB tint if needed
            
            # Calculate how "white" this temperature is
            rgb_min = min(rgb_r, rgb_g, rgb_b)
            rgb_max = max(rgb_r, rgb_g, rgb_b)
            whiteness = rgb_min / rgb_max if rgb_max > 0 else 1.0
            
            if whiteness > 0.8:  # Very white/neutral color
                # Use pure white LEDs for maximum efficiency
                white_intensity = int(255 * brightness)
                logger.debug(f"Temperature {temperature}K -> Pure White({white_intensity})")
                return await self.set_white(white_intensity)
            else:
                # Use RGB for colors that are less white (more colored)
                final_r = int(rgb_r * brightness)
                final_g = int(rgb_g * brightness) 
                final_b = int(rgb_b * brightness)
                logger.debug(f"Temperature {temperature}K -> RGB({final_r}, {final_g}, {final_b})")
                return await self.set_rgb(final_r, final_g, final_b)
        else:
            # For warm temperatures or when white LEDs disabled, use RGB only
            # Boost brightness slightly to compensate for not using white LEDs
            brightness_boost = min(1.0, brightness * 1.2)
            
            final_r = int(rgb_r * brightness_boost)
            final_g = int(rgb_g * brightness_boost)
            final_b = int(rgb_b * brightness_boost)
            
            # Ensure values don't exceed 255
            final_r = min(255, final_r)
            final_g = min(255, final_g)
            final_b = min(255, final_b)
            
            logger.debug(f"Temperature {temperature}K -> RGB({final_r}, {final_g}, {final_b})")
            return await self.set_rgb(final_r, final_g, final_b)
    
    async def test_white_leds(self, intensity: int = 255) -> bool:
        """
        Test white LEDs directly (debug method)
        
        Args:
            intensity: White LED intensity (0-255)
            
        Returns:
            bool: True if command sent successfully
        """
        logger.info(f"Testing white LEDs at intensity {intensity}")
        return await self.set_rgbw(0, 0, 0, intensity)
    
    async def test_rgbw_formats(self, red: int = 255, green: int = 0, blue: int = 0, white: int = 100) -> bool:
        """
        Test different RGBW command formats to find which one works (debug method)
        
        Args:
            red: Red component (0-255)
            green: Green component (0-255) 
            blue: Blue component (0-255)
            white: White component (0-255)
            
        Returns:
            bool: True if any command sent successfully
        """
        logger.info(f"Testing RGBW formats with R={red}, G={green}, B={blue}, W={white}")
        
        formats_to_try = [
            (bytes([0x56, red, green, blue, white, 0xFF, 0xAA]), "0xFF magic"),
            (bytes([0x56, red, green, blue, white, 0xF0, 0xAA]), "0xF0 magic (RGB-style)"),
            (bytes([0x56, red, green, blue, white, 0x0F, 0xAA]), "0x0F magic (White-style)"),
            (bytes([0x56, red, green, blue, white, 0x00, 0xAA]), "0x00 magic"),
            (bytes([0x56, red, green, blue, white, 0xAA, 0xAA]), "0xAA magic"),
        ]
        
        for command, description in formats_to_try:
            logger.info(f"  Trying {description}: {command.hex()}")
            if await self._write_command(command):
                logger.info(f"  ✅ {description} sent successfully")
                await asyncio.sleep(2)  # Wait to observe effect
            else:
                logger.error(f"  ❌ {description} failed")
        
        return True
    
    def __str__(self) -> str:
        return f"TrionesController({self.name}, {self.address})"
    
    def __repr__(self) -> str:
        return f"TrionesController(name='{self.name}', address='{self.address}', connected={self.is_connected})"

class TrionesScanner:
    """Scanner for discovering Triones controllers"""
    
    @staticmethod
    async def discover(timeout: float = 10.0, device_names: Optional[List[str]] = None) -> List[TrionesController]:
        """
        Discover Triones controllers
        
        Args:
            timeout: Discovery timeout in seconds
            device_names: Specific device names to look for (optional)
            
        Returns:
            List[TrionesController]: Found controllers
        """
        logger.info(f"Scanning for Triones controllers (timeout: {timeout}s)")
        
        devices = await BleakScanner.discover(timeout=timeout)
        controllers = []
        
        for device in devices:
            if device.name:
                # Check if it's a Triones device
                if "triones" in device.name.lower():
                    # If specific device names specified, filter by them
                    if device_names is None or device.name in device_names:
                        controller = TrionesController(device)
                        controllers.append(controller)
                        logger.info(f"Found Triones controller: {device.name} ({device.address})")
        
        logger.info(f"Found {len(controllers)} Triones controller(s)")
        return controllers
    
    @staticmethod
    async def find_by_name(name: str, timeout: float = 10.0) -> Optional[TrionesController]:
        """
        Find a specific controller by name
        
        Args:
            name: Device name to search for
            timeout: Discovery timeout in seconds
            
        Returns:
            TrionesController: Found controller or None
        """
        controllers = await TrionesScanner.discover(timeout=timeout, device_names=[name])
        return controllers[0] if controllers else None
    
    @staticmethod
    async def find_by_address(address: str, timeout: float = 10.0) -> Optional[TrionesController]:
        """
        Find a controller by MAC address
        
        Args:
            address: MAC address to search for
            timeout: Discovery timeout in seconds
            
        Returns:
            TrionesController: Found controller or None
        """
        devices = await BleakScanner.discover(timeout=timeout)
        
        for device in devices:
            if device.address.lower() == address.lower():
                if device.name and "triones" in device.name.lower():
                    return TrionesController(device)
        
        return None

# Convenience functions
async def discover_controllers(timeout: float = 10.0) -> List[TrionesController]:
    """Convenience function to discover all Triones controllers"""
    return await TrionesScanner.discover(timeout=timeout)

async def connect_by_name(name: str, timeout: float = 10.0) -> Optional[TrionesController]:
    """Convenience function to find and connect to a controller by name"""
    controller = await TrionesScanner.find_by_name(name, timeout)
    if controller and await controller.connect():
        return controller
    return None

async def connect_by_address(address: str, timeout: float = 10.0) -> Optional[TrionesController]:
    """Convenience function to find and connect to a controller by address"""
    controller = await TrionesScanner.find_by_address(address, timeout)
    if controller and await controller.connect():
        return controller
    return None