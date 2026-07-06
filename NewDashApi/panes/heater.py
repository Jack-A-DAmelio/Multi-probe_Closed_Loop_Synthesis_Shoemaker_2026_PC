class HeaterPane(Pane):

    NAME = "heater"

    def build(self):

        self.temperature = NumberInput(
            label="temperature",
            default=25,
            source="http://localhost:5000/api/heater/temperature"
        )

        self.power = NumberInput(
            label="power",
            default=0,
            source="http://localhost:5000/api/heater/power"
        )