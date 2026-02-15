#include <Servo.h>

Servo gripperServo;
Servo rotateServo;

void setup() {
  gripperServo.attach(9);
  rotateServo.attach(10);
  gripperServo.write(180);
  rotateServo.write(90);
  Serial.begin(9600);
}

void loop() {
  if (Serial.available()) {
    String command = Serial.readStringUntil('\n');
    command.trim();

    if (command.startsWith("S1:")) {
      int angle = command.substring(3).toInt();
      angle = constrain(angle, 0, 180);
      gripperServo.write(angle);
    } else if (command.startsWith("S2:")) {
      int angle = command.substring(3).toInt();
      angle = constrain(angle, 0, 180);
      rotateServo.write(angle);
    }
  }
}
