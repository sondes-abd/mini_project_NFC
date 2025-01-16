#include <Wire.h>
#include <SPI.h>
#include <Adafruit_PN532.h>

#define PN532_IRQ   (2)
#define PN532_RESET (3)

Adafruit_PN532 nfc(PN532_IRQ, PN532_RESET);

// Allowed UID for the card
String allowedUIDs[] = {
  "93064AFC"  // Your RFID card UID
};

// Person name associated with the UID
String personNames[] = {
  "Sondes Ouledabdallah"
};

int availablePlaces = 10;
unsigned long lastEntryTimes[10] = {0};
String currentUIDs[10] = {""};
int parkedCount = 0;

void setup(void) {
  Serial.begin(115200);
  while (!Serial) delay(10);

  pinMode(12, OUTPUT);  // Green LED
  pinMode(8, OUTPUT);   // Red LED

  nfc.begin();

  uint32_t versiondata = nfc.getFirmwareVersion();
  if (!versiondata) {
    Serial.print("Didn't find PN53x board");
    while (1);
  }

  Serial.println("\nSmart Parking System Ready");
  Serial.print("Stored UID in system: ");
  Serial.println(allowedUIDs[0]);
}

void loop(void) {
  uint8_t success;
  uint8_t uid[] = { 0, 0, 0, 0, 0, 0, 0 };
  uint8_t uidLength;

  success = nfc.readPassiveTargetID(PN532_MIFARE_ISO14443A, uid, &uidLength);

  if (success) {
    String cardUID = "";
    for (uint8_t i = 0; i < uidLength; i++) {
      if (uid[i] < 0x10) cardUID += "0";
      cardUID += String(uid[i], HEX);
    }
    cardUID.toUpperCase();
    
    // Debug print
    Serial.println("\n=== Card Scanned ===");
    Serial.print("Card UID: ");
    Serial.println(cardUID);
    Serial.print("Stored UID: ");
    Serial.println(allowedUIDs[0]);
    
    // Check if the scanned UID matches any allowed UID
    if (isUIDAllowed(cardUID)) {
      String personName = getPersonName(cardUID);
      
      // Check if card is already registered as parked
      int parkedIndex = -1;
      for(int i = 0; i < parkedCount; i++) {
        if(currentUIDs[i] == cardUID) {
          parkedIndex = i;
          break;
        }
      }

      if(parkedIndex == -1) { // Entry
        if(parkedCount < 10 && availablePlaces > 0) {
          currentUIDs[parkedCount] = cardUID;
          lastEntryTimes[parkedCount] = millis();
          parkedCount++;
          availablePlaces--;
          
          Serial.print("ENTRY|");
          Serial.print(cardUID);
          Serial.print("|");
          Serial.print(personName);
          Serial.print("|");
          Serial.print(formatTime(millis()));
          Serial.print("|");
          Serial.print("-");
          Serial.print("|");
          Serial.println(availablePlaces);
          
          digitalWrite(12, HIGH); // Green LED
          delay(1000);
          digitalWrite(12, LOW);
        }
      } else { // Exit
        unsigned long duration = millis() - lastEntryTimes[parkedIndex];
        
        Serial.print("EXIT|");
        Serial.print(cardUID);
        Serial.print("|");
        Serial.print(personName);
        Serial.print("|");
        Serial.print(formatTime(lastEntryTimes[parkedIndex]));
        Serial.print("|");
        Serial.print(formatTime(millis()));
        Serial.print("|");
        Serial.println(availablePlaces + 1);

        for(int i = parkedIndex; i < parkedCount - 1; i++) {
          currentUIDs[i] = currentUIDs[i + 1];
          lastEntryTimes[i] = lastEntryTimes[i + 1];
        }
        parkedCount--;
        availablePlaces++;
        
        digitalWrite(12, HIGH); // Green LED
        delay(1000);
        digitalWrite(12, LOW);
      }
    } else {
      // Access Denied: UID not recognized
      Serial.println("ACCESS DENIED");
      digitalWrite(8, HIGH); // Red LED
      delay(2000);
      digitalWrite(8, LOW);
    }
  }
}

bool isUIDAllowed(String uid) {
  for (int i = 0; i < sizeof(allowedUIDs) / sizeof(allowedUIDs[0]); i++) {
    if (allowedUIDs[i] == uid) {
      return true;
    }
  }
  return false;
}

String formatTime(unsigned long millisTime) {
  unsigned long seconds = millisTime / 1000;
  unsigned long minutes = seconds / 60;
  unsigned long hours = minutes / 60;
  seconds = seconds % 60;
  minutes = minutes % 60;

  String timeString = String(hours) + ":" + 
                     (minutes < 10 ? "0" : "") + String(minutes) + ":" + 
                     (seconds < 10 ? "0" : "") + String(seconds);
  return timeString;
}

String getPersonName(String uid) {
  for (int i = 0; i < sizeof(allowedUIDs) / sizeof(allowedUIDs[0]); i++) {
    if (allowedUIDs[i] == uid) {
      return personNames[i];
    }
  }
  return "Unknown";
}
