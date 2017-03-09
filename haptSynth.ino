#include <Wire.h> //Include arduino Wire Library to enable to I2C
#include "Yurikleb_DRV2667.h"

Yurikleb_DRV2667 drv;

int counter=0;

void setup() {

  Serial.begin(115200);
  while (!Serial) {
    ; // wait for serial port to connect. Needed for native USB port only
  }
  Serial.println("Haptics synthesizer!");

}

void loop() {
  // drv.playWave(WaveForm_3, sizeof(WaveForm_3)); //Play one the Waveforms defined above;
  // delay(3000); //Wait for the wave to play;
}

void serialEvent() {
  while (Serial.available()) {
    // get the new byte:
    byte inByte = Serial.read();
    Serial.print(counter);
    Serial.print(": ");
    //Serial.print((char)inByte);
    if ((int)inByte<16){
      Serial.print("0");
    }
    Serial.println(inByte, HEX);
    waveForm[0][counter]=inByte;
    if (counter>2){
      Serial.println("");
      Serial.println("Playing");
      //Serial.println(waveForm, HEX);
      counter=0;
      drv.playWave(waveForm, 4);
    } else {
      //Serial.println("incriment counter");
      counter++;
    }
  }
}
