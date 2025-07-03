#include <ESP8266WiFi.h>
#include <ESP8266HTTPClient.h>
#include <ESP8266WebServer.h>
#include <WiFiClient.h>
#include <Ticker.h>

const char* ssid="IoT net";
const char* password="IoT_123456";

// pins
#define PIR_PIN D4
#define BUZZER_PIN D2
#define LED_PIN D3

volatile bool deskOccupied=false;
volatile unsigned long lastMotionTime=0;
volatile unsigned long TIMEOUT=1*60*1000;
bool motion_detected=false;
bool timeout_occurs=false;
int motion=0;
int tries=0;
const int maxTries=1000;

WiFiClient client;
HTTPClient http;
const char* serverURL="http://192.168.75.224:5000/sensor-data";
String jsonData;
int httpCode;


// timer
Ticker timer;

// WebServer
ESP8266WebServer server(80);

// interrupt handler for PIR sensor
void ICACHE_RAM_ATTR handlePIR(){
  motion_detected=true;
  
}


void setup() {
  Serial.begin(115200);

  pinMode(PIR_PIN,INPUT);
  pinMode(BUZZER_PIN,OUTPUT);
  pinMode(LED_PIN,OUTPUT);

  digitalWrite(BUZZER_PIN,LOW);
  digitalWrite(LED_PIN,LOW);

  attachInterrupt(digitalPinToInterrupt(PIR_PIN),handlePIR,RISING);

  timer.attach_ms(60000,handleTimeout);


  Serial.print("Connecting to ");
  Serial.println(ssid);
  WiFi.begin(ssid,password);
  while(WiFi.status()!=WL_CONNECTED && tries<maxTries){
    delay(500);
    Serial.print(".");
    tries++;
  }
  if(WiFi.status()!= WL_CONNECTED){
    Serial.print("WiFi disconnected!\n");
  }
  else{
    Serial.print("WiFi connected.\n");
    Serial.println(WiFi.localIP());
  }


  server.on("/reserve",HTTP_POST,handleReserve);
  server.on("/release",HTTP_POST,handleRelease);
  server.on("/sound_alert",HTTP_POST,handleSoundAlert);
  server.begin();
  Serial.println("HTTP server started.");

}

void loop() {
  
  if(motion_detected){
  if(deskOccupied){
  Serial.println("Motion detected!");
  lastMotionTime=millis();
  }
  motion_detected=false;
  }

  if(timeout_occurs){
    if(deskOccupied && (millis()-lastMotionTime>TIMEOUT)){
    for(int i=0;i<3;i++){
      digitalWrite(BUZZER_PIN,HIGH);
      digitalWrite(LED_PIN,HIGH);
      delay(50);
    
      digitalWrite(BUZZER_PIN,LOW);
      digitalWrite(LED_PIN,LOW);
      delay(50);
    }
    Serial.println("Timeout occurs!(User was 20 minutes without motion)");
    

    if(WiFi.status()==WL_CONNECTED){
        jsonData="{\"desk_id\":\"A1\",\"token\":\"abc123\",\"type\":\"motion\"}";
        

        http.begin(client,serverURL);
        http.addHeader("Content-Type", "application/json");
        httpCode=http.POST(jsonData);
        if(httpCode>=200 && httpCode <300){
          Serial.println("Motion status report was successful!");
        }
        client.stop();
        http.end();
    }
  }

  timeout_occurs=false;
  }


  server.handleClient();

  delay(500);
}

void handleTimeout(){
  timeout_occurs=true;
}


void handleReserve(){
  deskOccupied=true;
  digitalWrite(LED_PIN,HIGH);
  digitalWrite(BUZZER_PIN,HIGH);
  delay(100);
  digitalWrite(LED_PIN,LOW);
  digitalWrite(BUZZER_PIN,LOW);


  lastMotionTime=millis();
  Serial.println("The desk is reserved.");
  server.send(200, "text/plain", "OK");
}

void handleRelease(){
  deskOccupied=false;
  digitalWrite(LED_PIN,HIGH);
  digitalWrite(BUZZER_PIN,HIGH);
  delay(100);
  digitalWrite(LED_PIN,LOW);
  digitalWrite(BUZZER_PIN,LOW);


  lastMotionTime=0;
  Serial.println("The desk is released.");

  server.send(200, "text/plain", "OK");
}

void handleSoundAlert(){
  digitalWrite(BUZZER_PIN,HIGH);
  digitalWrite(LED_PIN,HIGH);
  delay(100);
  digitalWrite(BUZZER_PIN,LOW);
  digitalWrite(LED_PIN,LOW);
  //delay(100);
  Serial.println("Sound Alert!");
  server.send(200, "text/plain", "OK");
}


