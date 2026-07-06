from dashboard_framework.pane import Pane
from dashboard_framework.widgets import NumberInput


class CameraPane(Pane):

    NAME = "camera"

    def build(self):

        self.ip = NumberInput("ip", default="192.168.0.10")
        self.exposure = NumberInput("exposure", default=10)

        self.widgets = [
            self.ip,
            self.exposure
        ]

        self.actions = {
            "send": {
                "label": "Send",
                "endpoint": "/camera",
                "payload": lambda: {
                    "ip": self.ip.value,
                    "exposure": self.exposure.value
                }
            }
        }