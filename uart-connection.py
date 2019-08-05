import serial
import re
import array
import glob
import sys
from serial import Serial
from os import system, name
import getopt
import time
import numpy as np
import matplotlib.pyplot as plt

# import sleep to show output for some time period
from time import sleep



config = {}
config["port"] = 'COM4'
config["baudrate"] = 9600
config["bytesize"] = serial.EIGHTBITS
config["parity"] = serial.PARITY_NONE
config["timeout"] = 2

## frame
# 1 char - 1 remote controle, 0 manual control
# 2 char - 0 reading, 1 writing
# 3 char - 3 different modes of led
# 4 - 6 char - 3 chars of speed  - 128 change of direction

controls = {}
controls_to_send = {}
menu_options = []
menu_options.append(('read_uart', "Read status"))
menu_options.append(('read_continous', "Read status, continous mode"))
menu_options.append(('send_uart', "Send controls", '-'))
menu_options.append(('choose_port', "Choose port"))
menu_options.append(('set_controls', "Set controls"))
menu_options.append(('set_config', "Set config for connection", '-'))
menu_options.append(('read_saved', "Read saved config and controls from file"))
menu_options.append(('save_to_file', "Save controls and config in file", '-'))
menu_options.append(('read_fft_data', "Read fft data", '-'))
menu_options.append(('exit', "Exit"))


def menu():
    clear()
    print("####MENU####")
    for i, j in enumerate(menu_options):
        print(i, ". ", j[1])
        if len(j) > 2:
            print("--------------------------------------")


    x = ''
    while not is_number(x) or int(x) > len(menu_options) or int(x) < 0:
        x = input("Enter number: ")

    return globals()[menu_options[int(x)][0]]()


def serial_ports():
    if sys.platform.startswith('win'):
        ports = ['COM%s' % (i + 1) for i in range(256)]
    elif sys.platform.startswith('linux') or sys.platform.startswith('cygwin'):
        # this excludes your current terminal "/dev/tty"
        ports = glob.glob('/dev/tty[A-Za-z]*')
    elif sys.platform.startswith('darwin'):
        ports = glob.glob('/dev/tty.*')
    else:
        raise EnvironmentError('Unsupported platform')

    result = []
    for port in ports:
        try:
            s = serial.Serial(port)
            s.close()
            result.append(port)
        except (OSError, serial.SerialException):
            pass
    return result


def choose_port():
    avaiable = serial_ports()
    for index, port in enumerate(avaiable):
        print(index, ". ", port)

    x = ''
    while not is_number(x) or int(x) > len(avaiable):
        x = input("Enter number of port: ")
    config["port"] = avaiable[int(x)]
    return menu()


def read_uart():
    ser = serial.Serial(port=config["port"], baudrate=int(config["baudrate"]), bytesize=int(config["bytesize"]),
                        parity=config["parity"], timeout=int(config["timeout"]))

    last_character = ''
    read_buffer = ""
    if ser.isOpen():
        try:
            err = ser.write(str.encode("000000\n"))
            while last_character != '\n':
                last_character = ser.read()
                last_character = last_character.decode('utf-8')
                read_buffer += last_character
        except Exception:
            ser.close()
            print('error')
    else:
        print("Cannot open serial port")

    ser.close()

    if len(read_buffer) > 5:
        controls['Connection_mode'] = read_buffer[0]
        controls['Access_mode'] = read_buffer[1]
        controls['LED_mode'] = read_buffer[2]
        controls['Speed'] = read_buffer[3:6]

    # words = re.split(', |\[|\]| |:|\n', read_buffer)
    # i = 0
    # while i < len(words):
    #     if len(words[i]):
    #         for key, val in controls.items():
    #             if words[i] == key:
    #                 controls[key] = words[i+1]
    #                 i += 1
    #                 break

        # if words[i] == "LED_FREQ":
        #     controls["LED_FREQ"] = words[i+1]
        #     i += 1
        # elif words[i] == "LED_FILL":
        #     controls["LED_FILL"] = words[i+1]
        #     i += 1
        # i += 1
    print_map(controls)
    input("Press enter to go back to menu")
    return menu()


def read_continous():
    ser = serial.Serial(port=config["port"], baudrate=int(config["baudrate"]), bytesize=int(config["bytesize"]),
                        parity=config["parity"], timeout=int(config["timeout"]))
    while 1:
        last_character = ''
        read_buffer = ""
        if ser.isOpen():
            try:
                ser.write(str.encode("000000\n"))
                while last_character != '\n':
                    last_character = ser.read()
                    last_character = last_character.decode('utf-8')
                    read_buffer += last_character
            except Exception:
                ser.close()
                print('error')
        else:
            print("Cannot open serial port")
        if len(read_buffer) > 5:
            controls['Connection_mode'] = read_buffer[0]
            controls['Access_mode'] = read_buffer[1]
            controls['LED_mode'] = read_buffer[2]
            controls['Speed'] = read_buffer[3:6]
        # words = re.split(', |\[|\]| |:|\n', read_buffer)
        # i = 0
        # while i < len(words):
        #     if len(words[i]):
        #         for key, val in controls.items():
        #             if words[i] == key:
        #                 controls[key] = words[i + 1]
        #                 i += 1
        #                 break
        #     i += 1
        clear()
        print_map(controls)
        time.sleep(0.5)  #wait 10 seconds



def set_config_from_string(str_config):
    words = re.split(',|\[|\]| |:|\n', str_config)
    i = 0
    while i < len(words):
        if len(words[i]) > 0:
            for key, val in config.items():
                if words[i] == key:
                    while i + 1 < len(words) and len(words[i+1]) == 0:
                        i += 1
                    config[key] = words[i + 1]
                    i += 1
                    break
        i += 1




def set_controls_from_string(str_controls):
    words = re.split(',|\[|\]| |:|\n', str_controls)
    i = 0
    while i < len(words):
        if len(words[i]) > 0:
            key = words[i]
            while i + 1 < len(words) and len(words[i + 1]) == 0:
                i += 1
            controls[key] = words[i + 1]
            i += 1
        i += 1


def set_config():
    print("Actual config:")
    print_map(config)
    x = input("Enter name and value: ")
    set_config_from_string(x)

    return menu()

def set_controls():
    print("Actual controls:")
    print_map(controls)
    x = input("Enter name and value: ")
    set_controls_from_string(x)

    return menu()


def print_map(dictionary):
    for key, val in dictionary.items():
        print(key, "\t: ", val)


def send_uart(message=""):
    ser = serial.Serial(port=config["port"], baudrate=int(config["baudrate"]), bytesize=int(config["bytesize"]), parity=config["parity"], timeout=int(config["timeout"]))
    if len(message) == 0:
        message = controls['Connection_mode']
        message += controls['Access_mode']
        message += controls['LED_mode']
        message += controls['Speed']
    message += '\n'
    response = ''
    read_data = ''
    print(message)
    if ser.isOpen():
        try:
            # while response == '':
            ser.write(str.encode(message))
                # response = ser.read()
                # response = response.decode('utf-8')
                # read_data += response

            print("Controls send")

        except Exception:
            print('error')
    else:
        print("Cannot open serial port")
    ser.close()

    input("Press enter to go back to menu")
    ser.close()
    return menu()


def read_fft_data():
    ser = serial.Serial(port=config["port"], baudrate=int(config["baudrate"]), bytesize=int(config["bytesize"]),
                        parity=config["parity"], timeout=int(config["timeout"]))
    last_character = 0
    read_buffer = np.zeros([100, 256])
    i = 0
    while 1:
        current_buffer = []
        if ser.isOpen():
            try:
                while last_character != 0xFFFFFFFF:
                    last_character = ser.read()
                    current_buffer.append(last_character)
            except Exception:
                print('error')
        else:
            print("Cannot open serial port")
        read_buffer[i] = np.array(current_buffer)
        plt.plot(read_buffer)



def read_saved(return_to_menu=True):
    with open("config.txt", "r") as file:
        data = file.read()
        set_config_from_string(data)
    with open("controls.txt", "r") as file:
        data = file.read()
        set_controls_from_string(data)
    # print("Config: ")
    # print_map(config)
    # print("Controls: ")
    # print_map(controls)
    # input()
    if return_to_menu:
        return menu()


def save_to_file():
    with open("config.txt", "w+") as file:
        str_config = ""
        for key, val in config.items():
            str_config += str(key)
            str_config += ' '
            str_config += str(val)
            str_config += '\n'
        file.write(str_config)

    with open("controls.txt", "w+") as file:
        str_controls = ""
        for key, val in controls.items():
            str_controls += str(key)
            str_controls += ' '
            str_controls += str(val)
            str_controls += '\n'
        file.write(str_controls)
    return menu()



def clear():
    # for windows
    if name == 'nt':
        _ = system('cls')

    # for mac and linux(here, os.name is 'posix')
    else:
        _ = system('clear')


def exit():
    sys.exit()


def is_number(n):
    try:
        float(n)   # Type-casting the string to `float`.
                   # If string is not a valid `float`,
                   # it'll raise `ValueError` exception
    except ValueError:
        return False
    return True


def main(argv):
    try:
        opts, args = getopt.getopt(argv, "hs:rc:", ["send=", "read", "config="])
    except getopt.GetoptError:
        print("Flags for: uart-connection.py")
        print("none \t\t\t\t open menu")
        print("-s, --send <string to send>; \t send string, with default configuration")
        print("-c, --config <string with config> \t configure connection")
        print("-r, --read; \t\t\t read from default COM port with default configuration")
        sys.exit(2)
    read_saved(return_to_menu=False)
    for opt, arg in opts:
        if opt == '-h':
            print("Flags for: uart-connection.py")
            print("none \t\t\t\t open menu")
            print("-s, --send <string to send> \t send string, with default configuration")
            print("-c, --config <string with config> \t configure connection")
            print("-r, --read \t\t\t read from COM port continously, with 10s delay")
            sys.exit()
        elif opt in ("-s", "--send"):
            send_uart(arg)
        elif opt in ("-c", "--config"):
            set_config_from_string(arg)
        elif opt in ("-r", "--read"):
            read_continous()


if __name__ == "__main__":
   main(sys.argv[1:])

menu()