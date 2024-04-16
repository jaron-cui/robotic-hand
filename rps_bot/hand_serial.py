import threading
import time
from enum import Enum

import serial as ps


FINGER_RETRACTION_MAX = 1750


class Finger(Enum):
    PINKY = 4
    RING = 3
    MIDDLE = 2
    INDEX = 1


FOUR_FINGERS = [Finger.PINKY, Finger.RING, Finger.MIDDLE, Finger.INDEX]


def read_forever(serial: ps.Serial, lock: threading.Lock):
    while lock.locked():
        print(serial.readline())


class RPSSerial:
    def __init__(self, port: str, eport: str, baudrate=250000):
        self.finger_control = ps.Serial(port, baudrate)
        self.elbow_control = ps.Serial(eport, baudrate)
        self.stop = threading.Lock()
        self.stop.acquire()
        thread = threading.Thread(target=lambda: read_forever(self.elbow_control, self.stop))
        thread.start()
        # self.recalibrate()

    def __set_finger_position(self, finger: Finger, position: int):
        self.finger_control.write(f'{finger.value}|GOAL: {position}\n'.encode('utf-8'))

    def __trigger_movement(self):
        self.finger_control.write(b'STATE: MOVE\n')

    def __zero(self):
        self.finger_control.write(b'ZERO:')
        time.sleep(1)

    def __extend_finger(self, finger: Finger):
        self.__set_finger_position(finger, 0)

    def __retract_finger(self, finger: Finger):
        self.__set_finger_position(finger, FINGER_RETRACTION_MAX)

    def recalibrate(self):
        self.elbow_control.write(b'ZERO:')
        for finger in FOUR_FINGERS:
            self.__set_finger_position(finger, int(FINGER_RETRACTION_MAX * 1.1))
        self.__trigger_movement()
        time.sleep(3)
        self.__zero()
        for finger in FOUR_FINGERS:
            self.__set_finger_position(finger, -FINGER_RETRACTION_MAX)
        self.__trigger_movement()
        time.sleep(3)
        self.__zero()
    
    def recalibrate_elbow(self):
        self.elbow_control.write(b'ZERO:')

    def rock(self):
        for finger in FOUR_FINGERS:
            self.__retract_finger(finger)

        self.__trigger_movement()

    def paper(self):
        for finger in FOUR_FINGERS:
            self.__extend_finger(finger)
        self.__trigger_movement()

    def scissors(self):
        for finger in [Finger.PINKY, Finger.RING]:
            self.__retract_finger(finger)
        for finger in [Finger.MIDDLE, Finger.INDEX]:
            self.__extend_finger(finger)
        self.__trigger_movement()

    def begin_elbow_movement(self, pos):
        TICK_MULT = 2000/360
        pos = int(-pos * TICK_MULT)
        self.elbow_control.write(f'1|GOAL: {pos}\n'.encode('utf'))
        self.elbow_control.write(b'STATE: MOVE\n')

    def read(self, finger):
        self.finger_control.write(b'%s: GET: POS'.format(finger))
        self.finger_control.write(b'%s: GET: SPEED'.format(finger))
        self.finger_control.write(b'%s: GET: GOAL'.format(finger))
        for i in range(3):
            print(self.finger_control.readline() + b'\n')

    def read_all(self):
        self.finger_control.write(b'GET: POS')
        self.finger_control.write(b'GET: SPEED')
        self.finger_control.write(b'GET: GOAL')
        for i in range(12):
            self.read(i)

    def close(self):
        self.paper()
        self.begin_elbow_movement(0)
        time.sleep(3)

        self.stop.release()
        self.finger_control.close()
        self.elbow_control.close()


def main():
    connection = RPSSerial(port='COM3', eport='COM4')
    connection.recalibrate()
    connection.rock()
    connection.begin_elbow_movement(20)
    time.sleep(0.5)
    connection.begin_elbow_movement(0)
    time.sleep(0.5)
    connection.begin_elbow_movement(20)
    time.sleep(0.5)
    connection.begin_elbow_movement(0)
    time.sleep(0.5)
    connection.begin_elbow_movement(20)
    time.sleep(0.5)
    connection.begin_elbow_movement(0)
    time.sleep(0.5)
    connection.begin_elbow_movement(20)
    time.sleep(0.5)
    connection.begin_elbow_movement(0)
    # connection.scissors()
    # time.sleep(3)
    # connection.paper()
    time.sleep(6)
    connection.close()
    time.sleep(3)


if __name__ == '__main__':
    main()
