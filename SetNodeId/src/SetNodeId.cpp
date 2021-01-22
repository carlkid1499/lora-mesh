
#include <Arduino.h>
#include <EEPROM.h>

#define EEPROM_SIZE 1

// change this to be the ID of your node in the mesh network
uint8_t nodeId = 1;

void setup() {
  Serial.begin(115200);
  while (!Serial) ; // Wait for serial port to be available

  Serial.println("setting nodeId...");

  EEPROM.begin(EEPROM_SIZE); // initialize EEPROM with predefined size
  EEPROM.write(0, nodeId);
  EEPROM.commit();
  Serial.print("set nodeId = ");
  Serial.println(nodeId);

  uint8_t readVal = EEPROM.read(0);

  Serial.print("read nodeId: ");
  Serial.println(readVal);

  if (nodeId != readVal) {
    Serial.println("*** FAIL ***");
  } else {
    Serial.println("SUCCESS");
  }
}

void loop() {

}
