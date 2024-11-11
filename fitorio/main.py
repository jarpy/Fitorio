
import asyncio
import struct

import factorio_rcon
from bleak import BleakClient

from fitorio.constants import HEART_RATE_MEASUREMENT_CHAR_UUID, HEART_RATE_SERVICE_UUID

factorio = factorio_rcon.RCONClient("localhost", 27015, "fakepotato")

async def heart_rate_notification_handler(_, data: bytearray):
    bpm = data[1]
    rr_sample_count = len(data[2:]) // 2
    rr_intervals = struct.unpack("<" + "H" * rr_sample_count, data[2:])

    print(f"BPM={bpm}", end="\t")
    print(f"RRIs={rr_intervals}")
    print(f"Setting reactor temperature to {bpm * 5}")
    factorio.send_command(render_set_temperature(bpm * 5))
    factorio.send_command("/command helpers.write_file('rt.txt', game.players[1].surface.find_entities_filtered{type='reactor'}[1].temperature, false, 1)")

async def main():
    async with BleakClient("A0:9E:1A:DF:24:31") as client:
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
                        await client.start_notify(char.uuid, heart_rate_notification_handler)
                        await asyncio.Future()  # run forever


def render_set_temperature(temperature: int) -> str:
    return "/silent-command game.players[1].surface.find_entities_filtered{type='reactor'}[1].temperature = %s" % temperature

if __name__ == "__main__":
    asyncio.run(main())
