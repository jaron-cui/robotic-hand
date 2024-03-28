# Code for 1 revolution of the motor
'''
from machine import Pin
from time import sleep

IN1 = Pin(5,Pin.OUT)
IN2 = Pin(18,Pin.OUT)
IN3 = Pin(19,Pin.OUT)
IN4 = Pin(21,Pin.OUT)

pins = [IN1, IN2, IN3, IN4]

sequence = [[1,0,0,0],[0,1,0,0],[0,0,1,0],[0,0,0,1]]

for a in range(512):
    for step in sequence:
        for i in range(len(pins)):
            pins[i].value(step[i])
            sleep(0.001)
'''
from machine import Pin
from time import sleep
import asyncio

# Steps per revolution
SPR = 500 #512

C_SEQUENCE = [[1,0,0,0],[0,1,0,0],[0,0,1,0],[0,0,0,1]]
CC_SEQUENCE = [[0,0,0,1],[0,0,1,0],[0,1,0,0],[1,0,0,0]]

class MotorController:
    def __init__(self, pins: tuple, max_revolutions: float, delay: float = 0.001):
        """Creates a controller for a motor that can spin within a limited range.
        
        Parameters:
        - pins: The GPIO pins that the motor is connected to
        - max_revolutions: The maximum number of revolutions allowed from the base position
        - delay: The delay between each step in seconds
        - clockwise: Whether 'increasing' revolutions is clockwise or counter-clockwise
        """
        try:
            IN1 = Pin(pins[0], Pin.OUT)
            IN2 = Pin(pins[1], Pin.OUT)
            IN3 = Pin(pins[2], Pin.OUT)
            IN4 = Pin(pins[3], Pin.OUT)
        except:
            raise Exception(f'Invalid pin configuration: {pins}')
        
        self.pins = (IN1, IN2, IN3, IN4)
        self.max_revolutions = max_revolutions
        self.max_steps = int(SPR * max_revolutions)
        if (delay < 0.001):
            raise ValueError(f'Delay must be at least 0.001, otherwise motor is at risk of stalling')
        self.delay = delay
        self.current_position = 0.0

    def __move_to(self, goal: float, delay: float = 0.001):
        """Move the motor to a specified position
        
        Parameters:
        - goal: A value in the range [0.0, 1.0], where 0.0 represents the base position
                and 1.0 represents the maximum revolutions allowed from the base position,
                to which the motion will proceed before stopping
        - delay: The delay between each step in seconds
        """
        if not 0.0 <= goal <= 1.0:
            raise ValueError(f'Specified goal {goal} is not in the range [0.0, 1.0]')
        if (delay < 0.001):
            raise ValueError(f'Delay must be at least 0.001, otherwise motor is at risk of stalling')
        
        steps = int(abs(self.current_position - goal) * self.max_steps)
        sequence = C_SEQUENCE if goal > self.current_position else CC_SEQUENCE
        #sequence = C_SEQUENCE if self.clockwise else CC_SEQUENCE
        for a in range(steps):
            for step in sequence:
                for i in range(len(self.pins)):
                    self.pins[i].value(step[i])
                    sleep(delay)
        self.current_position = goal

    # Schedule asynchronous movement
    async def move_to(self, goal: float, delay: float = 0.001):
        await self.__move_to(goal, delay)

    def close(self):
        """Cleanup function for when we are done using this motor controller"""
        self.__move_to(0)
        self.pins = None
    