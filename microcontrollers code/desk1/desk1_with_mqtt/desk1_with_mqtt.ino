#include <ESP8266WiFi.h>
#include <PubSubClient.h>
#include <Ticker.h>

const char* ssid="IoT net";
const char* password="IoT_123456";
const char* mqttServer="thingsboard.cloud";
const char* token="cf51vwkvj6rc7e64hhu7"; // desk1 token

// pins
#define PIR_PIN D1
#define BUZZER_PIN D2
#define LED_PIN D3

volatile bool deskOccupied=false;
volatile unsigned long long lastMotionTime=0;
const unsigned long TIMEOUT=1*60*1000;
const int maxTries=1000;

// timer
Ticker timer;

// WiFi
WiFiClient espClient;
PubSubClient client(espClient);

// interrupt handler for PIR sensor
void ICACHE_RAM_ATTR handlePIR(){
  if(deskOccupied){
  lastMotionTime=millis();
  }
}


void setup() {
  Serial.begin(115200);

  pinMode(PIR_PIN,INPUT);
  pinMode(BUZZER_PIN,OUTPUT);
  pinMode(LED_PIN,OUTPUT);

  attachInterrupt(digitalPinToInterrupt(PIR_PIN),handlePIR,RISING);

  timer.attach_ms(60000,handleTimeout);

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
  client.setCallback(callback);
  reconnectMQTT();

}

void loop() {
  if(!client.connected()){
    reconnectMQTT();
  }
  client.loop();

  delay(100);

}

void handleTimeout(){
  if(deskOccupied && (millis()-lastMotionTime>TIMEOUT)){
    for(int i=0;i<3;i++){
      digitalWrite(BUZZER_PIN,HIGH);
      digitalWrite(LED_PIN,HIGH);
      delay(500);
      digitalWrite(BUZZER_PIN,LOW);
      digitalWrite(LED_PIN,LOW);
      delay(500);
    }
    client.publish("v1/devices/me/telemetry","{\"timer\":\"timeout\"}");
  }
}

void reconnectMQTT(){
  while(!client.connected()){
    if(client.connect("desk1",token,NULL)){
      client.subscribe("v1/devices/me/rpc/request/+");
    }
    else{
      delay(5000);
    }
  }
}

void callback(char*topic,byte* payload,unsigned int length){
  String message="";
  for(int i=0;i<length;i++){
    message+=(char)payload[i];
  }

  if(message.indexOf("\"method\":\"reserve\"")!=-1){
    deskOccupied=true;
    digitalWrite(LED_PIN,HIGH);
    delay(500);
    digitalWrite(LED_PIN,LOW);

    lastMotionTime=millis();
  }
  else if(message.indexOf("\"method\":\"release\"")!=-1){
    deskOccupied=false;
    digitalWrite(LED_PIN,HIGH);
    delay(500);
    digitalWrite(LED_PIN,LOW);

    lastMotionTime=0;
  }
  else if(message.indexOf("\"method\":\"sound_alert\"")!=-1){
    digitalWrite(BUZZER_PIN,HIGH);
    digitalWrite(LED_PIN,HIGH);
    delay(500);
    digitalWrite(BUZZER_PIN,LOW);
    digitalWrite(LED_PIN,LOW);
    delay(500);

  }
}