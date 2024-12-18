import asyncio
import struct
import sys
from time import time

import factorio_rcon
from bleak import BleakClient, BleakScanner

from fitorio.constants import HEART_RATE_CHARACTERISTIC_UUID, HEART_RATE_SERVICE_UUID
from typing import Final

resting_heart_rate: Final[int] = 85
heart_rate_to_steam_exponent: Final[float] = 2.2
steam_storage_entity_name: Final[str] = "fluid-tank-5x5"
steam_storage_entity_position: Final[tuple[int, int]] = (27, -170)
factorio: factorio_rcon.RCONClient = None
last_update_time = time()


async def connect_to_factorio():
    global factorio
    print("Connecting to Factorio RCON...", end=" ")
    factorio = factorio_rcon.RCONClient("localhost", 27015, "fakepotato")
    print("OK.")


async def process_h10_data(_, data: bytearray):
    global last_update_time
    bpm = data[1]
    now = time()
    elapsed = now - last_update_time
    last_update_time = now

    steam_to_add = (
        max(0, (bpm - resting_heart_rate)) ** heart_rate_to_steam_exponent * elapsed
    )
    print(
        f"Adding {steam_to_add:.1f} steam for {elapsed:.2f} seconds at {bpm} BPM ({steam_to_add*60/elapsed:.0f} steam/min)"
    )
    if steam_to_add > 0:
        factorio.send_command(render_add_steam(steam_to_add))


async def main():
    await connect_to_factorio()
    print("Scanning for devices...")
    devices = await BleakScanner.discover()
    polar_h10_device = None
    for device in [d for d in devices if d.name is not None]:
        print(f"Found device: {device.name} - {device.address}")
        if "Polar H10" in device.name:
            polar_h10_device = device
            break

    if not polar_h10_device:
        print("Polar H10 not found.")
        sys.exit(1)

    async with BleakClient(polar_h10_device.address) as client:
        print(f"Connected: {client.is_connected}")
        services = client.services
        for service in services:
            if service.uuid == HEART_RATE_SERVICE_UUID:
                print(f"Found Heart Rate Service: {service.uuid}")
                characteristics = service.characteristics
                for characteristic in characteristics:
                    uuid = characteristic.uuid
                    print(f" - {uuid}")
                    if uuid == HEART_RATE_CHARACTERISTIC_UUID:
                        print(f"Found Heart Rate Measurement Characteristic: {uuid}")
                        await client.start_notify(uuid, process_h10_data)
                        await asyncio.Future()  # run forever


def render_add_steam(amount: int) -> str:
    command = (
        '/silent-command game.surfaces[1].find_entity("%s", {x=%s, y=%s}).insert_fluid({name="steam", amount=%s, temperature=500})'
        % (steam_storage_entity_name, *steam_storage_entity_position, amount)
    )
    return command


if __name__ == "__main__":
    asyncio.run(main())
