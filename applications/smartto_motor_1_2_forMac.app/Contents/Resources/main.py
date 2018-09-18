# !/usr/bin/env python
#-*- coding: utf-8 -*-

import os
import time
import chardet
import logging
import threading
import ttk
from Tkinter import *
import tkFont as tkFont
from ScrolledText import *
from Helper.DeviceHelper import DeviceHelper
from Helper.SerialHelper import SerialHelper

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(levelname)s %(message)s',
                    datefmt='%H:%M:%S')

timeout_count = 0
timer = None

class MotorController(object):
    def __init__(self, output):
        self.serial_list = None
        self.ser = None
        self.output_panel = output

    def init_config(self, profile, com, show_ports):
        if com == "Empty":
            raise Exception("no port detected")
        self.port = com
        # logging.debug(self.port + ' was chosen')

        config = None
        try:
            with open(profile, 'r') as conf_file:
                config = dict(line.strip().split(':') for line in conf_file if line)
            
            # load parameters from configuration
            self.baudrate = config['baudrate']
            self.parity = config['parity']
            self.databit = config['databit']
            self.stopbit = config['stopbit']
            
        # exception threw when configuration broken or gone, fatal error
        except Exception as e:
            # logging.error(e)       
            raise Exception("broken profile")

    def open_serial(self):
        if self.ser is not None and self.ser.is_connected():
            raise Exception("duplicated serial port")
        
        self.ser = SerialHelper(Port=self.port,
                                BaudRate=self.baudrate,
                                ByteSize=self.databit,
                                Parity=self.parity,
                                Stopbits=self.stopbit)
        self.ser.connect()

    def close_serial(self):
        self.ser.disconnect()

    def send_cmd(self, msg, parent):
        try:
            if self.ser is not None:
                self.ser.write(msg + '\n')
            else:
                raise Exception("no connection")
        except Exception as e:
            raise e

    def send_motor_cmd(self, mode, parent):
        try:
            if self.ser is not None:
                if mode == 1:
                    self.ser.write("M2003 X" + parent.travel_x.get() + " Y" + parent.travel_y.get() + " Z" + parent.travel_z.get() + "\n")
                    self.wait_for_ok()
                elif mode == 2:
                    self.ser.write("M2004 X" + parent.step_x.get() + " Y" + parent.step_y.get() + " Z" + parent.step_z.get() + " E" + parent.step_e.get() + "\n")
                    self.wait_for_ok()
                elif mode == 3:
                    self.ser.write("M2005 X " + parent.direction_x.get() + " Y " + parent.direction_y.get() + " Z " + parent.direction_z.get() + " E0 " + parent.direction_e0.get() + " E1 " + parent.direction_e1.get() + " E2 " + parent.direction_e2.get() + "\n")
                    self.wait_for_ok()
                elif mode == 4:
                    self.ser.write("M2006 X" + parent.velocity_x.get() + " Y" + parent.velocity_y.get() + " Z" + parent.velocity_z.get() + " E" + parent.velocity_e.get() + "\n")
                    self.wait_for_ok()
                elif mode == 5:
                    self.ser.write("M201 X" + parent.max_printing_acceleration_x.get() + " Y" + parent.max_printing_acceleration_y.get() + " Z" + parent.max_printing_acceleration_z.get() + " E" + parent.max_printing_acceleration_e.get() + "\n")
                    self.wait_for_ok()
                elif mode == 6:
                    self.ser.write("M202 X" + parent.max_traveling_acceleration_x.get() + " Y" + parent.max_traveling_acceleration_y.get() + " Z" + parent.max_traveling_acceleration_z.get() + " E" + parent.max_traveling_acceleration_e.get() + "\n")
                    self.wait_for_ok()
                elif mode == 7:
                    self.ser.write("M203 X" + parent.max_feedrate_x.get() + " Y" + parent.max_feedrate_y.get() + " Z" + parent.max_feedrate_z.get() + " E" + parent.max_feedrate_e.get() + "\n")
                    self.wait_for_ok()
                elif mode == 8:
                    self.ser.write("M204 P" + parent.default_acceleration_p.get() + " R" + parent.default_acceleration_r.get() + "\n")
                    self.wait_for_ok()
                elif mode == 9:
                    self.ser.write("M205 S" + parent.min_speed_s.get() + " T" + parent.min_speed_t.get() + "\n")
                    self.wait_for_ok()
                elif mode == 10:
                    self.ser.write("M205 B" + parent.min_segment_time_b.get() + "\n")
                    self.wait_for_ok()
                elif mode == 11:
                    self.ser.write("M205 X" + parent.max_jerk_x.get() + " Y" + parent.max_jerk_y.get() + " Z" + parent.max_jerk_z.get() + " E" + parent.max_jerk_e.get() + "\n")
                    self.wait_for_ok()
                elif mode == 12:
                    self.ser.write("M301 H" + parent.extruder_pid_h.get() + " P" + parent.extruder_pid_p.get() + " I" + parent.extruder_pid_i.get() + " D" + parent.extruder_pid_d.get() + "\n")
                    self.wait_for_ok()
                elif mode ==13:
                    self.ser.write("M304 P" + parent.bed_pid_p.get() + " I" + parent.bed_pid_i.get() + " D" + parent.bed_pid_d.get() + "\n")
                    self.wait_for_ok()
                else:
                    self.ser.write("M500\n")
            else:
                    raise Exception("no connection")
        except Exception as e:
            raise e

    def get_motor_status(self, parent):
        if self.ser is not None:
            self.ser.write("M2002\n")
            self.wait_for_status1()
            parent.travel_x.set(self.s_config1["max_position[X_AXIS]"])
            parent.travel_y.set(self.s_config1["max_position[Y_AXIS]"])
            parent.travel_z.set(self.s_config1["max_position[Z_AXIS]"])
            parent.step_x.set(self.s_config1["steps_per_mm[X_AXIS]"])
            parent.step_y.set(self.s_config1["steps_per_mm[Y_AXIS]"])
            parent.step_z.set(self.s_config1["steps_per_mm[Z_AXIS]"])
            parent.step_e.set(self.s_config1["steps_per_mm[E_AXIS]"])
            parent.direction_x.set(self.s_config1["motor_direction[X_AXIS]"])
            parent.direction_y.set(self.s_config1["motor_direction[Y_AXIS]"])
            parent.direction_z.set(self.s_config1["motor_direction[Z_AXIS]"])
            parent.direction_e0.set(self.s_config1["motor_direction[E_AXIS]"])
            parent.direction_e1.set(self.s_config1["motor_direction[E1_AXIS]"])
            parent.direction_e2.set(self.s_config1["motor_direction[E2_AXIS]"])
            parent.velocity_x.set(self.s_config1["max_feedrate[X_AXIS]"])
            parent.velocity_y.set(self.s_config1["max_feedrate[Y_AXIS]"])
            parent.velocity_z.set(self.s_config1["max_feedrate[Z_AXIS]"])
            parent.velocity_e.set(self.s_config1["max_feedrate[E_AXIS]"])

            self.ser.write("M2202\n")
            self.wait_for_status2()
            parent.max_printing_acceleration_x.set(self.s_config2["max_x_acceleration"])
            parent.max_printing_acceleration_y.set(self.s_config2["max_y_acceleration"])
            parent.max_printing_acceleration_z.set(self.s_config2["max_z_acceleration"])
            parent.max_printing_acceleration_e.set(self.s_config2["max_e_acceleration"])
            parent.max_feedrate_x.set(self.s_config2["max_x_feedrate"])
            parent.max_feedrate_y.set(self.s_config2["max_y_feedrate"])
            parent.max_feedrate_z.set(self.s_config2["max_z_feedrate"])
            parent.max_feedrate_e.set(self.s_config2["max_e_feedrate"])
            parent.default_acceleration_p.set(self.s_config2["acceleration"])
            parent.default_acceleration_r.set(self.s_config2["retract_acceleration"])
            parent.min_speed_s.set(self.s_config2["min_feedrate"])
            parent.min_speed_t.set(self.s_config2["min_travel_feedrate"])
            parent.min_segment_time_b.set(self.s_config2["min_segment_time"])
            parent.max_jerk_x.set(self.s_config2["max_x_jerk"])
            parent.max_jerk_y.set(self.s_config2["max_y_jerk"])
            parent.max_jerk_z.set(self.s_config2["max_z_jerk"])
            parent.max_jerk_e.set(self.s_config2["max_e_jerk"])

            self.ser.write("M301\n")
            self.wait_for_status3()
            parent.extruder_pid_h.set(self.s_config3["hotend_H"])
            parent.extruder_pid_p.set(self.s_config3["P"])
            parent.extruder_pid_i.set(self.s_config3["I"])
            parent.extruder_pid_d.set(self.s_config3["D"])

            self.ser.write("M304\n")
            self.wait_for_status4()
            parent.bed_pid_p.set(self.s_config4["bed_P"])
            parent.bed_pid_i.set(self.s_config4["I"])
            parent.bed_pid_d.set(self.s_config4["D"])
        else:
            raise Exception('no connection')
    
    def wait_for_ok(self):
        global timeout_count
        global timer
        
        def check_receive_timeout():
            global timer
            global timeout_count
            timeout_count += 1
            timer = threading.Timer(1, check_receive_timeout)
            timer.start()
        timer = threading.Timer(1, check_receive_timeout)
        timer.start()
        while True:
            if timeout_count > 5:
                timer.cancel()
                timeout_count = 0
                timer = None
                # error threw when wrong port chosen or not support the command in this firmware version
                raise Exception("receive data timeout")
            line = self.ser._serial.readline()
            if line == None:
                continue
            elif 'ok' in line:
                timer.cancel()
                timeout_count = 0
                timer = None
                break
            else:
                continue
    
    def wait_for_status1(self):
        global timeout_count
        global timer
        
        def check_receive_timeout():
            global timer
            global timeout_count
            timeout_count += 1
            timer = threading.Timer(1, check_receive_timeout)
            timer.start()
        timer = threading.Timer(1, check_receive_timeout)
        timer.start()
        while True:
            if timeout_count > 8:
                timer.cancel()
                timeout_count = 0
                timer = None
                raise Exception("receive data timeout")
            line = self.ser._serial.readline()
            if line == None:
                continue
            elif 'AXIS' in line:
                timer.cancel()
                timeout_count = 0
                timer = None
                config = line.split(";")
                config.pop()
                self.s_config1 = dict(item.strip().split(":") for item in config if item)
                break
            else:
                continue
        
    def wait_for_status2(self):
        global timeout_count
        global timer
        
        def check_receive_timeout():
            global timer
            global timeout_count
            timeout_count += 1
            timer = threading.Timer(1, check_receive_timeout)
            timer.start()
        timer = threading.Timer(1, check_receive_timeout)
        timer.start()
        while True:
            if timeout_count > 8:
                timer.cancel()
                timeout_count = 0
                timer = None
                raise Exception("receive data timeout")
            line = self.ser._serial.readline()
            if line == None:
                continue
            elif 'max' in line:
                timer.cancel()
                timeout_count = 0
                timer = None
                config = line.split(";")
                self.s_config2 = dict(item.strip().split(":") for item in config if item)
                break
            else:
                continue

    def wait_for_status3(self):
        global timeout_count
        global timer
        
        def check_receive_timeout():
            global timer
            global timeout_count
            timeout_count += 1
            timer = threading.Timer(1, check_receive_timeout)
            timer.start()
        timer = threading.Timer(1, check_receive_timeout)
        timer.start()
        while True:
            if timeout_count > 8:
                timer.cancel()
                timeout_count = 0
                timer = None
                raise Exception("receive data timeout")
            line = self.ser._serial.readline()
            if line == None:
                continue
            elif 'hotend' in line:
                timer.cancel()
                timeout_count = 0
                timer = None
                config = line.split(";")
                self.s_config3 = dict(item.strip().split(":") for item in config if item)
                break
            else:
                continue

    def wait_for_status4(self):
        global timeout_count
        global timer

        def check_receive_timeout():
            global timer
            global timeout_count
            timeout_count += 1
            timer = threading.Timer(1, check_receive_timeout)
            timer.start()
        timer = threading.Timer(1, check_receive_timeout)
        timer.start()
        while True:
            if timeout_count > 8:
                timer.cancel()
                timeout_count = 0
                timer = None
                raise Exception("receive data timeout")
            line = self.ser._serial.readline()
            if line == None:
                continue
            elif 'bed' in line:
                timer.cancel()
                timeout_count = 0
                timer = None
                config = line.split(";")
                self.s_config4 = dict(item.strip().split(":") for item in config if item)
                break
            else:
                continue

    def set_normal(self):
        try:
            self.open_serial()
        except Exception as e:
            raise e
        self.start_on_data_received(self.data_received_handler)
        time.sleep(3)
        self.stop_serial_listener()

    def set_motor(self, mode, parent):
        try:
            self.send_motor_cmd(mode, parent)
        except Exception as e:
            raise e

    def start_on_data_received(self, func):
        if self.ser is not None:
            self.ser.start_on_data_received(func)
        else:
            raise Exception("no connection")

    def stop_serial_listener(self):
        if self.ser is not None:
            self.ser.stop_on_data_received()
        else:
            raise Exception("no connection")

    def data_received_handler(self, data):
        # logging.debug(str(data))
        pass

    def reconnect_serial(self):
        try:
            if self.ser is not None:
                self.ser.reconnect()
            else:
                raise Exception("no connection")
        except Exception as e:
            raise e

class Application(Frame):
    def __init__(self, master=None):
        Frame.__init__(self, master)
        self.controller = None
        self.serial_list = None
        self.createWindow(master, 1000, 900)
        self.createWidget(master)

        self.init_output_board()

    def createWindow(self, root, width, height):
        screenwidth = root.winfo_screenwidth()  
        screenheight = root.winfo_screenheight()  
        size = '%dx%d+%d+%d' % (width, height, (screenwidth - width)/2, (screenheight - height)/2)
        root.geometry(size)
        root.maxsize(width, height)
        root.minsize(width, height)

    def createWidget(self, master):

        self.device_helper = DeviceHelper()
        self.device_helper.find_all_devices(self)

        self.menu = Frame(master)
        self.menu.pack(side=TOP, fill=X)

        self.lb_port_list = Label(self.menu, text="Serial Port:", width=10)
        self.lb_port_list.pack(side=LEFT, anchor="n", padx=5, pady=5)

        self.port_item = StringVar()
        self.cb_port_list = ttk.Combobox(self.menu, width=20, textvariable=self.port_item, state="readonly")
        self.cb_port_list["values"] = self.serial_list or ("Empty")
        self.cb_port_list.current(0)
        self.cb_port_list.pack(side=LEFT, anchor="n", pady=5)

        # for controlling the button size
        bitmap_data = """
#define im_width 8
#define im_height 8
static char im_bits[] = {
    0x00, 0x00, 
    0x00, 0x00, 
    0x00, 0x00, 
    0x00, 0x00
};
"""
        bitmap_transparent = BitmapImage(data = bitmap_data)
        self.btn_store = Button(self.menu, text=" Apply",  image=bitmap_transparent, compound="center", anchor="center",   height=15, width=95, command=self.store_parameters)
        self.btn_store.image = bitmap_transparent
        self.btn_store.pack(side=RIGHT, anchor="n", padx=5, pady=5)

        self.btn_get = Button(self.menu, text=" Get Status",  image=bitmap_transparent, compound=RIGHT, anchor="center",   height=15, width=95, command=self.get_motor_status)
        self.btn_get.image = bitmap_transparent
        self.btn_get.pack(side=RIGHT, anchor="n", padx=5, pady=5)

        self.btn_reconnect = Button(self.menu, text=" Reconnect",  image=bitmap_transparent, compound=RIGHT, anchor="center",   height=15, width=95, command=self.reconnect)
        self.btn_reconnect.image = bitmap_transparent
        self.btn_reconnect.pack(side=RIGHT, anchor="n", padx=5, pady=5)

        self.btn_disconnect = Button(self.menu, text=" Disconnect",  image=bitmap_transparent, compound=RIGHT, anchor="center",   height=15, width=95, command=self.disconnect)
        self.btn_disconnect.image = bitmap_transparent
        self.btn_disconnect.pack(side=RIGHT, anchor="n", padx=5, pady=5)

        self.btn_connect = Button(self.menu, text=" Connect",   image=bitmap_transparent, compound=RIGHT, anchor="center",   height=15, width=95, command=self.connect)
        self.btn_connect.image = bitmap_transparent
        self.btn_connect.pack(side=RIGHT, anchor="n", padx=5, pady=5)

        self.upper_panel = Frame(master)
        self.upper_panel.pack(side=TOP, fill=X)

        self.middle_panel = Frame(master)
        self.middle_panel.pack(side=TOP, fill=X)

        self.lower_panel = Frame(master)
        self.lower_panel.pack(side=TOP, fill=X)

        ##########Travel##########

        self.travel_board = Frame(self.upper_panel)
        self.travel_board.pack(side=TOP, fill=X)
        
        self.lb_travel = Label(self.travel_board, text="Motor Travel", anchor = 'w', width=12)
        self.lb_travel.pack(side=LEFT, anchor="n", padx=10, pady=5)

        self.lb_travel_x = Label(self.travel_board, text="X", width=2)
        self.lb_travel_x.pack(side=LEFT, anchor="n", padx=5, pady=5)
        self.travel_x = StringVar()
        self.et_travel_x = Entry(self.travel_board, textvariable=self.travel_x, width=8, state="normal")
        self.et_travel_x.pack(side=LEFT, anchor="n", padx=2, pady=5)
        
        self.lb_travel_y = Label(self.travel_board, text="Y", width=2)
        self.lb_travel_y.pack(side=LEFT, anchor="n", padx=5, pady=5)
        self.travel_y = StringVar()
        self.et_travel_y = Entry(self.travel_board, textvariable=self.travel_y, width=8, state="normal")
        self.et_travel_y.pack(side=LEFT, anchor="n", padx=2, pady=5)

        self.lb_travel_z = Label(self.travel_board, text="Z", width=2)
        self.lb_travel_z.pack(side=LEFT, anchor="n", padx=5, pady=5)
        self.travel_z = StringVar()
        self.et_travel_z = Entry(self.travel_board, textvariable=self.travel_z, width=8, state="normal")
        self.et_travel_z.pack(side=LEFT, anchor="n", padx=2, pady=5)

        self.btn_travel = Button(self.travel_board, text=" Set Travel ",    image=bitmap_transparent, compound=RIGHT, anchor="center",   height=15, width=95, command=self.set_travel)
        self.btn_travel.image = bitmap_transparent
        self.btn_travel.pack(side=RIGHT, anchor="n", padx=5, pady=5)

        ##########Step##########

        self.step_board = Frame(self.upper_panel)
        self.step_board.pack(side=TOP, fill=X)

        self.lb_step = Label(self.step_board, text="Motor Step",  anchor = 'w', width=12)
        self.lb_step.pack(side=LEFT, anchor="n", padx=10, pady=5)

        self.lb_step_x = Label(self.step_board, text="X", width=2)
        self.lb_step_x.pack(side=LEFT, anchor="n", padx=5, pady=5)
        self.step_x = StringVar()
        self.et_step_x = Entry(self.step_board, textvariable=self.step_x, width=8, state="normal")
        self.et_step_x.pack(side=LEFT, anchor="n", padx=2, pady=5)
        
        self.lb_step_y = Label(self.step_board, text="Y", width=2)
        self.lb_step_y.pack(side=LEFT, anchor="n", padx=5, pady=5)
        self.step_y = StringVar()
        self.et_step_y = Entry(self.step_board, textvariable=self.step_y, width=8, state="normal")
        self.et_step_y.pack(side=LEFT, anchor="n", padx=2, pady=5)

        self.lb_step_z = Label(self.step_board, text="Z", width=2)
        self.lb_step_z.pack(side=LEFT, anchor="n", padx=5, pady=5)
        self.step_z = StringVar()
        self.et_step_z = Entry(self.step_board, textvariable=self.step_z, width=8, state="normal")
        self.et_step_z.pack(side=LEFT, anchor="n", padx=2, pady=5)

        self.lb_step_e = Label(self.step_board, text="E", width=2)
        self.lb_step_e.pack(side=LEFT, anchor="n", padx=5, pady=5)
        self.step_e = StringVar()
        self.et_step_e = Entry(self.step_board, textvariable=self.step_e, width=8, state="normal")
        self.et_step_e.pack(side=LEFT, anchor="n", padx=2, pady=5)

        self.btn_step = Button(self.step_board, text=" Set Step ",   image=bitmap_transparent, compound=RIGHT, anchor="center",   height=15, width=95, command=self.set_step)
        self.btn_step.image = bitmap_transparent
        self.btn_step.pack(side=RIGHT, anchor="n", padx=5, pady=5)

        ##########Direction##########

        self.direction_board = Frame(self.upper_panel)
        self.direction_board.pack(side=TOP, fill=X)

        self.lb_direction = Label(self.direction_board, text="Motor Direction", anchor = 'w', width=12)
        self.lb_direction.pack(side=LEFT, anchor="n", padx=10, pady=5)

        self.lb_direction_x = Label(self.direction_board, text="X", width=2)
        self.lb_direction_x.pack(side=LEFT, anchor="n", padx=5, pady=5)
        self.direction_x = StringVar()
        self.et_direction_x = Entry(self.direction_board, textvariable=self.direction_x, width=8, state="normal")
        self.et_direction_x.pack(side=LEFT, anchor="n", padx=2, pady=5)
        
        self.lb_direction_y = Label(self.direction_board, text="Y", width=2)
        self.lb_direction_y.pack(side=LEFT, anchor="n", padx=5, pady=5)
        self.direction_y = StringVar()
        self.et_direction_y = Entry(self.direction_board, textvariable=self.direction_y, width=8, state="normal")
        self.et_direction_y.pack(side=LEFT, anchor="n", padx=2, pady=5)

        self.lb_direction_z = Label(self.direction_board, text="Z", width=2)
        self.lb_direction_z.pack(side=LEFT, anchor="n", padx=5, pady=5)
        self.direction_z = StringVar()
        self.et_direction_z = Entry(self.direction_board, textvariable=self.direction_z, width=8, state="normal")
        self.et_direction_z.pack(side=LEFT, anchor="n", padx=2, pady=5)

        self.lb_direction_e0 = Label(self.direction_board, text="E0", width=2)
        self.lb_direction_e0.pack(side=LEFT, anchor="n", padx=5, pady=5)
        self.direction_e0 = StringVar()
        self.et_direction_e0 = Entry(self.direction_board, textvariable=self.direction_e0, width=8, state="normal")
        self.et_direction_e0.pack(side=LEFT, anchor="n", padx=2, pady=5)

        self.lb_direction_e1 = Label(self.direction_board, text="E1", width=2)
        self.lb_direction_e1.pack(side=LEFT, anchor="n", padx=5, pady=5)
        self.direction_e1 = StringVar()
        self.et_direction_e1 = Entry(self.direction_board, textvariable=self.direction_e1, width=8, state="normal")
        self.et_direction_e1.pack(side=LEFT, anchor="n", padx=2, pady=5)

        self.lb_direction_e2 = Label(self.direction_board, text="E2", width=2)
        self.lb_direction_e2.pack(side=LEFT, anchor="n", padx=5, pady=5)
        self.direction_e2 = StringVar()
        self.et_direction_e2 = Entry(self.direction_board, textvariable=self.direction_e2, width=8, state="normal")
        self.et_direction_e2.pack(side=LEFT, anchor="n", padx=2, pady=5)

        self.btn_direction = Button(self.direction_board, text=" Set Direction ",    image=bitmap_transparent, compound=RIGHT, anchor="center",   height=15, width=95, command=self.set_direction)
        self.btn_direction.image = bitmap_transparent
        self.btn_direction.pack(side=RIGHT, anchor="n", padx=5, pady=5)

        ##########Velocity##########

        self.velocity_board = Frame(self.upper_panel)
        self.velocity_board.pack(side=TOP, fill=X)

        self.lb_velocity = Label(self.velocity_board, text="Motor Velocity", anchor = 'w', width=12)
        self.lb_velocity.pack(side=LEFT, anchor="n", padx=10, pady=5)

        self.lb_velocity_x = Label(self.velocity_board, text="X", width=2)
        self.lb_velocity_x.pack(side=LEFT, anchor="n", padx=5, pady=5)
        self.velocity_x = StringVar()
        self.et_velocity_x = Entry(self.velocity_board, textvariable=self.velocity_x, width=8, state="normal")
        self.et_velocity_x.pack(side=LEFT, anchor="n", padx=2, pady=5)
        
        self.lb_velocity_y = Label(self.velocity_board, text="Y", width=2)
        self.lb_velocity_y.pack(side=LEFT, anchor="n", padx=5, pady=5)
        self.velocity_y = StringVar()
        self.et_velocity_y = Entry(self.velocity_board, textvariable=self.velocity_y, width=8, state="normal")
        self.et_velocity_y.pack(side=LEFT, anchor="n", padx=2, pady=5)

        self.lb_velocity_z = Label(self.velocity_board, text="Z", width=2)
        self.lb_velocity_z.pack(side=LEFT, anchor="n", padx=5, pady=5)
        self.velocity_z = StringVar()
        self.et_velocity_z = Entry(self.velocity_board, textvariable=self.velocity_z, width=8, state="normal")
        self.et_velocity_z.pack(side=LEFT, anchor="n", padx=2, pady=5)

        self.lb_velocity_e = Label(self.velocity_board, text="E", width=2)
        self.lb_velocity_e.pack(side=LEFT, anchor="n", padx=5, pady=5)
        self.velocity_e = StringVar()
        self.et_velocity_e = Entry(self.velocity_board, textvariable=self.velocity_e, width=8, state="normal")
        self.et_velocity_e.pack(side=LEFT, anchor="n", padx=2, pady=5)

        self.btn_velocity = Button(self.velocity_board, text=" Set Velocity ",   image=bitmap_transparent, compound=RIGHT, anchor="center",   height=15, width=95, command=self.set_velocity)
        self.btn_velocity.image = bitmap_transparent
        self.btn_velocity.pack(side=RIGHT, anchor="n", padx=5, pady=5)

        ##########Max Printing Acceleration##########

        self.max_printing_acceleration_board = Frame(self.upper_panel)
        self.max_printing_acceleration_board.pack(side=TOP, fill=X)

        self.lb_max_printing_acceleration = Label(self.max_printing_acceleration_board, text="Max printing acceleration", anchor = 'w', width=25)
        self.lb_max_printing_acceleration.pack(side=LEFT, anchor="n", padx=10, pady=5)

        self.lb_max_printing_acceleration_x = Label(self.max_printing_acceleration_board, text="X", width=2)
        self.lb_max_printing_acceleration_x.pack(side=LEFT, anchor="n", padx=7, pady=5)
        self.max_printing_acceleration_x = StringVar()
        self.et_max_printing_acceleration_x = Entry(self.max_printing_acceleration_board, textvariable=self.max_printing_acceleration_x, width=8, state="normal")
        self.et_max_printing_acceleration_x.pack(side=LEFT, anchor="n", padx=2, pady=5)
        
        self.lb_max_printing_acceleration_y = Label(self.max_printing_acceleration_board, text="Y", width=2)
        self.lb_max_printing_acceleration_y.pack(side=LEFT, anchor="n", padx=5, pady=5)
        self.max_printing_acceleration_y = StringVar()
        self.et_max_printing_acceleration_y = Entry(self.max_printing_acceleration_board, textvariable=self.max_printing_acceleration_y, width=8, state="normal")
        self.et_max_printing_acceleration_y.pack(side=LEFT, anchor="n", padx=2, pady=5)

        self.lb_max_printing_acceleration_z = Label(self.max_printing_acceleration_board, text="Z", width=2)
        self.lb_max_printing_acceleration_z.pack(side=LEFT, anchor="n", padx=5, pady=5)
        self.max_printing_acceleration_z = StringVar()
        self.et_max_printing_acceleration_z = Entry(self.max_printing_acceleration_board, textvariable=self.max_printing_acceleration_z, width=8, state="normal")
        self.et_max_printing_acceleration_z.pack(side=LEFT, anchor="n", padx=2, pady=5)

        self.lb_max_printing_acceleration_e = Label(self.max_printing_acceleration_board, text="E", width=2)
        self.lb_max_printing_acceleration_e.pack(side=LEFT, anchor="n", padx=5, pady=5)
        self.max_printing_acceleration_e = StringVar()
        self.et_max_printing_acceleration_e = Entry(self.max_printing_acceleration_board, textvariable=self.max_printing_acceleration_e, width=8, state="normal")
        self.et_max_printing_acceleration_e.pack(side=LEFT, anchor="n", padx=2, pady=5)

        self.btn_max_printing_acceleration = Button(self.max_printing_acceleration_board, text=" Set Acceleration(P) ",   image=bitmap_transparent, compound=RIGHT, anchor="center",   height=15, width=130, command=self.set_max_printing_acceleration)
        self.btn_max_printing_acceleration.image = bitmap_transparent
        self.btn_max_printing_acceleration.pack(side=RIGHT, anchor="n", padx=5, pady=5)

        ##########Max Traveling Acceleration##########

        self.max_traveling_acceleration_board = Frame(self.upper_panel)
        self.max_traveling_acceleration_board.pack(side=TOP, fill=X)

        self.lb_max_traveling_acceleration = Label(self.max_traveling_acceleration_board, text="Max traveling acceleration", anchor = 'w', width=25)
        self.lb_max_traveling_acceleration.pack(side=LEFT, anchor="n", padx=10, pady=5)

        self.lb_max_traveling_acceleration_x = Label(self.max_traveling_acceleration_board, text="X", width=2)
        self.lb_max_traveling_acceleration_x.pack(side=LEFT, anchor="n", padx=7, pady=5)
        self.max_traveling_acceleration_x = StringVar()
        self.et_max_traveling_acceleration_x = Entry(self.max_traveling_acceleration_board, textvariable=self.max_traveling_acceleration_x, width=8, state="normal")
        self.et_max_traveling_acceleration_x.pack(side=LEFT, anchor="n", padx=2, pady=5)
        
        self.lb_max_traveling_acceleration_y = Label(self.max_traveling_acceleration_board, text="Y", width=2)
        self.lb_max_traveling_acceleration_y.pack(side=LEFT, anchor="n", padx=5, pady=5)
        self.max_traveling_acceleration_y = StringVar()
        self.et_max_traveling_acceleration_y = Entry(self.max_traveling_acceleration_board, textvariable=self.max_traveling_acceleration_y, width=8, state="normal")
        self.et_max_traveling_acceleration_y.pack(side=LEFT, anchor="n", padx=2, pady=5)

        self.lb_max_traveling_acceleration_z = Label(self.max_traveling_acceleration_board, text="Z", width=2)
        self.lb_max_traveling_acceleration_z.pack(side=LEFT, anchor="n", padx=5, pady=5)
        self.max_traveling_acceleration_z = StringVar()
        self.et_max_traveling_acceleration_z = Entry(self.max_traveling_acceleration_board, textvariable=self.max_traveling_acceleration_z, width=8, state="normal")
        self.et_max_traveling_acceleration_z.pack(side=LEFT, anchor="n", padx=2, pady=5)

        self.lb_max_traveling_acceleration_e = Label(self.max_traveling_acceleration_board, text="E", width=2)
        self.lb_max_traveling_acceleration_e.pack(side=LEFT, anchor="n", padx=5, pady=5)
        self.max_traveling_acceleration_e = StringVar()
        self.et_max_traveling_acceleration_e = Entry(self.max_traveling_acceleration_board, textvariable=self.max_traveling_acceleration_e, width=8, state="normal")
        self.et_max_traveling_acceleration_e.pack(side=LEFT, anchor="n", padx=2, pady=5)

        self.btn_max_traveling_acceleration = Button(self.max_traveling_acceleration_board, text=" Set Acceleration(T) ",   image=bitmap_transparent, compound=RIGHT, anchor="center",   height=15, width=130, command=self.set_max_traveling_acceleration)
        self.btn_max_traveling_acceleration.image = bitmap_transparent
        self.btn_max_traveling_acceleration.pack(side=RIGHT, anchor="n", padx=5, pady=5)

        ##########Max Feedrate##########
        self.max_feedrate_board = Frame(self.upper_panel)
        self.max_feedrate_board.pack(side=TOP, fill=X)

        self.lb_max_feedrate = Label(self.max_feedrate_board, text="Max Feedrate", anchor = 'w', width=25)
        self.lb_max_feedrate.pack(side=LEFT, anchor="n", padx=10, pady=5)

        self.lb_max_feedrate_x = Label(self.max_feedrate_board, text="X", width=2)
        self.lb_max_feedrate_x.pack(side=LEFT, anchor="n", padx=7, pady=5)
        self.max_feedrate_x = StringVar()
        self.et_max_feedrate_x = Entry(self.max_feedrate_board, textvariable=self.max_feedrate_x, width=8, state="normal")
        self.et_max_feedrate_x.pack(side=LEFT, anchor="n", padx=2, pady=5)
        
        self.lb_max_feedrate_y = Label(self.max_feedrate_board, text="Y", width=2)
        self.lb_max_feedrate_y.pack(side=LEFT, anchor="n", padx=5, pady=5)
        self.max_feedrate_y = StringVar()
        self.et_max_feedrate_y = Entry(self.max_feedrate_board, textvariable=self.max_feedrate_y, width=8, state="normal")
        self.et_max_feedrate_y.pack(side=LEFT, anchor="n", padx=2, pady=5)

        self.lb_max_feedrate_z = Label(self.max_feedrate_board, text="Z", width=2)
        self.lb_max_feedrate_z.pack(side=LEFT, anchor="n", padx=5, pady=5)
        self.max_feedrate_z = StringVar()
        self.et_max_feedrate_z = Entry(self.max_feedrate_board, textvariable=self.max_feedrate_z, width=8, state="normal")
        self.et_max_feedrate_z.pack(side=LEFT, anchor="n", padx=2, pady=5)

        self.lb_max_feedrate_e = Label(self.max_feedrate_board, text="E", width=2)
        self.lb_max_feedrate_e.pack(side=LEFT, anchor="n", padx=5, pady=5)
        self.max_feedrate_e = StringVar()
        self.et_max_feedrate_e = Entry(self.max_feedrate_board, textvariable=self.max_feedrate_e, width=8, state="normal")
        self.et_max_feedrate_e.pack(side=LEFT, anchor="n", padx=2, pady=5)

        self.btn_max_feedrate = Button(self.max_feedrate_board, text=" Set Feedrate ",  image=bitmap_transparent, compound=RIGHT, anchor="center",   height=15, width=130, command=self.set_max_feedrate)
        self.btn_max_feedrate.image = bitmap_transparent
        self.btn_max_feedrate.pack(side=RIGHT, anchor="n", padx=5, pady=5)

        ##########Default Acceleration##########
        self.default_acceleration_board = Frame(self.upper_panel)
        self.default_acceleration_board.pack(side=TOP, fill=X)

        self.lb_default_acceleration = Label(self.default_acceleration_board, text="Default acceleration", anchor = 'w', width=25)
        self.lb_default_acceleration.pack(side=LEFT, anchor="n", padx=10, pady=5)

        self.lb_default_acceleration_p = Label(self.default_acceleration_board, text="P", width=2)
        self.lb_default_acceleration_p.pack(side=LEFT, anchor="n", padx=7, pady=5)
        self.default_acceleration_p = StringVar()
        self.et_default_acceleration_p = Entry(self.default_acceleration_board, textvariable=self.default_acceleration_p, width=8, state="normal")
        self.et_default_acceleration_p.pack(side=LEFT, anchor="n", padx=2, pady=5)

        self.lb_default_acceleration_r = Label(self.default_acceleration_board, text="R", width=2)
        self.lb_default_acceleration_r.pack(side=LEFT, anchor="n", padx=5, pady=5)
        self.default_acceleration_r = StringVar()
        self.et_default_acceleration_r = Entry(self.default_acceleration_board, textvariable=self.default_acceleration_r, width=8, state="normal")
        self.et_default_acceleration_r.pack(side=LEFT, anchor="n", padx=2, pady=5)

        self.btn_default_acceleration = Button(self.default_acceleration_board, text=" Set Acceleration(D) ",   image=bitmap_transparent, compound=RIGHT, anchor="center",   height=15, width=130, command=self.set_default_acceleration)
        self.btn_default_acceleration.image = bitmap_transparent
        self.btn_default_acceleration.pack(side=RIGHT, anchor="n", padx=5, pady=5)


        ##########Extruder PID##########

        self.extruder_pid_board = Frame(self.upper_panel)
        self.extruder_pid_board.pack(side=TOP, fill=X)

        self.lb_extruder_pid = Label(self.extruder_pid_board, text="Extruder PID", anchor = 'w', width=12)
        self.lb_extruder_pid.pack(side=LEFT, anchor="n", padx=10, pady=5)

        self.lb_extruder_pid_h = Label(self.extruder_pid_board, text="H", width=2)
        self.lb_extruder_pid_h.pack(side=LEFT, anchor="n", padx=5, pady=5)
        self.extruder_pid_h = StringVar()
        self.et_extruder_pid_h = Entry(self.extruder_pid_board, textvariable=self.extruder_pid_h, width=8, state="normal")
        self.et_extruder_pid_h.pack(side=LEFT, anchor="n", padx=2, pady=5)

        self.lb_extruder_pid_p = Label(self.extruder_pid_board, text="P", width=2)
        self.lb_extruder_pid_p.pack(side=LEFT, anchor="n", padx=5, pady=5)
        self.extruder_pid_p = StringVar()
        self.et_extruder_pid_p = Entry(self.extruder_pid_board, textvariable=self.extruder_pid_p, width=8, state="normal")
        self.et_extruder_pid_p.pack(side=LEFT, anchor="n", padx=2, pady=5)
        
        self.lb_extruder_pid_i = Label(self.extruder_pid_board, text="I", width=2)
        self.lb_extruder_pid_i.pack(side=LEFT, anchor="n", padx=5, pady=5)
        self.extruder_pid_i = StringVar()
        self.et_extruder_pid_i = Entry(self.extruder_pid_board, textvariable=self.extruder_pid_i, width=8, state="normal")
        self.et_extruder_pid_i.pack(side=LEFT, anchor="n", padx=2, pady=5)

        self.lb_extruder_pid_d = Label(self.extruder_pid_board, text="D", width=2)
        self.lb_extruder_pid_d.pack(side=LEFT, anchor="n", padx=5, pady=5)
        self.extruder_pid_d = StringVar()
        self.et_extruder_pid_d = Entry(self.extruder_pid_board, textvariable=self.extruder_pid_d, width=8, state="normal")
        self.et_extruder_pid_d.pack(side=LEFT, anchor="n", padx=2, pady=5)


        self.btn_extruder_pid = Button(self.extruder_pid_board, text=" Set Extruder PID ",  image=bitmap_transparent, compound=RIGHT, anchor="center",   height=15, width=130, command=self.set_extruder_pid)
        self.btn_extruder_pid.image = bitmap_transparent
        self.btn_extruder_pid.pack(side=RIGHT, anchor="n", padx=5, pady=5)

        ##########Bed PID##########
        self.bed_pid_board = Frame(self.upper_panel)
        self.bed_pid_board.pack(side=TOP, fill=X)

        self.lb_bed_pid = Label(self.bed_pid_board, text="Bed PID", anchor = 'w', width=12)
        self.lb_bed_pid.pack(side=LEFT, anchor="n", padx=10, pady=5)

        self.lb_bed_pid_p = Label(self.bed_pid_board, text="P", width=2)
        self.lb_bed_pid_p.pack(side=LEFT, anchor="n", padx=5, pady=5)
        self.bed_pid_p = StringVar()
        self.et_bed_pid_p = Entry(self.bed_pid_board, textvariable=self.bed_pid_p, width=8, state="normal")
        self.et_bed_pid_p.pack(side=LEFT, anchor="n", padx=2, pady=5)
        
        self.lb_bed_pid_i = Label(self.bed_pid_board, text="I", width=2)
        self.lb_bed_pid_i.pack(side=LEFT, anchor="n", padx=5, pady=5)
        self.bed_pid_i = StringVar()
        self.et_bed_pid_i = Entry(self.bed_pid_board, textvariable=self.bed_pid_i, width=8, state="normal")
        self.et_bed_pid_i.pack(side=LEFT, anchor="n", padx=2, pady=5)

        self.lb_bed_pid_d = Label(self.bed_pid_board, text="D", width=2)
        self.lb_bed_pid_d.pack(side=LEFT, anchor="n", padx=5, pady=5)
        self.bed_pid_d = StringVar()
        self.et_bed_pid_d = Entry(self.bed_pid_board, textvariable=self.bed_pid_d, width=8, state="normal")
        self.et_bed_pid_d.pack(side=LEFT, anchor="n", padx=2, pady=5)


        self.btn_bed_pid = Button(self.bed_pid_board, text=" Set Bed PID ",   image=bitmap_transparent, compound=RIGHT, anchor="center",   height=15, width=130, command=self.set_bed_pid)
        self.btn_bed_pid.image = bitmap_transparent
        self.btn_bed_pid.pack(side=RIGHT, anchor="n", padx=5, pady=5)

        ##########Min Speed##########
        self.min_speed_board = Frame(self.upper_panel)
        self.min_speed_board.pack(side=TOP, fill=X)

        self.lb_min_speed = Label(self.min_speed_board, text="Min Speed", anchor = 'w', width=12)
        self.lb_min_speed.pack(side=LEFT, anchor="n", padx=10, pady=5)

        self.lb_min_speed_s = Label(self.min_speed_board, text="S", width=2)
        self.lb_min_speed_s.pack(side=LEFT, anchor="n", padx=5, pady=5)
        self.min_speed_s = StringVar()
        self.et_min_speed_s = Entry(self.min_speed_board, textvariable=self.min_speed_s, width=8, state="normal")
        self.et_min_speed_s.pack(side=LEFT, anchor="n", padx=2, pady=5)
        
        self.lb_min_speed_t = Label(self.min_speed_board, text="T", width=2)
        self.lb_min_speed_t.pack(side=LEFT, anchor="n", padx=5, pady=5)
        self.min_speed_t = StringVar()
        self.et_min_speed_t = Entry(self.min_speed_board, textvariable=self.min_speed_t, width=8, state="normal")
        self.et_min_speed_t.pack(side=LEFT, anchor="n", padx=2, pady=5)


        self.btn_min_speed = Button(self.min_speed_board, text=" Set Min Speed ",   image=bitmap_transparent, compound=RIGHT, anchor="center",   height=15, width=130, command=self.set_min_speed)
        self.btn_min_speed.image = bitmap_transparent
        self.btn_min_speed.pack(side=RIGHT, anchor="n", padx=5, pady=5)
        

        ##########Min Segment Time##########
        self.min_segment_time_board = Frame(self.upper_panel)
        self.min_segment_time_board.pack(side=TOP, fill=X)

        self.lb_min_segment_time = Label(self.min_segment_time_board, text="Min Segment Time", anchor = 'w', width=25)
        self.lb_min_segment_time.pack(side=LEFT, anchor="n", padx=10, pady=5)

        self.lb_min_segment_time_b = Label(self.min_segment_time_board, text="B", width=2)
        self.lb_min_segment_time_b.pack(side=LEFT, anchor="n", padx=7, pady=5)
        self.min_segment_time_b = StringVar()
        self.et_min_segment_time_b = Entry(self.min_segment_time_board, textvariable=self.min_segment_time_b, width=8, state="normal")
        self.et_min_segment_time_b.pack(side=LEFT, anchor="n", padx=2, pady=5)

        self.btn_min_segment_time = Button(self.min_segment_time_board, text=" Set Min Speed ",  image=bitmap_transparent, compound=RIGHT, anchor="center",   height=15, width=130, command=self.set_min_segment_time)
        self.btn_min_segment_time.image = bitmap_transparent
        self.btn_min_segment_time.pack(side=RIGHT, anchor="n", padx=5, pady=5)

        ##########Max Jerk##########
        self.max_jerk_board = Frame(self.upper_panel)
        self.max_jerk_board.pack(side=TOP, fill=X)

        self.lb_max_jerk = Label(self.max_jerk_board, text="Max Jerk", anchor = 'w', width=12)
        self.lb_max_jerk.pack(side=LEFT, anchor="n", padx=10, pady=5)

        self.lb_max_jerk_x = Label(self.max_jerk_board, text="X", width=2)
        self.lb_max_jerk_x.pack(side=LEFT, anchor="n", padx=5, pady=5)
        self.max_jerk_x = StringVar()
        self.et_max_jerk_x = Entry(self.max_jerk_board, textvariable=self.max_jerk_x, width=8, state="normal")
        self.et_max_jerk_x.pack(side=LEFT, anchor="n", padx=2, pady=5)
        
        self.lb_max_jerk_y = Label(self.max_jerk_board, text="Y", width=2)
        self.lb_max_jerk_y.pack(side=LEFT, anchor="n", padx=5, pady=5)
        self.max_jerk_y = StringVar()
        self.et_max_jerk_y = Entry(self.max_jerk_board, textvariable=self.max_jerk_y, width=8, state="normal")
        self.et_max_jerk_y.pack(side=LEFT, anchor="n", padx=2, pady=5)

        self.lb_max_jerk_z = Label(self.max_jerk_board, text="Z", width=2)
        self.lb_max_jerk_z.pack(side=LEFT, anchor="n", padx=5, pady=5)
        self.max_jerk_z = StringVar()
        self.et_max_jerk_z = Entry(self.max_jerk_board, textvariable=self.max_jerk_z, width=8, state="normal")
        self.et_max_jerk_z.pack(side=LEFT, anchor="n", padx=2, pady=5)

        self.lb_max_jerk_e = Label(self.max_jerk_board, text="E", width=2)
        self.lb_max_jerk_e.pack(side=LEFT, anchor="n", padx=5, pady=5)
        self.max_jerk_e = StringVar()
        self.et_max_jerk_e = Entry(self.max_jerk_board, textvariable=self.max_jerk_e, width=8, state="normal")
        self.et_max_jerk_e.pack(side=LEFT, anchor="n", padx=2, pady=5)

        self.btn_max_jerk = Button(self.max_jerk_board, text=" Set Max Jerk ",   image=bitmap_transparent, compound=RIGHT, anchor="center",   height=15, width=130, command=self.set_max_jerk)
        self.btn_max_jerk.image = bitmap_transparent
        self.btn_max_jerk.pack(side=RIGHT, anchor="n", padx=5, pady=5)

        ##########Custom Command Line##########

        self.lb_command_line = Label(self.middle_panel, text="Command", width=10)
        self.lb_command_line.pack(side=LEFT, anchor="n", padx=5, pady=5)
        self.command_line = StringVar()
        self.et_command_line = Entry(self.middle_panel, textvariable=self.command_line, width=78, state="normal")
        self.et_command_line.pack(side=LEFT, anchor="n", padx=2, pady=5)

        self.btn_command = Button(self.middle_panel, text=" Send Command ",  image=bitmap_transparent, width=130, height=15, compound=RIGHT, anchor="center", command=self.send_command)
        self.btn_command.image = bitmap_transparent
        self.btn_command.pack(side=RIGHT, anchor="n", padx=5, pady=5)

        ft = tkFont.Font(family='Lucida Console', size=10)
        self.motor_text = ScrolledText(self.lower_panel, state="normal", width=200, font=ft, highlightbackground="black", highlightthickness=1)
        self.motor_text.bind("<KeyPress>", lambda e: "break")
        self.motor_text.pack(side=LEFT, anchor="n", padx=5)

        self.controller = MotorController(self.motor_text)
        profile_path = os.path.join(os.path.join(os.path.split(os.path.realpath(__file__))[0]), "default.conf")
        profile_u_path = path_2_unicode(profile_path)
        self.profile = profile_u_path

        self.output_to_panel('info', "Traveling acceleration is unavailable now.\n")
        self.output_to_panel('info', "About acceleration settings, they all in unit/sec^2.\n")
        self.output_to_panel('info', "If you have problems in using, please contact us.\n")

    def init_output_board(self):
        prompt_conf   =   {
            "info"      :   "blue", 
            "success"     :   "green", 
            "error"     :   "red"
        }
        for tag, color in prompt_conf.items():
            self.motor_text.tag_config(tag, foreground=color)

    def output_to_panel(self, level, msg):
        prompt = {}
        (prompt['info'], prompt['success'], prompt['error']) = ["☼", "✔", "✘"]
        if level in ['info', 'success', 'error']:
            self.motor_text.insert(END, prompt[level], level)
            self.motor_text.insert(END, ' ' + msg)
            self.motor_text.see(END)

    def send_command(self):
        try:
            if self.controller is not None:
                self.controller.send_cmd(self.command_line.get(), self)
                self.output_to_panel('success', "Custom command has been sent\n")
            else:
                self.output_to_panel('error', "Controller is not initialized!\n")
        except Exception as e:
            self.output_to_panel('error', "Cannot send custom command! Details: " + str(e) + '\n')

    def set_travel(self):
        try:
            if self.controller is not None:
                self.controller.set_motor(1, self)
                self.output_to_panel('success', "Command of setting travel has been sent\n")
            else:
                self.output_to_panel('error', "Controller is not initialized!\n")
        except Exception as e:
            self.output_to_panel('error', "Cannot send command of setting travel! Details: " + str(e) + '\n')
    
    def set_step(self):
        try:
            if self.controller is not None:
                self.controller.set_motor(2, self)
                self.output_to_panel('success', "Command of setting step has been sent\n")
            else:
                self.output_to_panel('error', "Controller is not initialized!\n")
        except Exception as e:
            self.output_to_panel('error', "Cannot send command of setting step! Details: " + str(e) + '\n')
    
    def set_direction(self):
        try:
            if self.controller is not None:
                self.controller.set_motor(3, self)
                self.output_to_panel('success', "Command of setting direction has been sent\n")
            else:
                self.output_to_panel('error', "Controller is not initialized!\n")
        except Exception as e:
            self.output_to_panel('error', "Cannot send command of setting direction! Details: " + str(e) + '\n')
    
    def set_velocity(self):
        try:
            if self.controller is not None:
                self.controller.set_motor(4, self)
                self.output_to_panel('success', "Command of setting velocity has been sent\n")
            else:
                self.output_to_panel('error', "Controller is not initialized!\n")
        except Exception as e:
            self.output_to_panel('error', "Cannot send command of setting velocity! Details: " + str(e) + '\n')

    def set_max_printing_acceleration(self):
        try:
            if self.controller is not None:
                self.controller.set_motor(5, self)
                self.output_to_panel('success', "Command of setting max printing acceleration has been sent\n")
            else:
                self.output_to_panel('error', "Controller is not initialized!\n")
        except Exception as e:
            self.output_to_panel('error', "Cannot send command of setting max printing acceleration! Details: " + str(e) + '\n')

    def set_max_traveling_acceleration(self):
        try:
            if self.controller is not None:
                self.controller.set_motor(6, self)
                self.output_to_panel('success', "Command of setting max traveling acceleration has been sent\n")
            else:
                self.output_to_panel('error', "Controller is not initialized!\n")
        except Exception as e:
            self.output_to_panel('error', "Cannot send command of setting max traveling acceleration! Details: " + str(e) + '\n')

    def set_max_jerk(self):
        try:
            if self.controller is not None:
                self.controller.set_motor(11, self)
                self.output_to_panel('success', "Command of setting max jerk has been sent\n")
            else:
                self.output_to_panel('error', "Controller is not initialized!\n")
        except Exception as e:
            self.output_to_panel('error', "Cannot send command of setting max jerk! Details: " + str(e) + '\n')

    def set_max_feedrate(self):
        try:
            if self.controller is not None:
                self.controller.set_motor(7, self)
                self.output_to_panel('success', "Command of setting max feedrate has been sent\n")
            else:
                self.output_to_panel('error', "Controller is not initialized!\n")
        except Exception as e:
            self.output_to_panel('error', "Cannot send command of setting max feedrate! Details: " + str(e) + '\n')

    def set_default_acceleration(self):
        try:
            if self.controller is not None:
                self.controller.set_motor(8, self)
                self.output_to_panel('success', "Command of setting default acceleration has been sent\n")
            else:
                self.output_to_panel('error', "Controller is not initialized!\n")
        except Exception as e:
            self.output_to_panel('error', "Cannot send command of setting default acceleration! Details: " + str(e) + '\n')

    def set_extruder_pid(self):
        try:
            if self.controller is not None:
                self.controller.set_motor(12, self)
                self.output_to_panel('success', "Command of setting extruder PID has been sent\n")
            else:
                self.output_to_panel('error', "Controller is not initialized!\n")
        except Exception as e:
            self.output_to_panel('error', "Cannot send command of setting extruder PID! Details: " + str(e) + '\n')

    def set_bed_pid(self):
        try:
            if self.controller is not None:
                self.controller.set_motor(13, self)
                self.output_to_panel('success', "Command of setting bed PID has been sent\n")
            else:
                self.output_to_panel('error', "Controller is not initialized!\n")
        except Exception as e:
            self.output_to_panel('error', "Cannot send command of setting bed PID! Details: " + str(e) + '\n')

    def set_min_speed(self):
        try:
            if self.controller is not None:
                self.controller.set_motor(9, self)
                self.output_to_panel('success', "Command of setting min speed has been sent\n")
            else:
                self.output_to_panel('error', "Controller is not initialized!\n")
        except Exception as e:
            self.output_to_panel('error', "Cannot send command of setting min speed! Details: " + str(e) + '\n')

    def set_min_segment_time(self):
        try:
            if self.controller is not None:
                self.controller.set_motor(10, self)
                self.output_to_panel('success', "Command of setting min segment time has been sent\n")
            else:
                self.output_to_panel('error', "Controller is not initialized!\n")
        except Exception as e:
            self.output_to_panel('error', "Cannot send command of setting min segment time! Details: " + str(e) + '\n')

    def store_parameters(self):
        try:
            if self.controller is not None:
                self.controller.set_motor(14, self)
                self.output_to_panel('success', "Command of storing parameter set has been sent\n")
            else:
                self.output_to_panel('error', "Controller is not initialized!\n")
        except Exception as e:
            self.output_to_panel('error', "Cannot send command of storing parameter set! Details: " + str(e) + '\n')
    
    def connect(self):
        try:
            if self.controller is not None:
                self.output_to_panel('info', "Start to initialize configuration...\n")
                self.controller.init_config(self.profile, self.port_item.get(), False)
                self.output_to_panel('info', "Start to set normal mode...\n")
                self.controller.set_normal()
                self.output_to_panel('success', "Connected to port: " + self.port_item.get() + "\n")
            else:
                self.output_to_panel('error', "Controller is not initialized!\n")
        except Exception as e:
            self.output_to_panel('error', "Connecting failed! Details: " + str(e) + "\n")
        
    
    def disconnect(self):
        try:
            if self.controller is not None:
                self.controller.close_serial()
                self.output_to_panel('success', "Serial port has been closed!\n")
            else:
                self.output_to_panel('error', 'Controller is not initialized!\n')
        except Exception as e:
            self.output_to_panel('error', 'Cannot disconnect serial port! Details: ' + str(e) + "\n")

    def reconnect(self):
        try:
            if self.controller is not None:
                self.controller.reconnect_serial()
                self.output_to_panel('success', "Serial port has been reconnected!\n")
            else:
                self.output_to_panel('error', 'Controller is not initialized!\n')
        except Exception as e:
            self.output_to_panel('error', "Cannot reconnect serial port! Details: " + str(e) + "\n")
    
    def get_motor_status(self):
        try:
            if self.controller is not None:
                self.controller.get_motor_status(self)
                self.output_to_panel('success', 'Getting status successfully!\n')
            else:
                self.output_to_panel('error', 'Controller is not initialized!\n')
        except Exception as e:
            self.output_to_panel('error', "Getting status failed! Details: " + str(e) + "\n")
        
def path_2_utf8(raw_path):
    utf8_path = raw_path.decode(chardet.detect(raw_path)["encoding"]).encode("utf-8")
    return utf8_path

def path_2_unicode(raw_path):
    u_path = raw_path.decode(chardet.detect(raw_path)["encoding"])
    return u_path

if __name__ == '__main__':
    master = Tk()
    master.title('Smatto Motor Tool V1.2')
    icon_path = os.path.join(os.path.join(os.path.split(os.path.realpath(__file__))[0]), "tool.ico")
    icon_u_path = path_2_unicode(icon_path)
    master.iconbitmap(icon_u_path)
    app = Application(master)
    app.mainloop()






