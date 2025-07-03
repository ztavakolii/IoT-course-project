#include <ESP8266WiFi.h>
#include <ESP8266HTTPClient.h>
#include <ESP8266WebServer.h>
#include <WiFiClient.h>
#include <Adafruit_Sensor.h>
#include <DHT.h>
#include <MQ135.h> // for mq135 calibration


const char* ssid="IoT net";
const char* password="IoT_123456";

// environment1 token environment1 includes desk1 & desk2

bool soundDetected = false;
int tries=0;
const int maxTries=1000;


String jsonData;
WiFiClient client;
HTTPClient http;
const char* serverURL="http://192.168.75.224:5000/sensor-data";
int httpCode;


#define SOUND_PIN D1
#define DHT_PIN D4
#define COOLER_LED_PIN D5
#define HEATER_LED_PIN D6
#define MQ135_PIN A0
#define DHT_TYPE DHT22

// temperature & humidity sensor
DHT dht(DHT_PIN,DHT_TYPE);

// air quality sensor
MQ135 gasSensor = MQ135(MQ135_PIN);

void ICACHE_RAM_ATTR handleSoundSensorInterrupt(){
  soundDetected=true;
}

void setup() {
  dht.begin();

  Serial.begin(115200);

  pinMode(SOUND_PIN,INPUT);
  pinMode(COOLER_LED_PIN,OUTPUT);
  pinMode(HEATER_LED_PIN,OUTPUT);
  pinMode(DHT_PIN,INPUT_PULLUP);

  digitalWrite(COOLER_LED_PIN,LOW);
  digitalWrite(HEATER_LED_PIN,LOW);

  attachInterrupt(digitalPinToInterrupt(SOUND_PIN), handleSoundSensorInterrupt, FALLING);

  float ro=gasSensor.getRZero();
  Serial.print("basic amount of RZero: ");
  Serial.println(ro);

  
  Serial.print("Connecting to ");
  Serial.println(ssid);
  WiFi.begin(ssid,password);
  while(WiFi.status()!=WL_CONNECTED && tries<maxTries){
    delay(500);
    Serial.print(".");
    tries++;
  }
  if(WiFi.status()!= WL_CONNECTED){
    Serial.println("WiFi disconnected!");
  }
  else{
    Serial.println("WiFi connected.");
    Serial.println(WiFi.localIP());
  }


}

void loop() {

  if(soundDetected){
  // send sound level to server to manage the users' behavior of that environment desks
  Serial.println("Sound detected!");
  if(WiFi.status()==WL_CONNECTED){
        jsonData="{\"desk_id\":\"A\",\"token\":\"ghi789\",\"type\":\"sound\"}";

        http.begin(client,serverURL);
        http.addHeader("Content-Type", "application/json");
        httpCode=http.POST(jsonData);
        if(httpCode>=200 && httpCode<300){
          Serial.print("Sound level status report was successful!\n");
        }
        client.stop();
        http.end();
        
    }
    soundDetected=false;
  }

  float humidity=dht.readHumidity();
  float temperature=dht.readTemperature();
  int airQuality=gasSensor.getPPM();
  //int airQuality=gasSensor.getCorrectedPPM(36, 25);
  //int airQuality=analogRead(A0);
  //float soundLevel=digitalRead(SOUND_PIN);

  Serial.println();
  if(!isnan(temperature)&&!isnan(humidity)){
  Serial.print("Temperature is ");
  Serial.println(temperature);
  Serial.print("Humidity is ");
  Serial.println(humidity);
  }
  Serial.print("Air quality is ");
  Serial.println(airQuality);
  // Serial.print("Sound level is ");
  // Serial.println(soundLevel);


  // Serial.print("dht pin ");
  // Serial.println(digitalRead(DHT_PIN));

// turn on cooler or heater
if(!isnan(temperature)&&!isnan(humidity)){
  if(temperature>25){
    digitalWrite(COOLER_LED_PIN,HIGH);
  }
  else if(temperature<15){
    digitalWrite(HEATER_LED_PIN,HIGH);
  }
}


  delay(2000);
}



