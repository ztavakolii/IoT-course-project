# IoT-course-project
## Smart study hall management
 In this project, using the Internet of Things, things such as measuring the actual presence of people and not occupying the study table without using it, measuring the silence level of the study hall and warning people if they do not observe silence, monitoring environmental conditions and taking necessary measures are carried out automatically, and students are encouraged to observe order and use the study space effectively through interactive methods.
### Electronic devices used
• Three ESP8266 microcontrollers

• Two HC-SR501 motion sensors

• One MQ-135 air quality control sensor

• One DHT22 temperature and humidity sensor

• One FC-04 sound sensor

• Two buzzers

• Some LED bulbs

• Some resistors

• Three breadboards and jumper wires

### How to close the circuits
In this project, we have used a motion sensor for each study table, a buzzer and LED for notifications, and a microcontroller to send and receive data to the server.
We also have a sound sensor for each table that is close to each other to measure the sound level in that area, a temperature sensor and an air quality control sensor, and a microcontroller to communicate with the server.
The sensors are connected to the microcontrollers using jumper wires, but in real-world implementation, it is better to use sensors with wireless communication capabilities if it is cost-effective.
The microcontrollers communicate with the server via a Wi-Fi module and exchange data.
A potentiometer built into the sensor has been used to calibrate the motion and sound sensors. To calibrate the sound sensor, the potentiometer is adjusted in such a way that the LED on the sensor turns off when there is silence and turns on when there is sound. To calibrate the motion sensor, the potentiometers are set to set the motion detection range (for example, motion detection within a radius of 3 meters from the sensor), and the duration of the corresponding pin being high when motion is detected. In this project, the detection radius and the duration of the sensor pin being high are each set to their minimum limits, i.e. 3 meters and 2.5 seconds. Also, to calibrate the air quality control sensor, given that we have used the sensor's analog output pin, the appropriate code has been used. (Calibrating using a potentiometer affects the sensor's digital output, not its analog output.)

![image](https://github.com/user-attachments/assets/163861f0-6abb-45c9-8f21-0a53369c1785)

Closed-circuit image for each area of ​​the desks to monitor environmental variables

![image](https://github.com/user-attachments/assets/c8b006de-5c9e-41a1-885b-25584ec2c752)

Closed circuit image for each study table

Note: The cover on the motion sensor in the closed circuit for the tables has been removed for better motion detection.

In the above circuits, the 3.3V pin of the microcontroller is used to power the LEDs and buzzers, and the Vin pin is used to power the sensors to provide the appropriate voltage to start the sensors.

### Explanation of microcontroller codes related to study tables
The microcontroller codes in this project are written in two ways: using the HTTP protocol and using the MQTT protocol to communicate with the server. The codes are also written in the Arduino environment.
The logic of this microcontroller program is that when a table is reserved by a user, the microcontroller is responsible for sounding the buzzer to warn the user if no movement is detected from the user for 20 minutes, and turning on the LED of the table and reporting this situation to the server to display an appropriate message for handing over the table and picking up the items for the user on the site. The buzzer sound level is low to maintain the silence of the hall and it sounds for a short time, but it is better to use more appropriate methods for warning. Also, if there is noise in an area, the microcontroller receives a command from the server to sound the buzzer and turn on the LED to warn the user.
#### HTTP method: 
First, to prevent stackoverflow, an attempt has been made to define variables globally. The deskOccupied variable determines whether the desk is reserved by someone on the site. The lastMotionTime variable stores the time of the user's last movement so that if 20 minutes have passed since that situation, it can be reported to the server. The TIMEOUT variable stores the same 20 minutes in milliseconds. Of course, in the program testing phase, this time is considered to be 1 minute. For the timer, the Ticker.h library software timer has been used, which checks the time that has passed since the last movement every minute and, if there is no movement, sets a logical variable to true so that the necessary actions can be taken in the loop function. Also, the motion sensor creates an interrupt if it detects movement, and in the interrupt handler function, a logical variable becomes true so that the necessary actions can be taken in the loop function, such as changing the lastMotionTime variable. In the above scenario, the microcontroller acts as a client when sending the no-motion status to the server and as a server when receiving the server commands to sound the buzzer and alert. The main server is connected to it and sends the commands. To send the no-motion status, the microcontroller makes an HTTP POST request to the desired URL, i.e. http://192.168.75.224:5000/sensor-data, where the IP address is replaced with the server IP or its domain name. Also, if the server reserves or releases a desk on the site, the server program makes an HTTP POST request to the addresses http://microcontroller IP address/reserve and http://microcontroller IP address/release so that the microcontroller changes the value of the deskOccupied variable. To send the alert command to the microcontroller, the server requests the address http://microcontroller IP address/sound_alert.
In the microcontroller setup function, tasks such as setting up a serial connection with the computer, connecting to Wi-Fi, starting the server, configuring pins and interrupts are done.
#### MQTT method: 
In this method, first a Device is created in the ThingsBoard Cloud section like any microcontroller and server, and its token is used in the code to communicate with the MQTT Server. In the codes of this section, all components such as the setup and loop functions are almost the same as in the previous section, with the difference that in the setup function, the microcontroller tries to connect to the MQTT Server using the client.connect function and the token it has obtained from the ThingsBoard site, and subscribes to topics such as v1/devices/me/rpc/request/+ using the client.subscribe function. In the topic mentioned and the topics that follow, the me section is replaced with the device token. The microcontroller subscribes to this topic to receive server commands, and in fact, the server publishes commands in these topics. Whenever the server publishes something in these topics, the microcontroller callback function is executed and appropriate actions are taken. Also, the microcontroller publishes the inactivity using the client.publish function in the v1/devices/me/telemetry topic as a json document as {"timer":"timeout"} and the server has already subscribed to these topics and this data transfer between the microcontrollers and the server is done by the MQTT Server.

### Explanation of microcontroller codes related to monitoring environmental variables in an area
The logic of this microcontroller program is that it monitors environmental variables such as temperature and humidity or air quality using sensors and takes necessary actions such as turning on the cooler if the reading room environment is hot or turning on the heater if the environment is cold and reports the status to the server if needed. In this project, we have used a green LED as the cooler and a red LED as the heater, which are turned on if the temperature is more than 25 degrees and less than 15 degrees Celsius, respectively. Another task of the microcontroller is to report it to the server if the sound sensor detects noise so that the server can warn users.

#### HTTP method: 
Initially, an attempt has been made to define most of the program variables globally to prevent stackoverflow. To use the temperature and humidity sensors and air quality control, the DHT.h and MQ135.h libraries and objects of the DHT and MQ135 classes have been used, respectively. The MQ135 library includes codes for calibrating the air quality control sensor. Then, in the setup function, tasks such as setting up a serial connection with the computer, connecting to Wi-Fi, configuring pins and sensors, and interrupts have been performed. In the loop function, the values ​​of the temperature and air quality control sensors are checked and necessary actions such as turning on the cooler and heater are performed. In addition, if the sound sensor detects a sound, it generates a pulse with a falling edge and creates an interrupt. In the interrupt handler function, the soundDetected variable is set to true, and if this variable is true, the status report is made to the server by sending an HTTP POST request to http://192.168.75.224:5000/sensor-data in the loop function.

#### MQTT method: 
This method is exactly the same as the MQTT method in table microcontrollers in terms of publishing or subscribing to topics. Other things are like the HTTP codes explained above.

### Explanation of how to calibrate the MQ-135 sensor
To calibrate the MQ135 sensor, first turn on the sensor for about 24 hours in clean air at a temperature of about 20 degrees Celsius and obtain the resistance of the MQ135 sensor, which is Rzero, through the getRZero() function. Then, in the MQ135.h file, change the RZERO value based on the obtained data.


### Explanation of the database code
In the models.py file, the database models are defined using SQLAlchemy. Each of these models represents a table in the database. The User model stores user information, including student number, hashed password, full name, score, and registration time. The Zone model represents different zones in the study hall that can be connected to temperature, sound, and pollution sensors. The Desk model associates study desks with zones and stores information such as the desk status, connected sensor, last presence time, and description of the desk. The Session model records user attendance sessions, including start and end times, QR scan status, associated alerts, and score. The Alert model records alerts such as noise pollution or absence, and is associated with the desk, session, or zone. Finally, the Device model records information about all devices and sensors, including type, status, location, and last message. In the setup.py file, using these models, initial data such as general sensors, area A, two tables, and their associated motion sensors are added to the database.

### Description app.py
This section is implemented using the Flask framework in Python. This server acts as an interface between users, microcontrollers, and the database.

#### 1. Main components of the application:

• Flask: A framework for building server-side APIs.

• SQLAlchemy: For interacting with the database (here sqlite).

• CORS: Enable communication between the server and the client on the local network or browser.

• requests: For sending HTTP requests to the microcontrollers.

• Qr_code_reader: For reading QR codes from files or images.

• models: Contains database models

#### 2. API Routes:

#### @app.route('/')

Show the main page

#### @app.route('/register', methods=['POST'])

Register new users by receiving student number and password.

#### @app.route('/login', methods=['POST'])

Users login by checking password (with hashed password in database).

#### @app.route('/checkin_qr', methods=['POST'])

Login process via QR code:

• User uploads or scans a QR.

• By reading the QR, desk_id and zone are obtained.

• If a desk is found, a Session is created, the desk status is changed to "occupied" and an HTTP request is sent to the IP address of the microcontroller of that desk (/reserve).

#### @app.route('/checkout', methods=['POST'])

User check out of a desk:

• End the session and release the desk.

• Give the user privileges.

• Send a release request to the desk microcontroller.

#### @app.route('/sensor-data', methods=['POST'])

Getting information from microcontrollers:

1. If type is "motion", meaning the user left the desk without officially logging out:

• The session is closed.

• The user is penalized.

• The desk is released.

• An HTTP /release request is sent to the desk microcontroller.

• An alert is recorded in the database.

2. If type is "sound":

• All active desks are checked.

• Users are penalized and sound_alert is given to the desks.

3. If temperature and ppm are sent:

• The environmental status is stored in the desk comment section.

#### @app.route('/desk-data')

Getting information about the desk reserved for the current user.


### MQTT method:
First, an MQTT client is created using the paho.mqtt.client library, which connects to the specified broker (mqtt.thingsboard.cloud) and the standard port 1883.
ACCESS_TOKEN is set on this connection for authentication. When the connection is successfully established (on_connect function), the server subscribes to the global topic v1/devices/+/telemetry, which contains sensor data from all devices.
When a new message is received via MQTT (on_message function), its payload is converted to JSON and different actions are taken depending on the data type (which is in type). For example, if the message type is "motion", it means that the user left the table without registering an official exit; in this case, the user's session is closed, the user's points are reduced, the table is freed, and the corresponding alert is recorded in the database. If the message type is "sound", active tables are penalized and a "loud sound" warning is recorded. Also, if environmental data such as temperature or ppm is sent, it is stored in the table's comment section.
In API routes such as checkin_qr and checkout, the server instructs devices to reserve or release reserved tables by sending messages to the MQTT channels associated with each table.

### Qr_code.py Description
The generate_qr(data, filename) function is used to generate a QR code from a string. This function creates a QRCode object, adds text data to it, and creates an image of the QR and saves it in a file with a desired name.
For example, in the examples, for tables 1 and 2 in area A, two QRs are created with the names A1.png and A2.png.

### Explanation Qr_code_reader.py
The function read_qr(image_path) acts as the main method for reading QR. It first loads the image using OpenCV. If the image is not found or the QR is not recognized in it, an error message is printed and then the helper function read_qr_pillow is used to re-examine the image.
The function read_qr_opencv(image_path) is a simpler method that only uses the QR recognition feature in OpenCV. This function tries to recognize the QR code and extract its content with the help of cv2.QRCodeDetector. If successful, it returns the data, otherwise, a recognition failure message is printed.
The third function, read_qr_pillow(image_path), opens the image using the Pillow library and converts it to RGB format, then tries to decode the QR with the help of pyzbar.decode. This method acts as a fallback solution and is useful in cases where the OpenCV method fails.

### Explanation of Front-End Server Code
The front-end server section is written using HTML, CSS, and JavaScript and has a user interface in Persian. This system provides features such as registration, login, attendance registration via QR scanning, viewing reserved tables, and logging out of the system.
In the <head> section, the Persian font Vazirmatn is loaded via CDN and styles are defined for the body, forms, buttons, tables, and display elements.
The page has a background with an image and a light blue color, and the forms are placed in a box called main-box, which looks beautiful with box-shadow and border-radius. All forms are aligned and fully Persianized.
There are two forms:

#### Login: 
Includes student number and password.

#### Registration: 
Includes student number, full name, password, and password confirmation.

• JavaScript is used to display the appropriate form (with the functions showLogin
, showRegister ).

• If incorrect or empty information is entered, an error message is displayed.

#### Attendance registration with QR Code:

After logging in, the user can register his attendance by scanning the table QR Code or uploading a QR image:

• The html5-qrcode library is used for scanning.

• The QR must contain information such as zone:1;desk:2, which is parsed by the parseQRData function and its accuracy is checked.

• The information is sent to the server to register attendance.

If the user has an active table, the system displays the table information (such as table number and zone) by requesting /desk-data.

• If the table is reserved, the table release (checkout) form is displayed.

• The user can end his attendance by clicking the "Release table" button.


 On page reload (window.onload), a /me request is made to check whether the user is already logged in.

• If logged in, his/her information (name, student number, points) is displayed at the top of the page.

• If he/she has an active desk, the checkout form is displayed; otherwise, the check-in form is displayed.


#### Alerts and messages:

• The system has the ability to display alerts that are taken from the /alerts path and displayed using SweetAlert2.

• These alerts are displayed in a window as a dated list in Persian.


![Screenshot (262)](https://github.com/user-attachments/assets/4b850f40-c112-4537-9353-cbcf7971246e)


![Screenshot (263)](https://github.com/user-attachments/assets/74f67712-04c7-45c6-a3f8-70d3062ccee4)

