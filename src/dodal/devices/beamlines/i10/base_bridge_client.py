import asyncio
import socket
from functools import partial
from unittest.mock import MagicMock

from ophyd_async.core import Device, DeviceMock
from ophyd_async.core._utils import DEFAULT_TIMEOUT


class BaseBridgeClient(Device):
    def __init__(
        self,
        host: str,
        port: int,
        timeout: float,
        name: str = "",
    ) -> None:
        self.host = host
        self.port = port
        self.timeout = timeout
        self._client: socket.socket | None = None
        self._lock: asyncio.Lock | None = None
        super().__init__(name)

    @property
    def client(self):
        if self._client is not None:
            return self._client
        raise ConnectionError("client not connected.")

    async def connect(
        self,
        mock: bool | DeviceMock = False,
        timeout: float = DEFAULT_TIMEOUT,
        force_reconnect: bool = False,
    ) -> None:

        await super().connect(
            mock=mock, timeout=timeout, force_reconnect=force_reconnect
        )

        if not mock:
            self._client = socket.create_connection(
                (self.host, self.port), timeout=self.timeout
            )

        else:
            mock_socket = MagicMock(spec=socket.socket)
            mock_reader = MagicMock()
            mock_reader.readline.return_value = "1\tmock_ok\n"
            mock_socket.makefile.return_value.__enter__.return_value = mock_reader

            self._client = mock_socket

    def send_payload(self, command: str, *args: str | int | float) -> str:
        payload_parts = [command] + [str(arg) for arg in args]
        payload = "\t".join(payload_parts)

        if not payload.endswith("\n"):
            payload += "\n"
        max_attempts = 2
        for attempt in range(max_attempts):
            try:
                self.client.sendall(payload.encode("utf-8"))

                with self.client.makefile(
                    "r", encoding="utf-8", errors="strict"
                ) as reader:
                    response_line = reader.readline()

                if not response_line:
                    raise ConnectionError(
                        "Server closed connection without returning data."
                    )

                response = response_line.strip()

                if "\t" in response:
                    status, data = response.split("\t", 1)
                else:
                    status, data = response, ""

                if status == "1":
                    return data
                else:
                    raise RuntimeError(f"Server Error: {data}")

            except (ConnectionError, OSError) as e:
                if attempt == max_attempts - 1:
                    raise e
                try:
                    if self._client:
                        try:
                            self._client.close()
                        except Exception:
                            pass
                    self._client = socket.create_connection(
                        (self.host, self.port), timeout=self.timeout
                    )
                    self._client.settimeout(self.timeout)
                except Exception as reconnect_error:
                    raise ConnectionError(
                        f"Reconnect failed during recovery: {reconnect_error}"
                    ) from e
            except Exception as e:
                raise ConnectionError(f"Communication layer failure: {e}") from e
        raise ConnectionError("Communication failed unexpectedly.")

    async def send_payload_async(self, command: str, *args: str | int | float) -> str:
        if self._lock is None:
            self._lock = asyncio.Lock()

        async with self._lock:
            loop = asyncio.get_running_loop()
            _func = partial(self.send_payload, command, *args)
            return await loop.run_in_executor(None, _func)
