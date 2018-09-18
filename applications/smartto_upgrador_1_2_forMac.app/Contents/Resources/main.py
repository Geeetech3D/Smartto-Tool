#!/usr/bin/env python
#-*- coding: utf-8 -*-

import os
import time
import math
import zipfile
import chardet
import logging
import requests
import threading
import subprocess
import ttk
from Tkinter import *
from ScrolledText import *
import tkFileDialog as filedialog
import tkFont as tkFont
import UI.TkinterDnD as tkDnD
from Protocol.YModem import YModem
from Protocol.GModem import GModem
from Network.SerialPortClient import SerialPortClient
from Network.NetworkManager import NetworkManager
from Common.CatchableThread import CatchableThread

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(levelname)s %(message)s',
                    datefmt='%H:%M:%S')

timeout_count = 0
timer = None

class FirmwareUpdator(object):
    def __init__(self, output):
        self.serial_list = None
        self.ser = None
        self.output_panel = output

        self.init_output_board()

    def init_output_board(self):
        prompt_conf   =   {
            "info"      :   "blue", 
            "progress"  : "yellow",
            "success"     :   "green", 
            "error"     :   "red"
        }
        for tag, color in prompt_conf.items():
            self.output_panel.tag_config(tag, foreground=color)

    def output_to_panel(self, level, msg):
        prompt = {}
        (prompt['info'], prompt['progress'], prompt['success'], prompt['error']) = ["☼", "➢", "✔", "✘"]
        if level in ['info', 'progress', 'success', 'error']:
            self.output_panel.insert(END, prompt[level], level)
            self.output_panel.insert(END, ' ' + msg)
            self.output_panel.see(END)

    def replace_to_panel(self, level, msg):
        prompt = {}
        (prompt['info'], prompt['progress'], prompt['success'], prompt['error']) = ["☼", "➢", "✔", "✘"]
        if level in ['info', 'progress', 'success', 'error']:
            self.output_panel.delete("%s - 1 chars - 1 lines + 1 chars" % END,  END)
            self.output_panel.insert(END, ' ' + msg)
            self.output_panel.see(END)

    def read_progress_in_avrdude(self, upgrador):
        self.output_to_panel('info', '----------AVRDUDE PROCESSING START----------\n')
        try:
            progress_info = upgrador.stderr.readline()
            upgrador.stderr.flush()
            
            while progress_info  != "":
                '''
                if 'initialized and ready' in progress_info:
                    self.output_to_panel('progress', "Upgrading... 5%(initializing) \n")
                elif 'writing flash' in progress_info:
                    self.replace_to_panel('progress', "Upgrading... 20%(writing flash) \n")
                elif 'reading on-chip flash data' in progress_info:
                    self.replace_to_panel('progress', "Upgrading... 70%(reading on-chip flash data) \n")
                elif 'avrdude.exe done' in progress_info:
                    self.replace_to_panel('progress', "Upgrading... 100% \n")
                    self.output_to_panel('success', "Mainboard(GT2560) upgraded successfully! \n")
                    upgrador.stderr.close()
                    break
                elif 't open device' in progress_info:
                    self.output_to_panel('error', "Cannot open serial port(from avrdude), you should extract USB cable physically!")
                    upgrador.stderr.close()
                    break
                '''
                self.output_to_panel('progress', progress_info)
                progress_info = upgrador.stderr.readline()
                upgrador.stderr.flush()
        except Exception as e:
            self.output_to_panel('error', 'Upgrading interrupted! Details: ' + str(e) + '\n')
            upgrador.stderr.close()
        finally:
            self.output_to_panel('info', '----------AVRDUDE PROCESSING END----------\n')

    def update_firmware(self, profile, com, firmware_file):
        file_name = os.path.split(firmware_file)[1]
        file_end = os.path.splitext(file_name)[1]
        if file_end == '.hex' or file_end == '.HEX':
            self.output_to_panel('success', "Detected mainboard hex file!\n")
            avrdude_path = os.path.join(os.path.join(os.path.split(os.path.realpath(__file__))[0]), "avrdude")
            avrdude_conf_path = os.path.join(os.path.join(os.path.split(os.path.realpath(__file__))[0]), "avrdude.conf")
            avrdude_u_path = path_2_unicode(avrdude_path)
            avrdude_conf_u_path = path_2_unicode(avrdude_conf_path)
            self.output_to_panel('info', "Start to Upgrade Mainboard with avrdude!\n")
            self.output_to_panel('info', "If AVRDUDE interrupted/threw exception, you can extract USB cable physically and restart upgrading process.\n")
            print(avrdude_u_path + ' -P ' + com + ' -C ' +  avrdude_conf_u_path + ' -c stk500v2 -p m2560 -U flash:w:' + firmware_file+':i')
            upgrador = subprocess.Popen([avrdude_u_path, '-P', com, '-C', avrdude_conf_u_path, '-c', 'stk500v2', '-p', 'm2560', '-U', 'flash:w:' + firmware_file+':i'], stderr=subprocess.PIPE, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
            avrdude_listener = CatchableThread(self.read_progress_in_avrdude, upgrador)
            avrdude_listener.setDaemon(True)
            avrdude_listener.start()


        else:
            if '_S_' in firmware_file:
                self.output_to_panel('success', "Detected mainboard bin file!\n")
                try:
                    self.output_to_panel('info', "Initializing Global Configuration...\n")
                    self.init_config(profile, com)
                    
                    self.output_to_panel('info', "Entering Boot Mode...\n")
                    self.set_boot()
                    self.output_to_panel('info', "Start to Upgrade Mainboard...\n")
                    self.upload_mainboard(firmware_file)
                    
                    self.output_to_panel('info', "Restart System...\n")
                    self.reconnect_serial()
                    self.output_to_panel('success', "Mainboard upgraded successfully!\n")
                    self.close_serial()

                except Exception as e:
                    self.output_to_panel('error', "Upgrading failed! Detail: " + str(e) + "\n")
                    return

            elif '_M_' in firmware_file:
                self.output_to_panel('success', "Detected LCD bin file!\n")
                try:
                    self.output_to_panel('info', "Initializing Global Configuration...\n")
                    self.init_config(profile, com)
                    self.output_to_panel('info', "Entering Normal Mode...\n")
                    self.set_normal()
                    self.output_to_panel('info', "Start to Upgrade LCD...\n")
                    self.upload_LCD(firmware_file)
                    self.output_to_panel('success', "LCD upgraded successfully! You may restart your machine manually.\n")
                    self.close_serial()
                except Exception as e:
                    self.output_to_panel('error', "Upgrading failed! Detail: " + str(e) + "\n")
            else:
                self.output_to_panel('error', "Unrecognized file!")

    def init_config(self, profile, com):
        if com == "Empty":
            raise Exception("no port detected!")
        self.port = com

        config = None
        try:
            with open(profile, 'r') as conf_file:
                config = dict(line.strip().split(':') for line in conf_file if line and line.split())
            
            self.baudrate = config['baudrate']
            self.parity = config['parity']
            self.databit = config['databit']
            self.stopbit = config['stopbit']
            
        except Exception as e:
            # logging.error(e)       
            raise Exception("broken profile")

    def set_boot(self):
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
            if timeout_count > 6:
                timer.cancel()
                timeout_count = 0
                raise Exception("open serial port timeout")

            try:
                self.open_serial()
            except Exception as e:
                timer.cancel()
                timeout_count = 0
                raise Exception(e)

            # clear the tunnel
            self.start_on_data_received(self.data_received_handler)
            time.sleep(0.3)
            self.ser.write('c') 
            time.sleep(0.1)
            self.ser.write('1')
            time.sleep(0.1)

            self.stop_serial_listener()

            timer.cancel()
            timeout_count = 0
            break

    def set_normal(self):
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
                raise Exception("open serial port timeout")

            try:
                self.open_serial()
            except Exception as e:
                timer.cancel()
                timeout_count = 0
                raise Exception("cannot make serial port object")
            
            # create a thread(scavenger) to clear tunnel
            self.start_on_data_received(self.data_received_handler)
            time.sleep(3)

            # close scavenger
            self.stop_serial_listener()

            timer.cancel()
            timeout_count = 0
            break

        time.sleep(5)

    def reconnect_serial(self):
        self.ser.reconnect()

    def open_serial(self):
        # auto disconnect
        if self.ser is not None and self.ser.is_connected():
            self.ser.disconnect()

        self.ser = SerialPortClient(Port=self.port,
                                BaudRate=self.baudrate,
                                ByteSize=self.databit,
                                Parity=self.parity,
                                Stopbits=self.stopbit)
        self.ser.connect()

    def data_received_handler(self, data):
        # logging.debug(str(data))
        pass

    def close_serial(self):
        self.ser.disconnect()

    def start_on_data_received(self, func):
        self.ser.start_on_data_received(func)

    def stop_serial_listener(self):
        self.ser.stop_on_data_received()

    def upload_mainboard(self, mainboard):
        parent = self
        def getc(size):
            return parent.ser._serial.read(size) or None
        def putc(data):
            return parent.ser._serial.write(data)
        modem = YModem(getc, putc)
        try:
            stream = open(mainboard, 'rb')
            length = os.path.getsize(mainboard)
        except IOError as e:
            # logging.error(e)
            raise Exception("cannot open profile")
        try:
            modem.send(stream, length, self.data_received_handler, 8, self.record_progress)
        except Exception as e:
            stream.close()
            raise e
        stream.close()

    def upload_LCD(self, LCD):
        parent = self
        def getl():
            return parent.ser._serial.readline() or None
        def putc(data):
            return parent.ser._serial.write(data)
        modem = GModem(getl, putc)
        try:
            stream = open(LCD, 'rb')
            length = os.path.getsize(LCD)
        except IOError as e:
            # logging.error(e)
            raise Exception("cannot open profile")
        try:
            modem.send(stream, length, self.data_received_handler, 8, self.record_progress)
        except Exception as e:
            stream.close()
            raise e
        stream.close()

    def record_progress(self, total_count, ok_count):
        if ok_count == 1:
            self.output_to_panel('progress', "Upgrading... " + str(math.trunc(ok_count * 100 / total_count)) + '% \n')
        else:
            self.replace_to_panel('progress', "Upgrading... " + str(math.trunc(ok_count * 100 / total_count)) + '% \n')


class Application(Frame):
    def __init__(self, master=None):
        Frame.__init__(self, master)
        self.serial_list = None
        self.updator = None
        self.news_list = None
        self.firmware_list = None

        # initialize widgets/UI
        self.createWindow(master, 1280, 800)
        self.createWidget(master)

        try:
            self.network_manager = NetworkManager(self)
            profile_path = os.path.join(os.path.join(os.path.split(os.path.realpath(__file__))[0]), "net.conf")
            profile_u_path = path_2_unicode(profile_path)
            self.network_manager.detect_network_queue()
            self.network_manager.load_config(profile_u_path)
            self.network_manager.run_tasks()
            self.network_manager.detect_serial_port()
            self.network_manager.detect_news()
            self.output_to_panel('success', 'Connecting remote end successfully!\n')
        except Exception as e:
            self.output_to_panel('error', 'Network manager setup failed! Details: ' + str(e) + '\n')

        self.init_ad_board()
        self.init_output_board()

    def show_firmware_details(self, event):
        lbx = event.widget
        index = lbx.curselection()
        size = len(index)
        if size > 0:
            for i in index[::-1]:
                self.firmware_text.delete(1.0, END)
                self.firmware_text.insert(END, 'Firmware:\n' + self.firmware_list[i]["name"] + '\n\n')
                self.firmware_text.see(END)
                details = self.firmware_list[i]["details"]
                for item in details:
                    if item["type"] == "feature":
                        self.firmware_text.insert(END, 'Features:\n')
                        self.firmware_text.see(END)
                        for index, descs in enumerate(item["description"]):
                            self.firmware_text.insert(END,  descs + '\n\n')
                            self.firmware_text.see(END)
                    elif item["type"] == "bug":
                        self.firmware_text.insert(END, 'Bugs:\n')
                        self.firmware_text.see(END)
                        for index, descs in enumerate(item["description"]):
                            self.firmware_text.insert(END, descs + '\n\n')
                            self.firmware_text.see(END)
                self.firmware_text.see(END)

    def init_output_board(self):
        prompt_conf   =   {
            "info"      :   "blue", 
            "progress"  : "yellow",
            "success"     :   "green", 
            "error"     :   "red"
        }
        for tag, color in prompt_conf.items():
            self.info_text.tag_config(tag, foreground=color)

    def init_ad_board(self):
        prompt_conf = {
            "info"      :   "blue",
            "warning"   :   "yellow",
            "solved"    :   "green"
        }
        for tag, color in prompt_conf.items():
            self.news_text.tag_config(tag, foreground=color)

    def show_notice(self, level, msg):
        prompt = {}
        (prompt['info'], prompt['warning'], prompt['solved']) = ["☼", "☢", "☑"]
        if level in ['info', 'warning', 'solved']:
            self.news_text.insert(END, prompt[level], level)
            self.news_text.insert(END, ' ' + msg)
            self.news_text.see(END)

    def output_to_panel(self, level, msg):
        prompt = {}
        (prompt['info'], prompt['progress'], prompt['success'], prompt['error']) = ["☼", "➢", "✔", "✘"]
        if level in ['info', 'progress', 'success', 'error']:
            self.info_text.insert(END, prompt[level], level)
            self.info_text.insert(END, ' ' + msg)
            self.info_text.see(END)

    def createWindow(self, root, width, height):
        screenwidth = root.winfo_screenwidth()  
        screenheight = root.winfo_screenheight()  
        size = '%dx%d+%d+%d' % (width, height, (screenwidth - width)/2, (screenheight - height)/2)
        root.geometry(size)
        root.maxsize(width, height)
        root.minsize(width, height)

    def createWidget(self, master):

        ft = tkFont.Font(family='Lucida Console', size=15)

        self.news_panel = Frame(master, width=450)
        self.news_panel.pack(side=LEFT, fill=Y)

        self.news_upper_menu = Frame(self.news_panel, height=10)
        self.news_upper_menu.pack(side=TOP, fill=X, pady=5)

        self.btn_connect_to_remote = Button(self.news_upper_menu, width=64, text="Reconnect to remote", height=1, command=self.reconnect_to_remote)
        self.btn_connect_to_remote.pack(side=LEFT, anchor="n", padx=10)

        self.news_board = Frame(self.news_panel)
        self.news_board.pack(side=TOP, fill=X, pady=5)

        self.news_text = ScrolledText(self.news_board, state="normal", width=66, height=10, font=ft, highlightbackground = 'black', highlightthickness=1)
        self.news_text.pack(side=LEFT, anchor="n", padx=5)

        self.firmware_board = Frame(self.news_panel)
        self.firmware_board.pack(side=TOP, fill=X, pady=5)

        firmware_list_ft = tkFont.Font(family='Lucida Console', size=12)
        self.lbx_firmware = Listbox(self.firmware_board, width=29, height=32, font=firmware_list_ft)
        self.lbx_firmware.pack(side=LEFT, anchor="n", padx=5)
        self.lbx_firmware.bind('<<ListboxSelect>>', self.show_firmware_details)

        self.firmware_text = ScrolledText(self.firmware_board, state="normal", width=44, height=34, font=firmware_list_ft, highlightbackground = 'black', highlightthickness=1)
        self.firmware_text.pack(side=LEFT, anchor="n", padx=5)

        self.news_lower_menu = Frame(self.news_panel, height=10)
        self.news_lower_menu.pack(side=TOP, fill=X, pady=5)

        self.btn_upgrade_from_remote = Button(self.news_lower_menu, width=64, text="Upgrade from remote", height=1, command=self.create_remote_upgrade_thread)
        self.btn_upgrade_from_remote.pack(side=LEFT, anchor="n", padx=10)

        self.user_panel = Frame(master)
        self.user_panel.pack(side=LEFT, fill=Y)

        self.user_upper_menu = Frame(self.user_panel, height=10)
        self.user_upper_menu.pack(side=TOP, fill=X, pady=5)

        self.lb_port_list = Label(self.user_upper_menu, text="Port:", width=6, height=1)
        self.lb_port_list.pack(side=LEFT, anchor="n", padx=5)
        self.port_item = StringVar()
        self.cb_port_list = ttk.Combobox(self.user_upper_menu, width=25, textvariable=self.port_item, state="readonly")
        self.cb_port_list["values"] = self.serial_list or ("Empty")
        self.cb_port_list.current(0)
        self.cb_port_list.pack(side=LEFT, anchor="w", padx=5)

        self.btn_select = Button(self.user_upper_menu, text="Select", height=1, width=18, command=self.select_firmware)
        self.btn_select.pack(side=LEFT, anchor="w", padx=10)

        self.btn_clear = Button(self.user_upper_menu, text="Clear", height=1, width=8, command=self.clear_info_text)
        self.btn_clear.pack(side=LEFT, anchor="w", padx=10)

        self.display_board = Frame(self.user_panel)
        self.display_board.pack(side=TOP, fill=X, pady=5)

        
        self.info_text = ScrolledText(self.display_board, state="normal", width=70, height=39, font=ft, highlightbackground = 'black', highlightthickness=1)
        self.info_text.bind("<KeyPress>", lambda e: "break")
        self.info_text.pack(side=LEFT, anchor="n", padx=5)
        self.info_text.drop_target_register('DND_Files')
        self.info_text.dnd_bind('<<Drop>>', self.drop_file)

        self.user_lower_menu = Frame(self.user_panel, height=10)
        self.user_lower_menu.pack(side=TOP, fill=X, pady=5)

        self.btn_upgrade_from_local = Button(self.user_lower_menu, width=64, text="Upgrade from local", height=1, command=self.create_upgrade_thread)
        self.btn_upgrade_from_local.pack(side=LEFT, anchor="n", padx=10)

        self.output_to_panel('info', "Drag and drop local firmware into here.\n")

    def drop_file(self, event):
        self.file_path = event.data
        if self.file_path is not None and self.file_path != "":
            self.output_to_panel('success', "Selected path: " + self.file_path + '\n')

    def select_firmware(self):
        self.file_path = filedialog.askopenfilename(filetypes = [('BIN', 'bin'), ('HEX', 'hex')])
        if self.file_path is not None and self.file_path != "":
            self.output_to_panel('success', "Selected path: " + self.file_path + '\n')

    def clear_info_text(self):
        self.info_text.delete(1.0, END)

    def create_remote_upgrade_thread(self):
        index = self.lbx_firmware.curselection()
        size = len(index)
        if size > 0:
            remote_upgrade_thread = threading.Thread(target=self.start_to_remote_upgrade, args=(index))
            remote_upgrade_thread.setDaemon(True)
            remote_upgrade_thread.start()
        else:
            self.output_to_panel('error', "You haven't selected any remote firmware!\n")

    def start_to_remote_upgrade(self, firmware_index):
        '''
        self.btn_upgrade_from_local["state"] = "disabled"
        self.btn_upgrade_from_remote["state"] = "disabled"
        self.btn_connect_to_remote["state"] = "disabled"
        self.btn_select["state"] = "disabled"
        self.btn_clear["state"] = "disabled"
        '''

        try:
            url = self.firmware_list[firmware_index]["url"]
            self.output_to_panel('info', 'Start to get firmware from remote...\n')
            r = requests.get(url)
            if r.status_code == 200:
                firmware_path = os.path.join(os.path.join(os.path.split(os.path.realpath(__file__))[0]), "Firmware", "origin", "firmware.zip")
                firmware_u_path = path_2_unicode(firmware_path)
                with open(firmware_u_path, "wb") as code:
                    code.write(r.content)
                self.output_to_panel('success', 'Firmware downloaded to Firmware/origin/\n')
            elif r.status_code == 404:
                self.output_to_panel('error', 'Firmware doesn\'t exist\n')
                return
            else:
                self.output_to_panel('error', 'Firmware downloaded error! Details: code--%d\n' % r.status_code)
                return
        except Exception as e:
            self.output_to_panel('error', 'Firmware downloaded error! Details: ' + str(e) + '\n')
            return

        self.output_to_panel('info', 'Start to extract files from zip...\n')
        firmware_extract_path = os.path.join(os.path.join(os.path.split(os.path.realpath(__file__))[0]), "Firmware", "extract")
        firmware_extract_u_path = path_2_unicode(firmware_extract_path)

        self.target_file_list = []

        try:
            f = zipfile.ZipFile(firmware_u_path, 'r')
            for file in f.namelist():
                if '_S_' in file or 'hex' in file or 'HEX' in file:
                    self.target_file_list.append(file)
                f.extract(file, firmware_extract_u_path)
            self.output_to_panel('success', 'Firmware extracted to Firmware/extract\n')
        except Exception as e:
            self.output_to_panel('error', 'Firmware extracted error! Details: ' + str(e) + '\n')
            return
        
        self.updator = FirmwareUpdator(self.info_text)

        profile_path = os.path.join(os.path.join(os.path.split(os.path.realpath(__file__))[0]), "default.conf")
        profile_u_path = path_2_unicode(profile_path)

        self.file_path = path_2_unicode(os.path.join(firmware_extract_path, self.target_file_list[0]))
        self.updator.update_firmware(profile_u_path, self.port_item.get(), self.file_path)
        
        '''
        self.btn_upgrade_from_local["state"] = "normal"
        self.btn_upgrade_from_remote["state"] = "normal"
        self.btn_connect_to_remote["state"] = "normal"
        self.btn_select["state"] = "normal"
        self.btn_clear["state"] = "normal"
        '''
    
    def create_upgrade_thread(self):
        if hasattr(self, 'file_path'):
            upgrade_thread = threading.Thread(target=self.start_to_upgrade, args=())
            upgrade_thread.setDaemon(True)
            upgrade_thread.start()
        else:
            self.output_to_panel('error', "You haven't selected any firmware files!\n")

    def start_to_upgrade(self):
        self.btn_upgrade_from_local["state"] = "disabled"
        self.btn_upgrade_from_remote["state"] = "disabled"
        self.btn_connect_to_remote["state"] = "disabled"
        self.btn_select["state"] = "disabled"
        self.btn_clear["state"] = "disabled"
        self.updator = FirmwareUpdator(self.info_text)

        profile = os.path.join(os.path.split(os.path.realpath(__file__))[0], "default.conf")
        profile_path = os.path.join(os.path.join(os.path.split(os.path.realpath(__file__))[0]), "default.conf")
        profile_u_path = path_2_unicode(profile_path)

        self.updator.update_firmware(profile_u_path, self.port_item.get(), self.file_path)
        self.btn_upgrade_from_local["state"] = "normal"
        self.btn_upgrade_from_remote["state"] = "normal"
        self.btn_connect_to_remote["state"] = "normal"
        self.btn_select["state"] = "normal"
        self.btn_clear["state"] = "normal"

    def reconnect_to_remote(self):
        self.network_manager.run_tasks()
        self.output_to_panel('success', 'Reconnecting remote end successfully!\n')

    def close_connection(self):
        if self.updator is not None:
            self.updator.close_serial()

def path_2_utf8(raw_path):
    utf8_path = raw_path.decode(chardet.detect(raw_path)["encoding"]).encode("utf-8")
    return utf8_path

def path_2_unicode(raw_path):
    u_path = raw_path.decode(chardet.detect(raw_path)["encoding"])
    return u_path

if __name__ == '__main__':
    TK_DND_PATH = os.path.join(os.path.join(os.path.split(os.path.realpath(__file__))[0]), "tkdnd2.8")
    master = tkDnD.Tk(TK_DND_PATH)
    master.title('Smatto Firmware Upgrador V1.2 Beta')
    icon_path = os.path.join(os.path.join(os.path.split(os.path.realpath(__file__))[0]), "tool.ico")
    icon_u_path = path_2_unicode(icon_path)
    master.iconbitmap(icon_u_path)
    app = Application(master)
    app.mainloop()