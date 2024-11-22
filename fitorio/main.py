
import asyncio
import struct
import sys
from time import time

import factorio_rcon
from bleak import BleakClient, BleakScanner

from fitorio.constants import HEART_RATE_MEASUREMENT_CHAR_UUID, HEART_RATE_SERVICE_UUID
from typing import Final

resting_heart_rate: Final[int] = 75
heart_rate_to_steam_exponent: Final[float] = 2.2
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
    rr_sample_count = len(data[2:]) // 2
    rr_intervals = struct.unpack("<" + "H" * rr_sample_count, data[2:])

    now = time()
    elapsed = now - last_update_time
    last_update_time = now

    steam_to_add = max(0, (bpm - resting_heart_rate))**heart_rate_to_steam_exponent * elapsed
    print(f"Adding {steam_to_add} steam for {elapsed} seconds at {bpm} BPM")
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
                for char in characteristics:
                    print(f" - {char.uuid}")
                    if char.uuid == HEART_RATE_MEASUREMENT_CHAR_UUID:
                        print(f"Found Heart Rate Measurement Characteristic: {char.uuid}")
                        await client.start_notify(char.uuid, process_h10_data)
                        await asyncio.Future()  # run forever


def render_add_steam(amount: int) -> str:
    command = '/silent-command game.surfaces[1].find_entity("fluid-tank-5x5", {x=27, y=-170}).insert_fluid({name="steam", amount=%s, temperature=500})' % amount
    # print(command)
    return command

if __name__ == "__main__":
    asyncio.run(main())
