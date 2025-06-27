#include <ESP8266WiFi.h>
#include <PubSubClient.h>
#include <DHT.h>
#include <MQ135.h>


const char* ssid="IoT net";
const char* password="IoT_123456";
const char* mqttServer="mqtt.thingsboard.cloud";
const char* token="fTnQJ8tm6XsM8XNQsZyu"; // environment1 token environment1 includes desk1 & desk2

const int maxTries=1000;


#define SOUND_PIN D1
#define DHT_PIN D2
#define COOLER_LED_PIN D3
#define HEATER_LED_PIN D4
#define MQ135_PIN A0
#define DHT_TYPE DHT22

// temperature & humidity sensor
DHT dht(DHT_PIN,DHT_TYPE);

// air quality sensor
// MQ135 gasSensor = MQ135(MQ135_PIN);

// WiFi
WiFiClient espClient;
PubSubClient client(espClient);


void setup() {
  Serial.begin(115200);

  pinMode(SOUND_PIN,INPUT);
  pinMode(COOLER_LED_PIN,OUTPUT);
  pinMode(HEATER_LED_PIN,OUTPUT);

  dht.begin();


  int tries=0;
  Serial.println("Connecting to ");
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
  }

  client.setServer(mqttServer,1883);
  reconnectMQTT();

}

void loop() {
  if(!client.connected()){
    reconnectMQTT();
  }
  client.loop();


  float temperature=dht.readTemperature();
  float humidity=dht.readHumidity();
  int airQuality=analogRead(MQ135_PIN);
  int soundLevel=digitalRead(SOUND_PIN);

  String payload="{";
  payload+="\"tempreture\":"+String(temperature)+",";
  payload+="\"humidity\":"+String(humidity)+",";
  payload+="\"air_quality\":"+String(airQuality)+",";
  payload+="\"sound_level\":"+String(soundLevel)+",";
  payload+="}";

  client.publish("v1/devices/me/telemetry",payload.c_str());

  delay(5000);
}



void reconnectMQTT(){
  while(!client.connected()){
    if(client.connect("environment1",token,NULL)){
      client.subscribe("v1/devices/me/rpc/request/+");
    }
    else{
      delay(5000);
    }
  }
}
