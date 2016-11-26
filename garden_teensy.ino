#include <dht.h>

dht sensorA;
dht sensorB;

void setup() {
  // put your setup code here, to run once:
  Serial.begin(115200);
}

void loop() {
  digitalWrite(13, HIGH);
  sensorA.read22(2);
  sensorB.read22(3);
  Serial.print(sensorA.temperature, 1);
  Serial.print('\t');
  Serial.print(sensorA.humidity, 1);
  Serial.print('\t');
  Serial.print(sensorB.temperature, 1);
  Serial.print('\t');
  Serial.println(sensorB.humidity, 1);
  digitalWrite(13, LOW);
  
  delay(5000);
}
