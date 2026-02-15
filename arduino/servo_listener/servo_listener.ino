#include <Servo.h>

Servo gripperServo;
Servo rotateServo;

const int STEP_DELAY_MS = 15;  // milliseconds between each 1-degree step

void slowMove(Servo &servo, int target) {
  int current = servo.read();
  int step = (target > current) ? 1 : -1;
  while (current != target) {
    current += step;
    servo.write(current);
    delay(STEP_DELAY_MS);
  }
}

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
      slowMove(gripperServo, angle);
    } else if (command.startsWith("S2:")) {
      int angle = command.substring(3).toInt();
      angle = constrain(angle, 0, 180);
      slowMove(rotateServo, angle);
    }
  }
}
