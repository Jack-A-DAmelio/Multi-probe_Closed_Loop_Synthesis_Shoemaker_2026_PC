from dashboard_framework.pane import Pane
from dashboard_framework.widgets import (
    Display,
    NumberInput,
    Button, TextInput
)

# TEMP_PROBE_DIRECTORY = {
#     "name": "Main Temperature Probe", THIS IS ONE OF THE ONLY THING ACTIVLY USED IN THE TEMP MODULE

#     # Power wiring information.
#     "power_board_pin": "3V3",
#     "power_physical_pin": 1,
#     "power_sensor_pin": "VIN",

#     # Ground wiring information.
#     "ground_board_pin": "GND",
#     "ground_physical_pin": 6,
#     "ground_sensor_pin": "GND",

#     # SPI clock wiring information.
#     "sck_gpio": 11,
#     "sck_board_pin": "SCLK",
#     "sck_physical_pin": 23,
#     "sck_sensor_pin": "SCK",

#     # SPI data from MAX31856 to Raspberry Pi.
#     "miso_gpio": 9,
#     "miso_board_pin": "MISO",
#     "miso_physical_pin": 21,
#     "miso_sensor_pin": "SDO",

#     # SPI data from Raspberry Pi to MAX31856.
#     "mosi_gpio": 10,
#     "mosi_board_pin": "MOSI",
#     "mosi_physical_pin": 19,
#     "mosi_sensor_pin": "SDI",

#     # Chip-select configuration.
#     "cs_gpio": 5,  THIS IS ONE OF THE ONLY THING ACTIVLY USED IN THE TEMP MODULE
#     "cs_board_pin": "D5",
#     "cs_physical_pin": 29,
#     "cs_sensor_pin": "CS",

#     "thermocouple_type": "K", THIS IS ONE OF THE ONLY THING ACTIVLY USED IN THE TEMP MODULE
#     "read_interval_seconds": 0.5,
# }
class thermocouple_setup(Pane):

    NAME = "thermocouple_setup"

    def build(self):

        # Thermocouple configuration inputs
        self.name = TextInput(
            label="name",
            default= "Main Temperature Probe"
        )
        self.cs_gpio = NumberInput(
                label="cs_gpio", #this is the only thing acitvely used by the module the rest is book keeping
                default=5
            )
        self.thermocouple_type = TextInput(
            label="thermocouple_type",
            default="K"
        )
        # self.operator = TextInput(
        #             label="Operator Name",
        #             default=" ds"
        # )
        self.power = NumberInput(
            label= "Power",
            default=1
        )

        self.ground= NumberInput(
            label="Ground",
            default= 6
        )

        # self.miso= NumberInput(
        #     label="miso",
        #     default= 9
        # )

        # Send configuration to the PC server
        self.send = Button(
            label="Send to PC",
            endpoint="/add_module_to_pc_state?module_name=thermocouple"
        )


        # Live thermocouple temperature
        self.temperature = Display(
            label="Current Temperature",
            source="/api/get_data"
        )