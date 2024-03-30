// Basic C++ code to control two stepper motors using the AccelStepper library
// Use with PlatformIO
// Ensure that dependencies are installed in the platformio.ini file

#include <Arduino.h>
#include <AccelStepper.h>
#include <string.h>

// Define some steppers and the pins the will use
// AccelStepper stepper1; // Defaults to AccelStepper::FULL4WIRE (4 pins) on 2, 3, 4, 5
AccelStepper stepper1(AccelStepper::FULL4WIRE, 5, 19, 18, 21);
AccelStepper stepper2(AccelStepper::FULL4WIRE, 2, 16, 4, 17);

bool stepper1Running = false;
bool stepper2Running = false;

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
    Header header;
    String data;
};

Command parseCommand(String input)
{
    int colonIndex = input.indexOf(":");
    String header = input.substring(0, colonIndex);
    String data = input.substring(colonIndex + 2);
    Command command;
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
    stepper1.setMaxSpeed(800.0);
    stepper1.setAcceleration(1600.0);

    stepper2.setMaxSpeed(800.0);
    stepper2.setAcceleration(1600.0);
}

void loop()
{
    if (stepper1Running)
        stepper1.run();
    if (stepper2Running)
        stepper2.run();
    if (stepper1.distanceToGo() == 0)
        stepper1Running = false;
    if (stepper2.distanceToGo() == 0)
        stepper2Running = false;
    if (Serial.available() > 0)
    {
        Command cmd = parseCommand(Serial.readStringUntil('\n'));
        switch (cmd.header)
        {
        case SPEED:
            stepper1.setMaxSpeed(cmd.data.toFloat());
            stepper1.setAcceleration(cmd.data.toFloat() * 2);
            stepper2.setMaxSpeed(cmd.data.toFloat());
            stepper2.setAcceleration(cmd.data.toFloat() * 2);
            Serial.println("S1 Speed: " + String(stepper1.maxSpeed()));
            Serial.println("S2 Speed: " + String(stepper2.maxSpeed()));
            break;
        case GOAL:
            stepper1.moveTo(cmd.data.toInt());
            stepper2.moveTo(cmd.data.toInt());
            Serial.println("S1 Goal: " + String(stepper1.targetPosition()));
            Serial.println("S2 Goal: " + String(stepper2.targetPosition()));
            break;
        case STATE:
            if (cmd.data.equals("MOVE"))
            {
                stepper1Running = true;
                stepper2Running = true;
                Serial.println("S1 Running: " + String(stepper1Running));
                Serial.println("S2 Running: " + String(stepper2Running));
            }
            else if (cmd.data.equals("STOP"))
            {
                stepper1.stop();
                stepper2.stop();
                Serial.println("Stopping motors");
            }
            break;
        case ZERO:
            stepper1.stop();
            stepper2.stop();
            stepper1.setCurrentPosition(0);
            stepper2.setCurrentPosition(0);
            Serial.println("S1 Pos: " + String(stepper1.currentPosition()));
            Serial.println("S2 Pos: " + String(stepper2.currentPosition()));
            break;
        case GET:
            if (cmd.data.equals("SPEED"))
            {
                Serial.println("S1 Speed: " + String(stepper1.maxSpeed()));
                Serial.println("S2 Speed: " + String(stepper2.maxSpeed()));
            }
            else if (cmd.data.equals("GOAL"))
            {
                Serial.println("S1 Goal: " + String(stepper1.targetPosition()));
                Serial.println("S2 Goal: " + String(stepper2.targetPosition()));
            }
            else if (cmd.data.equals("STATE"))
            {
                Serial.println("S1 Running: " + String(stepper1Running));
                Serial.println("S2 Running: " + String(stepper2Running));
            }
            else if (cmd.data.equals("POS"))
            {
                Serial.println("S1 Pos: " + String(stepper1.currentPosition()));
                Serial.println("S2 Pos: " + String(stepper2.currentPosition()));
            }
        }
    }
}