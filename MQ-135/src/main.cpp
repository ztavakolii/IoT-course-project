#include <Arduino.h>
#include <MQ135.h>
MQ135 gasSensor = MQ135(A0);

void setup() {
  Serial.begin(9600);
}

void loop() {
  float rzero = gasSensor.getRZero();
  Serial.print("RZero = ");
  Serial.println(rzero);
  delay(10000); 
}

