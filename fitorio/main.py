
import factorio_rcon
import struct

# Polar H10 UUIDs
HEART_RATE_SERVICE_UUID = "0000180d-0000-1000-8000-00805f9b34fb"  # Heart Rate Service UUID
HEART_RATE_MEASUREMENT_CHAR_UUID = "00002a37-0000-1000-8000-00805f9b34fb"  # Heart Rate Measurement Characteristic UUID
BODY_SENSOR_LOCATION_CHAR_UUID = "00002a38-0000-1000-8000-00805f9b34fb"  # Body Sensor Location Characteristic UUID
MANUFACTURER_NAME_STRING_CHAR_UUID = "00002a29-0000-1000-8000-00805f9b34fb"  # Manufacturer Name String Characteristic UUID
MODEL_NUMBER_STRING_CHAR_UUID = "00002a24-0000-1000-8000-00805f9b34fb"  # Model Number String Characteristic UUID
SERIAL_NUMBER_STRING_CHAR_UUID = "00002a25-0000-1000-8000-00805f9b34fb"  # Serial Number String Characteristic UUID
HARDWARE_REVISION_STRING_CHAR_UUID = "00002a27-0000-1000-8000-00805f9b34fb"  # Hardware Revision String Characteristic UUID
FIRMWARE_REVISION_STRING_CHAR_UUID = "00002a26-0000-1000-8000-00805f9b34fb"  # Firmware Revision String Characteristic UUID
SOFTWARE_REVISION_STRING_CHAR_UUID = "00002a28-0000-1000-8000-00805f9b34fb"  # Software Revision String Characteristic UUID
SYSTEM_ID_CHAR_UUID = "00002a23-0000-1000-8000-00805f9b34fb"  # System ID Characteristic UUID
IEEE_11073_20601_REGULATORY_CERTIFICATION_DATA_LIST_CHAR_UUID = "00002a2a-0000-1000-8000-00805f9b34fb"  # IEEE 11073-20601 Regulatory Certification Data List Characteristic UUID
PnP_ID_CHAR_UUID = "00002a50-0000-1000-8000-00805f9b34fb"  # PnP ID Characteristic UUID



import asyncio
from bleak import BleakClient

factorio = factorio_rcon.RCONClient("localhost", 27015, "fakepotato")

async def heart_rate_notification_handler(characteristic, data: bytearray):
    # The heart rate measurement is sent as a byte array
    # The first byte contains the flags, and the second byte contains the heart rate value

    # Polar H10 sends heart rate data in the following format:
    # - If flags byte has bit 0 set, the heart rate value is a 16-bit integer
    # - If bit 1 is set, it also includes energy expended (though we will ignore it for now)
    flags = data[0]
    heart_rate_value = data[1]
    rr_sample_count = len(data[2:]) // 2

    rr_intervals = struct.unpack("<" + "H" * rr_sample_count, data[2:])
    print(f"BPM={heart_rate_value}", end="\t")
    print(f"RRIs={rr_intervals}")
    print(f"Setting reactor temperature to {heart_rate_value * 5}")
    factorio.send_command(render_set_temperature(heart_rate_value * 5))
    print(factorio.send_command("/command helpers.write_file('rt.txt', game.players[1].surface.find_entities_filtered{type='reactor'}[1].temperature, false, 1)"))

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
