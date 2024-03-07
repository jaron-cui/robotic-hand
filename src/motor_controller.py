import time

MAX_MOTOR_VELOCITY_RPS = 4.0


# TODO: REPLACE ... WITH THE PROPER TYPE FOR STEPPER MOTOR HARDWARE INTERFACE
def get_motor_connection(port_name: str) -> ...:
    """Retrieves a hardware connection to a stepper motor.

    :param port_name: The name of the port
    :raises Exception: If unable to connect to the motor
    """
    # TODO: IMPLEMENT THIS!
    pass


class MotorController:
    def __init__(self, port_name: str, clockwise: bool, max_revolutions: float, current_revolutions: float = 0):
        """Creates a controller for a motor that can spin within a limited range.

        :param port_name: The name of the port used to access the motor
        :param clockwise: Whether 'increasing' revolutions is clockwise or counter-clockwise
        :param max_revolutions: The maximum number of revolutions allowed from the base position
        :param current_revolutions: The current number of revolutions from the base position
        """
        self.max_revolutions = max_revolutions
        self.current_revolutions = current_revolutions
        self.hardware_connection = get_motor_connection(port_name)

    def start_moving_to(self, goal: float, velocity: float = 1.0) -> None:
        """Starts a nonblocking process to rotate the motor to a particular position
           with a specified velocity.
        :param goal: A value in the range [0.0, 1.0], where 0.0 represents the base position
                    and 1.0 represents the maximum revolutions allowed from the base position,
                    to which the motion will proceed before stopping
        :param velocity: The rate of revolution in revolutions per second
        :raises ValueError: If :goal: is not in the range [0.0, 1.0] or :velocity: is invalid
        """
        if not 0.0 <= goal <= 1.0:
            raise ValueError(f'Specified goal {goal} is not in the range [0.0, 1.0]')
        if not 0.0 < velocity <= MAX_MOTOR_VELOCITY_RPS:
            raise ValueError(f'Specified velocity {velocity} is not in the range (0.0, {MAX_MOTOR_VELOCITY_RPS}]')
        # stop the motor is it is currently moving, and then override it with the new goal
        self.stop_motion()
        # TODO: Start a cancelable thread or something that makes the
        #       motor move at the specified velocity until the goal is reached

    def wait_until_stopped(self):
        """Block until the motor stops moving"""
        # TODO: Implement this function that blocks until the motor is done moving

    def stop_motion(self) -> None:
        """Stops the motor and cancels the current motion"""
        # TODO: If the motor is current in motion, stop it

    def close(self) -> None:
        """Cleanup function for when we are done using this motor controller"""
        self.start_moving_to(0)
        # TODO: close the hardware connection and stuff


# run the file to test out the controller
def test():
    controller = MotorController('/usb/port_whatever', True, 10.0)
    time.sleep(2)
    # do ten revolutions
    controller.start_moving_to(1)
    controller.wait_until_stopped()
    # start slowly revolving in the opposite direction towards the base position
    controller.start_moving_to(0, 0.2)
    # speed up after 3 seconds
    time.sleep(3)
    controller.start_moving_to(0, 4)


if __name__ == '__main__':
    test()
