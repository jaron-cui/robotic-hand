import serial as ps

class RPSSerial():
    def __init__(self, port='COM5', baudrate=250000):
        self.ser = ps.Serial(port, baudrate)
        self.recalibrate()



    def recalibrate(self):
        for i in range(4):
            self.ser.write(b'%s: GOAL: 5000'.format(i+1))
        self.ser.write(b'ZERO:')

    def rock(self):
        for i in range(4):
            self.ser.write(b'%s: GOAL: 2000'.format(i+1))

    def paper(self):
        for i in range(4):
            self.ser.write(b'%s: GOAL: 0'.format(i+1))

    def scissors(self):
        for i in range(2, 4):
            self.ser.write(b'%s: GOAL: 2000'.format(i+1))

    def read(self, finger):
        self.ser.write(b'%s: GET: POS'.format(finger))
        self.ser.write(b'%s: GET: SPEED'.format(finger))
        self.ser.write(b'%s: GET: GOAL'.format(finger))
        for i in range(3):
            print(self.ser.readline() + b'\n')

    def read_all(self):
        self.ser.write(b'GET: POS')
        self.ser.write(b'GET: SPEED')
        self.ser.write(b'GET: GOAL')
        for i in range(12):
            self.read(i)

    def close(self):
        self.ser.close()