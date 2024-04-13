#include <Arduino.h>
#include <AccelStepper.h>
#include <string.h>

// Define some steppers and the pins the will use
// AccelStepper stepper1; // Defaults to AccelStepper::FULL4WIRE (4 pins) on 2, 3, 4, 5
AccelStepper stepper1(AccelStepper::FULL4WIRE, 5, 19, 18, 21);
AccelStepper stepper2(AccelStepper::FULL4WIRE, 2, 16, 4, 17);
AccelStepper stepper3(AccelStepper::FULL4WIRE, 13, 14, 12, 27);
AccelStepper stepper4(AccelStepper::FULL4WIRE, 26, 33, 25, 32);
AccelStepper stepper5(AccelStepper::FULL4WIRE, 0, 0, 0, 0);

bool stepper1Running = false;
bool stepper2Running = false;
bool stepper3Running = false;
bool stepper4Running = false;
bool stepper5Running = false;

enum Motor
{
    M1,
    M2,
    M3,
    M4,
    M5,
    ALL
};

enum Header
{
    SPEED,
    GOAL,
    STATE,
    ZERO,
    GET
};

struct Command
{
    int motors[4] = {1, 2, 3, 4};
    Header header;
    String data;
};

bool contains(int *arr, int size, int val)
{
    for (int i = 0; i < size; i++)
    {
        if (arr[i] == val)
        {
            return true;
        }
    }
    return false;
}

Command parseCommand(String input)
{
    int sepIndex = input.indexOf("|");
    int colonIndex = input.indexOf(":");
    String motor = input.substring(0, sepIndex);
    String header = input.substring(sepIndex + 1, colonIndex);
    String data = input.substring(colonIndex + 2);
    Command command;
    if (motor.equals("1"))
    {
        for (int i = 0; i < 4; i++)
        {
            command.motors[i] = 1;
        }
    }
    else if (motor.equals("2"))
    {
        for (int i = 0; i < 4; i++)
        {
            command.motors[i] = 2;
        }
    }
    else if (motor.equals("3"))
    {
        for (int i = 0; i < 4; i++)
        {
            command.motors[i] = 3;
        }
    }
    else if (motor.equals("4"))
    {
        for (int i = 0; i < 4; i++)
        {
            command.motors[i] = 4;
        }
    }
    else if (motor.equals("5"))
    {
        for (int i = 0; i < 4; i++)
        {
            command.motors[i] = 5;
        }
    }
    else
    {
        for (int i = 0; i < 4; i++)
        {
            command.motors[i] = i + 1;
        }
    }

    if (header.equals("SPEED"))
    {
        command.header = SPEED;
    }
    else if (header.equals("GOAL"))
    {
        command.header = GOAL;
    }
    else if (header.equals("STATE"))
    {
        command.header = STATE;
    }
    else if (header.equals("ZERO"))
    {
        command.header = ZERO;
    }
    else if (header.equals("GET"))
    {
        command.header = GET;
    }
    command.data = data;
    return command;
}

void setup()
{
    Serial.begin(250000);
    stepper1.setMaxSpeed(600.0);
    stepper1.setAcceleration(1600.0);

    stepper2.setMaxSpeed(600.0);
    stepper2.setAcceleration(1600.0);

    stepper3.setMaxSpeed(600.0);
    stepper3.setAcceleration(1600.0);

    stepper4.setMaxSpeed(600.0);
    stepper4.setAcceleration(1600.0);
}

void loop()
{
    if (stepper1Running)
        stepper1.run();
    if (stepper2Running)
        stepper2.run();
    if (stepper3Running)
        stepper3.run();
    if (stepper4Running)
        stepper4.run();
    if (stepper1.distanceToGo() == 0)
        stepper1Running = false;
    if (stepper2.distanceToGo() == 0)
        stepper2Running = false;
    if (stepper3.distanceToGo() == 0)
        stepper3Running = false;
    if (stepper4.distanceToGo() == 0)
        stepper4Running = false;
    if (Serial.available() > 0)
    {
        Command cmd = parseCommand(Serial.readStringUntil('\n'));
        switch (cmd.header)
        {
        case SPEED:
            if (contains(cmd.motors, 4, 1))
            {
                stepper1.setMaxSpeed(cmd.data.toFloat());
                stepper1.setAcceleration(cmd.data.toFloat() * 2);
                Serial.println("S1 Speed: " + String(stepper1.maxSpeed()));
            }
            if (contains(cmd.motors, 4, 2))
            {
                stepper2.setMaxSpeed(cmd.data.toFloat());
                stepper2.setAcceleration(cmd.data.toFloat() * 2);
                Serial.println("S2 Speed: " + String(stepper2.maxSpeed()));
            }
            if (contains(cmd.motors, 4, 3))
            {
                stepper3.setMaxSpeed(cmd.data.toFloat());
                stepper3.setAcceleration(cmd.data.toFloat() * 2);
                Serial.println("S3 Speed: " + String(stepper3.maxSpeed()));
            }
            if (contains(cmd.motors, 4, 4))
            {
                stepper4.setMaxSpeed(cmd.data.toFloat());
                stepper4.setAcceleration(cmd.data.toFloat() * 2);
                Serial.println("S4 Speed: " + String(stepper4.maxSpeed()));
            }
            if (contains(cmd.motors, 4, 5))
            {
                stepper5.setMaxSpeed(cmd.data.toFloat());
                stepper5.setAcceleration(cmd.data.toFloat() * 2);
                Serial.println("S5 Speed: " + String(stepper5.maxSpeed()));
            }
            break;
        case GOAL:
            if (contains(cmd.motors, 4, 1))
            {
                stepper1.moveTo(cmd.data.toInt());
                Serial.println("S1 Goal: " + String(stepper1.targetPosition()));
            }
            if (contains(cmd.motors, 4, 2))
            {
                stepper2.moveTo(cmd.data.toInt());
                Serial.println("S2 Goal: " + String(stepper2.targetPosition()));
            }
            if (contains(cmd.motors, 4, 3))
            {
                stepper3.moveTo(cmd.data.toInt());
                Serial.println("S3 Goal: " + String(stepper3.targetPosition()));
            }
            if (contains(cmd.motors, 4, 4))
            {
                stepper4.moveTo(cmd.data.toInt());
                Serial.println("S4 Goal: " + String(stepper4.targetPosition()));
            }
            if (contains(cmd.motors, 4, 5))
            {
                stepper5.moveTo(cmd.data.toInt());
                Serial.println("S5 Goal: " + String(stepper5.targetPosition()));
            }
            break;
        case STATE:
            if (cmd.data.equals("MOVE"))
            {
                if (contains(cmd.motors, 4, 1))
                {
                    stepper1Running = true;
                    Serial.println("S1 Running: " + String(stepper1Running));
                }
                if (contains(cmd.motors, 4, 2))
                {
                    stepper2Running = true;
                    Serial.println("S2 Running: " + String(stepper2Running));
                }
                if (contains(cmd.motors, 4, 3))
                {
                    stepper3Running = true;
                    Serial.println("S3 Running: " + String(stepper3Running));
                }
                if (contains(cmd.motors, 4, 4))
                {
                    stepper4Running = true;
                    Serial.println("S4 Running: " + String(stepper4Running));
                }
                if (contains(cmd.motors, 4, 5))
                {
                    stepper5Running = true;
                    Serial.println("S5 Running: " + String(stepper5Running));
                }
            }
            else if (cmd.data.equals("STOP"))
            {
                if (contains(cmd.motors, 4, 1))
                {
                    stepper1.stop();
                    stepper1Running = false;
                    Serial.println("S1 Running: " + String(stepper1Running));
                }
                if (contains(cmd.motors, 4, 2))
                {
                    stepper2.stop();
                    stepper2Running = false;
                    Serial.println("S2 Running: " + String(stepper2Running));
                }
                if (contains(cmd.motors, 4, 3))
                {
                    stepper3.stop();
                    stepper3Running = false;
                    Serial.println("S3 Running: " + String(stepper3Running));
                }
                if (contains(cmd.motors, 4, 4))
                {
                    stepper4.stop();
                    stepper4Running = false;
                    Serial.println("S4 Running: " + String(stepper4Running));
                }
                if (contains(cmd.motors, 4, 5))
                {
                    stepper5.stop();
                    stepper5Running = false;
                    Serial.println("S5 Running: " + String(stepper5Running));
                }
            }
            break;
        case ZERO:
            stepper1.stop();
            stepper2.stop();
            stepper3.stop();
            stepper4.stop();
            stepper5.stop();
            stepper1.setCurrentPosition(0);
            stepper2.setCurrentPosition(0);
            stepper3.setCurrentPosition(0);
            stepper4.setCurrentPosition(0);
            stepper5.setCurrentPosition(0);
            Serial.println("S1 Pos: " + String(stepper1.currentPosition()));
            Serial.println("S2 Pos: " + String(stepper2.currentPosition()));
            Serial.println("S3 Pos: " + String(stepper3.currentPosition()));
            Serial.println("S4 Pos: " + String(stepper4.currentPosition()));
            Serial.println("S5 Pos: " + String(stepper5.currentPosition()));
            break;
        case GET:
            if (cmd.data.equals("SPEED"))
            {
                if (contains(cmd.motors, 4, 1))
                {
                    Serial.println("S1 Speed: " + String(stepper1.maxSpeed()));
                }
                if (contains(cmd.motors, 4, 2))
                {
                    Serial.println("S2 Speed: " + String(stepper2.maxSpeed()));
                }
                if (contains(cmd.motors, 4, 3))
                {
                    Serial.println("S3 Speed: " + String(stepper3.maxSpeed()));
                }
                if (contains(cmd.motors, 4, 4))
                {
                    Serial.println("S4 Speed: " + String(stepper4.maxSpeed()));
                }
                if (contains(cmd.motors, 4, 5))
                {
                    Serial.println("S5 Speed: " + String(stepper5.maxSpeed()));
                }
            }
            else if (cmd.data.equals("GOAL"))
            {
                if (contains(cmd.motors, 4, 1))
                {
                    Serial.println("S1 Goal: " + String(stepper1.targetPosition()));
                }
                if (contains(cmd.motors, 4, 2))
                {
                    Serial.println("S2 Goal: " + String(stepper2.targetPosition()));
                }
                if (contains(cmd.motors, 4, 3))
                {
                    Serial.println("S3 Goal: " + String(stepper3.targetPosition()));
                }
                if (contains(cmd.motors, 4, 4))
                {
                    Serial.println("S4 Goal: " + String(stepper4.targetPosition()));
                }
                if (contains(cmd.motors, 4, 5))
                {
                    Serial.println("S5 Goal: " + String(stepper5.targetPosition()));
                }
            }
            else if (cmd.data.equals("STATE"))
            {
                if (contains(cmd.motors, 4, 1))
                {
                    Serial.println("S1 Running: " + String(stepper1Running));
                }
                if (contains(cmd.motors, 4, 2))
                {
                    Serial.println("S2 Running: " + String(stepper2Running));
                }
                if (contains(cmd.motors, 4, 3))
                {
                    Serial.println("S3 Running: " + String(stepper3Running));
                }
                if (contains(cmd.motors, 4, 4))
                {
                    Serial.println("S4 Running: " + String(stepper4Running));
                }
                if (contains(cmd.motors, 4, 5))
                {
                    Serial.println("S5 Running: " + String(stepper5Running));
                }
            }
            else if (cmd.data.equals("POS"))
            {
                if (contains(cmd.motors, 4, 1))
                {
                    Serial.println("S1 Pos: " + String(stepper1.currentPosition()));
                }
                if (contains(cmd.motors, 4, 2))
                {
                    Serial.println("S2 Pos: " + String(stepper2.currentPosition()));
                }
                if (contains(cmd.motors, 4, 3))
                {
                    Serial.println("S3 Pos: " + String(stepper3.currentPosition()));
                }
                if (contains(cmd.motors, 4, 4))
                {
                    Serial.println("S4 Pos: " + String(stepper4.currentPosition()));
                }
                if (contains(cmd.motors, 4, 5))
                {
                    Serial.println("S5 Pos: " + String(stepper5.currentPosition()));
                }
            }
        }
    }
}