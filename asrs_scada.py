# -*- coding: utf-8 -*-

from PyQt5 import QtCore, QtGui, QtWidgets
import snap7
from snap7.util import *
from snap7 import *
import subprocess

class Ui_MainWindow(object):

    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(661, 642)
        MainWindow.setMinimumSize(QtCore.QSize(661, 642))
        MainWindow.setMaximumSize(QtCore.QSize(661, 642))
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.gridLayout = QtWidgets.QGridLayout(self.centralwidget)
        self.gridLayout.setObjectName("gridLayout")

        self.shelves = {}
        self.system_on = False
        self.system_ready = False
        self.operation = None

        # Initialize Snap7 client
        self.plc = snap7.client.Client()
        self.plc.connect('192.168.56.105', 0, 1)

        self.createWidgets(MainWindow)

        MainWindow.setCentralWidget(self.centralwidget)
        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

        # Initialize QTimer
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.updateShelfColors)

    def createWidgets(self, MainWindow):
        self.guc_switch = QtWidgets.QPushButton(self.centralwidget)
        self.guc_switch.setObjectName("guc_switch")
        self.guc_switch.setText("Güç YOK")
        self.guc_switch.setStyleSheet("background-color: red")
        self.guc_switch.clicked.connect(self.togglePower)
        self.gridLayout.addWidget(self.guc_switch, 0, 0, 1, 2)

        self.start_stop_button = QtWidgets.QPushButton(self.centralwidget)
        self.start_stop_button.setObjectName("start_stop_button")
        self.start_stop_button.setText("Start")
        self.start_stop_button.setEnabled(False)
        self.start_stop_button.setStyleSheet("background-color: grey")
        self.start_stop_button.clicked.connect(self.startStop)
        self.gridLayout.addWidget(self.start_stop_button, 0, 2, 1, 2)

        self.urun_al_button = QtWidgets.QPushButton(self.centralwidget)
        self.urun_al_button.setObjectName("urun_al_button")
        self.urun_al_button.setText("Ürün Al")
        self.urun_al_button.setEnabled(False)
        self.urun_al_button.setStyleSheet("background-color: grey")
        self.urun_al_button.clicked.connect(self.urunAl)
        self.gridLayout.addWidget(self.urun_al_button, 0, 4, 1, 2)

        self.urun_birak_button = QtWidgets.QPushButton(self.centralwidget)
        self.urun_birak_button.setObjectName("urun_birak_button")
        self.urun_birak_button.setText("Ürün Bırak")
        self.urun_birak_button.setEnabled(False)
        self.urun_birak_button.setStyleSheet("background-color: grey")
        self.urun_birak_button.clicked.connect(self.urunBirak)
        self.gridLayout.addWidget(self.urun_birak_button, 0, 6, 1, 2)

        self.kamera_button = QtWidgets.QPushButton(self.centralwidget)
        self.kamera_button.setObjectName("kamera_button")
        self.kamera_button.setText("Kamera (DEMO)")
        self.kamera_button.setEnabled(False)
        self.kamera_button.setStyleSheet("background-color: grey")
        self.kamera_button.clicked.connect(self.startKamera)
        self.gridLayout.addWidget(self.kamera_button, 0, 8, 1, 2)     

        for i in range(1, 11):
            label = QtWidgets.QLabel(self.centralwidget)
            label.setObjectName(f"Raf{i}")
            self.gridLayout.addWidget(label, i, 0, 1, 1)

            for j in range(1, 11):
                button = QtWidgets.QPushButton(self.centralwidget)
                button.setObjectName(f"Raf{i}_Sira{j}")
                button.clicked.connect(lambda ch, r=i, s=j: self.buttonClicked(r, s))
                self.gridLayout.addWidget(button, i, j, 1, 1)
                self.shelves[(i, j)] = button  

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "AS/RS SCADA"))

        for i in range(1, 11):
            shelfLabel = self.centralwidget.findChild(QtWidgets.QLabel, f"Raf{i}")
            shelfLabel.setText(_translate("MainWindow", f"Raf {i}"))

        for (i, j) in self.shelves:
            self.shelves[(i, j)].setText(_translate("MainWindow", f"{j}"))

    def togglePower(self):
        self.system_on = not self.system_on
        self.updatePowerState()

    def updatePowerState(self):
        if self.system_on:
            self.guc_switch.setText("Güç VAR")
            self.guc_switch.setStyleSheet("background-color: green")
            self.start_stop_button.setEnabled(True)
            self.start_stop_button.setStyleSheet("background-color: yellow")
            sPower = self.plc.db_read(7, 0, 1)
            set_bool(sPower, 0, 0, self.system_on)
            self.plc.db_write(7, 0, sPower)  # Write to sPower (DB7.DBX0.0)
            self.updateShelfColors()
        else:
            self.updateShelfColors()
            self.guc_switch.setText("Güç YOK")
            self.guc_switch.setStyleSheet("background-color: red")
            self.start_stop_button.setEnabled(False)
            self.start_stop_button.setStyleSheet("background-color: grey")
            self.urun_al_button.setEnabled(False)
            self.urun_al_button.setStyleSheet("background-color: grey")
            self.urun_birak_button.setEnabled(False)
            self.urun_birak_button.setStyleSheet("background-color: grey")
            self.kamera_button.setStyleSheet("background-color: grey")
            self.kamera_button.setEnabled(False)
            self.system_ready = False
            self.clearShelfColors()

            # Reset all PLC flags
            sPower = self.plc.db_read(7, 0, 1)
            set_bool(sPower, 0, 0, self.system_on)
            self.plc.db_write(7, 0, sPower)  # Write to sPower (DB7.DBX0.0)
            sSituation = self.plc.db_read(7, 0, 1)
            set_bool(sSituation, 0, 1, self.system_ready)
            self.plc.db_write(7, 0, sSituation)  # Write to sSituation (DB7.DBX0.1)
            sAl = self.plc.db_read(7, 0, 1)
            set_bool(sAl, 0, 2, False)
            self.plc.db_write(7, 0, sAl)  # Write to sAl (DB7.DBX0.2)
            sBirak = self.plc.db_read(7, 0, 1)
            set_bool(sBirak, 0, 3, False)
            self.plc.db_write(7, 0, sBirak)  # Write to sBirak (DB7.DBX0.3)
            data = self.plc.db_read(7, 1, 1)
            set_usint(data, 0, 0)
            self.plc.db_write(7, 1, data)  # Write to sRaf (DB7.DBD1.0)
            data = self.plc.db_read(7, 2, 1)
            set_usint(data, 0, 0)
            self.plc.db_write(7, 2, data)  # Write to sUrun (DB7.DBD2.0)

    def startStop(self):
        if not self.system_on:
            return
        self.system_ready = not self.system_ready
        self.start_stop_button.setText("Stop" if self.system_ready else "Start")
        self.start_stop_button.setStyleSheet("background-color: green" if self.system_ready else "background-color: yellow")
        self.urun_al_button.setEnabled(self.system_ready)
        self.urun_al_button.setStyleSheet("background-color: white" if self.system_ready else "background-color: grey")
        self.urun_birak_button.setEnabled(self.system_ready)
        self.urun_birak_button.setStyleSheet("background-color: white" if self.system_ready else "background-color: grey") 
        self.kamera_button.setEnabled(self.system_ready)
        self.kamera_button.setStyleSheet("background-color: white" if self.system_ready else "background-color: grey")        
        
        sSituation = self.plc.db_read(7, 0, 1)
        set_bool(sSituation, 0, 1, self.system_ready)
        self.plc.db_write(7, 0, sSituation)  # Write to sSituation (DB7.DBX0.1)

        sAl = self.plc.db_read(7, 0, 1)
        set_bool(sAl, 0, 2, False)
        self.plc.db_write(7, 0, sAl)  # Write to sAl (DB7.DBX0.2)

        sBirak = self.plc.db_read(7, 0, 1)
        set_bool(sBirak, 0, 3, False)
        self.plc.db_write(7, 0, sBirak)  # Write to sBirak (DB7.DBX0.3)

        data = self.plc.db_read(7, 1, 1)
        set_usint(data, 0, 0)
        self.plc.db_write(7, 1, data)  # Write to sRaf (DB7.DBD1.0)
        data = self.plc.db_read(7, 2, 1)
        set_usint(data, 0, 0)
        self.plc.db_write(7, 2, data)  # Write to sUrun (DB7.DBD2.0)

        if self.system_ready:
            self.timer.start(1000)
        else:
            self.timer.stop()

    def urunAl(self):
        self.operation = "Ürün Al"
        self.urun_al_button.setStyleSheet("background-color: green")
        self.urun_birak_button.setStyleSheet("background-color: white")
        sAl = self.plc.db_read(7, 0, 1)
        set_bool(sAl, 0, 2, True)
        self.plc.db_write(7, 0, sAl)  # Write to sAl (DB7.DBX0.2)
        sBirak = self.plc.db_read(7, 0, 1)
        set_bool(sBirak, 0, 3, False)
        self.plc.db_write(7, 0, sBirak)  # Write to sBirak (DB7.DBX0.3)
        data = self.plc.db_read(7, 1, 1)
        set_usint(data, 0, 0)
        self.plc.db_write(7, 1, data)  # Write to sRaf (DB7.DBD1.0)
        data = self.plc.db_read(7, 2, 1)
        set_usint(data, 0, 0)
        self.plc.db_write(7, 2, data)  # Write to sUrun (DB7.DBD2.0)
     
    def urunBirak(self):
        self.operation = "Ürün Bırak"
        self.urun_birak_button.setStyleSheet("background-color: green")
        self.urun_al_button.setStyleSheet("background-color: white")
        sBirak = self.plc.db_read(7, 0, 1)
        set_bool(sBirak, 0, 3, True)
        self.plc.db_write(7, 0, sBirak)  # Write to sBirak (DB7.DBX0.3)
        sAl = self.plc.db_read(7, 0, 1)
        set_bool(sAl, 0, 2, False)
        self.plc.db_write(7, 0, sAl)  # Write to sAl (DB7.DBX0.2)
        data = self.plc.db_read(7, 1, 1)
        set_usint(data, 0, 0)
        self.plc.db_write(7, 1, data)  # Write to sRaf (DB7.DBD1.0)
        data = self.plc.db_read(7, 2, 1)
        set_usint(data, 0, 0)
        self.plc.db_write(7, 2, data)  # Write to sUrun (DB7.DBD2.0) 

    def startKamera(self):
        self.kamera_button.setStyleSheet("background-color: green")
        self.disableShelfButtons()
        self.urun_al_button.setEnabled(False)
        self.urun_al_button.setStyleSheet("background-color: grey")
        self.urun_birak_button.setEnabled(False)
        self.urun_birak_button.setStyleSheet("background-color: grey")
        for button in self.shelves.values():
            button.setEnabled(False)
            button.setStyleSheet("background-color: grey")
        subprocess.run(["python", "hand.py"])          

    def buttonClicked(self, shelf, position):
        if not self.system_ready:
            return
        self.disableShelfButtons()
        current_button = self.shelves[(shelf, position)]
        if self.operation == "Ürün Al":
            if current_button.styleSheet() == "background-color: orange":
                current_button.setText(f"{position}")
                data = self.plc.db_read(7, 1, 1)
                set_usint(data, 0, shelf)
                self.plc.db_write(7, 1, data)  # Write to sRaf (DB7.DBD1.0)
                data = self.plc.db_read(7, 2, 1)
                set_usint(data, 0, position)
                self.plc.db_write(7, 2, data)  # Write to sUrun (DB7.DBD2.0)
            else:
                QtWidgets.QMessageBox.warning(self.centralwidget, "Uyarı", "Bu raf zaten boş")
                self.enableShelfButtons()
        elif self.operation == "Ürün Bırak":
            if current_button.styleSheet() == "background-color: light blue":
                current_button.setText(f"{position}")
                data = self.plc.db_read(7, 1, 1)
                set_usint(data, 0, shelf)
                self.plc.db_write(7, 1, data)  # Write to sRaf (DB7.DBD1.0)
                data = self.plc.db_read(7, 2, 1)
                set_usint(data, 0, position)
                self.plc.db_write(7, 2, data)  # Write to sUrun (DB7.DBD2.0)
            else:
                QtWidgets.QMessageBox.warning(self.centralwidget, "Uyarı", "Bu raf zaten dolu")
                self.enableShelfButtons()

    def updateShelfColors(self):
        data = self.plc.db_read(1, 0, 20)
        color_changed = False
        if not self.system_on:
            return
        for (shelf, position), button in self.shelves.items():
            for shelf in range(1, 11):
                for position in range(10):
                    button = self.shelves[(shelf, position+1)]
                    shelf_based_index = (shelf-1)*2
                    index = (shelf - 1) * 10 + (position - 1)
                    byte_index = position // 8
                    bit_index = position % 8
                    total_byte_index = shelf_based_index + byte_index   
                    current_color = button.styleSheet()
                    if get_bool(data, total_byte_index, bit_index):
                        button.setStyleSheet("background-color: orange")
                    else:
                        button.setStyleSheet("background-color: light blue")
                    if current_color != button.styleSheet():
                        color_changed = True
        if color_changed:
            self.resetUrunAlBirak()
            self.enableShelfButtons()
            
    def resetUrunAlBirak(self):
        self.operation = None
        self.urun_al_button.setStyleSheet("background-color: white")
        self.urun_birak_button.setStyleSheet("background-color: white")
        sAl = self.plc.db_read(7, 0, 1)
        set_bool(sAl, 0, 2, False)
        self.plc.db_write(7, 0, sAl)  # Write to sAl (DB7.DBX0.2)
        sBirak = self.plc.db_read(7, 0, 1)
        set_bool(sBirak, 0, 3, False)
        self.plc.db_write(7, 0, sBirak)  # Write to sBirak (DB7.DBX0.3)
        data = self.plc.db_read(7, 1, 1)
        set_usint(data, 0, 0)
        self.plc.db_write(7, 1, data)  # Write to sRaf (DB7.DBD1.0)
        data = self.plc.db_read(7, 2, 1)
        set_usint(data, 0, 0)
        self.plc.db_write(7, 2, data)  # Write to sUrun (DB7.DBD2.0)

    def clearShelfColors(self):
        for (shelf, position), button in self.shelves.items():
            button.setStyleSheet("")

    def disableShelfButtons(self):
        for button in self.shelves.values():
            button.setEnabled(False)

    def enableShelfButtons(self):
        for button in self.shelves.values():
            button.setEnabled(True)


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    MainWindow = QtWidgets.QMainWindow()
    ui = Ui_MainWindow()
    ui.setupUi(MainWindow)
    MainWindow.show()
    sys.exit(app.exec_())