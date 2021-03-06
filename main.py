__author__ = 'Will'

import serial
import os
import time
import struct
from random import randint, randrange

global SERIALPORT
global SERIALPORT2
if os.name == "posix":
    SERIALPORT = "/dev/ttyVirtual1"
    SERIALPORT2 = "/dev/ttyVirtual2"
else:
    SERIALPORT = "COM5"

MSP_IDENT = 100  # out message         multitype + multiwii version + protocol version + capability variable
MSP_STATUS = 101  # out message         cycletime & errors_count & sensor present & box activation & current setting number
MSP_RAW_IMU = 102  # out message         9 DOF
MSP_SERVO = 103  # out message         8 servos
MSP_MOTOR = 104  # out message         8 motors
MSP_RC = 105  # out message         8 rc chan and more
MSP_RAW_GPS = 106  # out message         fix, numsat, lat, lon, alt, speed, ground course
MSP_COMP_GPS = 107  # out message         distance home, direction home
MSP_ATTITUDE = 108  # out message         2 angles 1 heading
MSP_ALTITUDE = 109  # out message         altitude, variometer
MSP_ANALOG = 110  # out message         vbat, powermetersum, rssi if available on RX
MSP_RC_TUNING = 111  # out message         rc rate, rc expo, rollpitch rate, yaw rate, dyn throttle PID
MSP_PID = 112  # out message         P I D coeff (9 are used currently)
MSP_BOX = 113  # out message         BOX setup (number is dependant of your setup)
MSP_MISC = 114  # out message         powermeter trig
MSP_MOTOR_PINS = 115  # out message         which pins are in use for motors & servos, for GUI
MSP_BOXNAMES = 116  # out message         the aux switch names
MSP_PIDNAMES = 117  # out message         the PID names
MSP_WP = 118  # out message         get a WP, WP# is in the payload, returns (WP#, lat, lon, alt, flags) WP#0-home, WP#16-poshold
MSP_BOXIDS = 119  # out message         get the permanent IDs associated to BOXes
MSP_SERVO_CONF = 120  # out message         Servo settings

MSP_SET_RAW_RC = 200  # in message          8 rc chan
MSP_SET_RAW_GPS = 201  # in message          fix, numsat, lat, lon, alt, speed
MSP_SET_PID = 202  # in message          P I D coeff (9 are used currently)
MSP_SET_BOX = 203  # in message          BOX setup (number is dependant of your setup)
MSP_SET_RC_TUNING = 204  # in message          rc rate, rc expo, rollpitch rate, yaw rate, dyn throttle PID
MSP_ACC_CALIBRATION = 205  # in message          no param
MSP_MAG_CALIBRATION = 206  # in message          no param
MSP_SET_MISC = 207  # in message          powermeter trig + 8 free for future use
MSP_RESET_CONF = 208  # in message          no param
MSP_SET_WP = 209  # in message          sets a given WP (WP#,lat, lon, alt, flags)
MSP_SELECT_SETTING = 210  # in message          Select Setting Number (0-2)
MSP_SET_HEAD = 211  # in message          define a new heading hold direction
MSP_SET_SERVO_CONF = 212  # in message          Servo settings
MSP_SET_MOTOR = 214  # in message          PropBalance function

MSP_BIND = 240  # in message          no param

MSP_EEPROM_WRITE = 250  # in message          no param

MSP_DEBUGMSG = 253  # out message         debug string buffer
MSP_DEBUG = 254  # out message         debug1,debug2,debug3,debug4




#############################################################
#
MSP_ESCDATA                 =99
MSP_CONTROLDATAOUT          =98
MSP_CONTROLDATAIN           =97
#
#############################################################


print "main"

def list_serial_ports():
    # Windows
    if os.name == 'nt':
        # Scan for available ports.
        available = []
        for i in range(256):
            try:
                s = serial.Serial(i)
                available.append('COM' + str(i + 1))
                s.close()
            except serial.SerialException:
                pass
        return available
    else:
        # Mac / Linux
        return [port[0] for port in list_ports.comports()]


#print list_serial_ports()

byte_buffer = bytearray()


def serialize8(a):
    global byte_buffer
    if isinstance(a, int):
        a = chr(a)
    byte_buffer += a;
    checksum[0] ^= ord(a);


def serialize16(a):
    serialize8((a   ) & 0xFF);
    serialize8((a >> 8) & 0xFF);


def serialize32(a):
    serialize8((a    ) & 0xFF);
    serialize8((a >> 8) & 0xFF);
    serialize8((a >> 16) & 0xFF);
    serialize8((a >> 24) & 0xFF);

def serializeFloat(a):
    b=struct.pack('<f', a)
    for x in xrange(0,4):
        serialize8(b[x])


checksum = [0, 0, 0, 0]


def headSerialResponse(s, type):
    global byte_buffer
    byte_buffer = bytearray()
    serialize8('$');
    serialize8('M');
    serialize8('>');
    checksum[0] = 0;  # // start calculating a new checksum
    serialize8(s);
    serialize8(type);


def headSerialReply(s, type):
    headSerialResponse(s, type);


def tailSerialReply():
    global byte_buffer
    byte_buffer += chr(checksum[0])


def send_gps(lat=0, lon=0, numsats=5, alt=0, speed=0, fix=1):
    GPS_ground_course = 0
    headSerialReply(16, MSP_RAW_GPS)
    serialize8(fix)
    serialize8(numsats)
    serialize32(lat)
    serialize32(lon)
    serialize16(alt)
    serialize16(speed)
    serialize16(GPS_ground_course)
    tailSerialReply()
    port.write(str(byte_buffer))

def sendControldatain(rpy=[0,0,0],drpy=[0,0,0],position=[0,0,0],velocity=[0,0,0]):
    headSerialReply(48, MSP_CONTROLDATAIN)
    for x in xrange(0,3):
        serializeFloat(rpy[x])
    for x in xrange(0,3):
        serializeFloat(drpy[x])
    for x in xrange(0,3):
        serializeFloat(position[x])
    for x in xrange(0,3):
        serializeFloat(velocity[x])
    tailSerialReply()
    port.write(str(byte_buffer))

def sendControldataout(servo=[0,0],esc=[0,0,0,0]):
    headSerialReply(24, MSP_CONTROLDATAOUT)
    serializeFloat(servo[0])
    serializeFloat(esc[0])
    serializeFloat(esc[1])
    serializeFloat(servo[1])
    serializeFloat(esc[2])
    serializeFloat(esc[3])
    tailSerialReply()
    port.write(str(byte_buffer))

def sendEscdata(rpm=[0,0],current=[0,0],voltage=[0,0]):
    headSerialReply(20, MSP_ESCDATA)
    for x in xrange(0,2):
        serialize16(rpm[x])
        serializeFloat(current[x])
        serializeFloat(voltage[x])
    tailSerialReply()
    port.write(str(byte_buffer))

def send_comp_gps(distance, direction):
    headSerialReply(5, MSP_COMP_GPS);
    serialize16(distance);
    serialize16(direction);
    serialize8(1);
    tailSerialReply()
    port.write(str(byte_buffer))


def send_attitude(x=0, y=0, z=0):
    headSerialReply(6, MSP_ATTITUDE)
    serialize16(x * 10)
    serialize16(y * 10)
    serialize16(z * 10)
    tailSerialReply()
    port.write(str(byte_buffer))


def send_analog(vbat=15, power=0, rssi=0, current=1234):
    headSerialReply(7, MSP_ANALOG)
    serialize8(vbat)
    serialize16(power)
    serialize16(rssi)
    serialize16(current)
    tailSerialReply()
    port.write(str(byte_buffer))


def send_altitude(alt=123, vario=123):
    headSerialReply(6, MSP_ALTITUDE)
    serialize32(alt)
    serialize16(vario)
    tailSerialReply()
    port.write(str(byte_buffer))


def send_status(stable=0, baro=0, mag=0):
    headSerialReply(10, MSP_STATUS)
    serialize16(0)
    serialize16(0)
    serialize16(0)
    serialize32(0)
    tailSerialReply()
    port.write(str(byte_buffer))


def send_debug(debug1, debug2, debug3,debug4):
    headSerialReply(8, MSP_DEBUG)
    serialize16(debug1)
    serialize16(debug2)
    serialize16(debug3)
    serialize16(debug4)
    tailSerialReply()
    port.write(str(byte_buffer))


def send_rc(channels):
    headSerialReply(12 * 2, MSP_RC)
    for i in range(12):
        serialize16(channels[i])
    tailSerialReply()
    port.write(str(byte_buffer))


def send_pid():
    headSerialReply(10 * 3, MSP_PID)
    for i in range(10):
        serialize8(123)
        serialize8(234)
        serialize8(78)
    tailSerialReply()
    port.write(str(byte_buffer))


def send_bicopter_identifier():
    headSerialResponse(7, MSP_IDENT);
    serialize8(32);
    serialize8(4);  # codigo do bicoptero
    serialize8(0);  # not used
    serialize32(0);
    tailSerialReply();
    port.write(str(byte_buffer))

servo = 0
def send_servos(servo_esquerdo,servo_direito):
    headSerialResponse(16, MSP_SERVO);

    serialize16(1500);
    serialize16(1500);
    serialize16(1500);
    serialize16(1500);

    serialize16(servo_esquerdo);
    serialize16(servo_direito);
    serialize16(1500);
    serialize16(1500);

    tailSerialReply();
    port.write(str(byte_buffer))

def send_raw_imu(gyro, acc, mag):
    headSerialResponse(18, MSP_RAW_IMU)
    for i in range(3):
        serialize16(gyro[i])
    for i in range(3):
        serialize16(acc[i])
    for i in range(3):
        serialize16(mag[i])
    tailSerialReply()
    port.write(str(byte_buffer))


def send_motor_pins():
    headSerialResponse(8, MSP_MOTOR_PINS)
    serialize8(1)
    serialize8(2)
    serialize8(0)
    serialize8(0)

    serialize8(0)
    serialize8(0)
    serialize8(0)
    serialize8(0)

    tailSerialReply();
    port.write(str(byte_buffer))

def send_motor(forca_esquerdo,forca_direito):
    headSerialResponse(16, MSP_MOTOR)
    serialize16(forca_esquerdo);
    serialize16(forca_direito);
    serialize16(1300);
    serialize16(1300);

    serialize16(1300);
    serialize16(1300);
    serialize16(1300);
    serialize16(1300);

    tailSerialReply();
    port.write(str(byte_buffer))

#provant_msg
def send_rc_normalize(channels):
    MSP_RCNORMALIZE             =96
    headSerialReply(12 * 2, MSP_RCNORMALIZE)
    for i in range(12):
        serialize16(channels[i])
    tailSerialReply()
    port.write(str(byte_buffer))


port = serial.Serial(SERIALPORT, baudrate=460800, timeout=1)
port2 = serial.Serial(SERIALPORT2, baudrate=460800, timeout=1)
angle = 0
distance = 0
print "connected to port " , port

def waitForRequest():
    time.sleep(0.001)

until100=0
lastSerialAvailable=0
while True:
    if until100>99:
        until100=0
    until100 += 1
    distance += 1
    waitForRequest()
    distance += 1
    send_gps(23 + distance / 100000, 24, speed=distance * 10, alt=distance, fix=1)
    waitForRequest()
    send_comp_gps(distance, (distance % 360) - 180)
    waitForRequest()
    angle += 1
    send_attitude(angle,angle,angle)
    if(angle>180):
        angle=-180
    waitForRequest()
    send_analog(rssi=distance)
    waitForRequest()
    send_altitude(666, 333)
    waitForRequest()
    send_status()
    waitForRequest()
    send_rc([600,700,1000,1700,1500,800,300,400,600,700,100,400,300])
    waitForRequest()
    send_rc_normalize([100-2*until100, 2*until100-100, 100-2*until100, 2*until100-100, until100, 100-until100, until100, 65, 33, 100, 89, 70])         #provant msg
    waitForRequest()
    send_bicopter_identifier()
    waitForRequest()
    send_motor_pins()
    waitForRequest()
    send_motor(12,12)
    waitForRequest()
    send_servos(5,-5)
    waitForRequest()
    send_debug(1,2,3,4)
    waitForRequest()
    send_raw_imu([1,2,3],[4,5,6],[7,8,9])
    waitForRequest()
    sendControldatain(rpy=[1.1,2.2,3.3],drpy=[4.4,5.5,6.6],position=[7.7,8.8,9.9],velocity=[10.10,11.11,12.12])
    waitForRequest()
    sendControldataout(servo=[128,137],esc=[1.1,2.2,3.3,4.4])
    waitForRequest()
    sendEscdata(rpm=[123,321],current=[1.1,2.2],voltage=[3.3,4.4])
    waitForRequest()
    print distance
    while(port2.inWaiting()>1024):
        waitForRequest()

