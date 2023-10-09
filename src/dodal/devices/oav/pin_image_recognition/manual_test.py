"""
Note: this file exists exclusively to make it easier to manually run
image recognition on a beamline without setting up all of the
bluesky infrastructure.

It is otherwise unused.
"""
import asyncio

from dodal.devices.oav.pin_image_recognition import PinTipDetection

if __name__ == "__main__":
    x = PinTipDetection(prefix="BL03I-DI-OAV-01:", name="edgeDetect")

    async def acquire():
        await x.connect()
        img = await x.array_data.read()
        tip = await x.read()
        return img, tip

    img, tip = asyncio.get_event_loop().run_until_complete(
        asyncio.wait_for(acquire(), timeout=10)
    )
    print(tip)
    print("Tip: {}".format(tip["edgeDetect"]["value"]))

    try:
        import matplotlib.pyplot as plt

        plt.imshow(img[""]["value"])
        plt.show()
    except ImportError:
        print("matplotlib not available; cannot show acquired image")
