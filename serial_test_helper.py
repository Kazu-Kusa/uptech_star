from repo.uptechStar import SerialHelper


class testHelper(object):
    def __init__(self):
        self.myserial = SerialHelper()
        self.myserial.on_connected_changed(self.myserial_on_connected_changed)

    def write(self, data):
        self.myserial.write(data, True)

    @staticmethod
    def generateCmd(device, cmd, len, data):
        buffer = [0] * (len + 6)
        buffer[0] = 0xF5
        buffer[1] = 0x5F
        buffer[2] = device & 0xFF
        buffer[3] = cmd & 0xFF
        buffer[4] = len & 0xFF
        for i in range(len):
            buffer[5 + i] = data[i]

        check = 0
        for i in range(len + 3):
            check += buffer[i + 2]

        buffer[len + 5] = (~check) & 0xFF
        return buffer, len + 6

    def setServoPosition(self, angel):
        data = [0] * 2
        data[0] = angel & 0xFF
        data[1] = (angel >> 8) & 0xFF
        buffer, len = self.generateCmd(0x55, 0x03, 0x02, data)
        self.myserial.write(data)

    def myserial_on_connected_changed(self, is_connected):
        if is_connected:
            print("Connected")
            self.myserial.connect()
            self.myserial.on_data_received(self.myserial_on_data_received)
        else:
            print("DisConnected")

    @staticmethod
    def myserial_on_data_received(data):
        print(data)
