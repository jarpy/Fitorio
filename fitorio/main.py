
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
from bleak import BleakScanner, BleakClient

async def connect_to_device(device_address):
    # Connect to the Polar H10 using its Bluetooth address
    async with BleakClient(device_address) as client:
        print(f"Connected to {device_address}")

        # Read the heart rate measurements characteristic
        # Register for notifications when a new heart rate measurement is received
        await client.start_notify(HEART_RATE_MEASUREMENT_CHAR_UUID, heart_rate_notification_handler)
        
        # Wait for a few notifications to be received
        await asyncio.sleep(10)  # adjust time as needed to receive heart rate updates

        # Stop notifications after receiving some data
        await client.stop_notify(HEART_RATE_MEASUREMENT_CHAR_UUID)
        print("Stopped receiving heart rate notifications.")

async def heart_rate_notification_handler(characteristic, data: bytearray):
    # The heart rate measurement is sent as a byte array
    # The first byte contains the flags, and the second byte contains the heart rate value

    # Polar H10 sends heart rate data in the following format:
    # - If flags byte has bit 0 set, the heart rate value is a 16-bit integer
    # - If bit 1 is set, it also includes energy expended (though we will ignore it for now)
    
    flags = data[0]
    heart_rate_value = None

    # Check if the heart rate is 16-bit or 8-bit
    if flags & 0x01:
        # 16-bit heart rate (2 bytes)
        heart_rate_value = struct.unpack('<H', data[1:3])[0]
    else:
        # 8-bit heart rate (1 byte)
        heart_rate_value = data[1]

    print(f"Heart Rate: {heart_rate_value} BPM")



async def main():
    # device = await BleakScanner.find_device_by_address("A0:9E:1A:DF:24:31")
    # props = (BleakScanner.discovered_devices_and_advertisement_data)
    # print(props.keys())
    # print(device)


    stop_event = asyncio.Event()

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
                        # await client.stop_notify(char.uuid)
                        # print("Stopped receiving heart rate notifications.")
        # Read a characteristic, etc.

    # TODO: add something that calls stop_event.set()

    # def callback(device, advertising_data):
    #     # TODO: do something with incoming data
    #     # print(device, advertising_data)
    #     if device and device.name and "Polar H10" in device.name:
    #         print(f"Found Polar H10 HRM: {device.name} ({device.address})")
    #         BleakClient.create_client(device.address, connect_to_device(device.address))

    #     # A0:9E:1A:DF:24:31: Polar H10 DF243120 AdvertisementData(local_name='Polar H10 DF243120', manufacturer_data={107: b'?\x00\x00R'}, service_uuids=['0000180d-0000-1000-8000-00805f9b34fb', '0000feee-0000-1000-8000-00805f9b34fb'], tx_power=4, rssi=-62)

    # async with BleakScanner(callback) as scanner:
    #     ...
    #     # Important! Wait for an event to trigger stop, otherwise scanner
    #     # will stop immediately.
    #     await stop_event.wait()

    # scanner stops when block exits



# f = factorio_rcon.RCONClient("localhost", 27015, "fakepotato")


def render_set_temperature(temperature: int) -> str:
    return "/c game.players[1].surface.find_entities_filtered{type='reactor'}[1].temperature = %s" % temperature

if __name__ == "__main__":
    asyncio.run(main())
    # f.send_command(render_set_temperature(0))
