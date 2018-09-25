import sys, os
from subprocess import Popen
from PyQt4 import QtGui, QtCore
from popplerqt4 import Poppler

import resources_rc
from ui_main_window import Ui_window
from __init__ import __version__

class ImageViewer(QtGui.QMainWindow, Ui_window):
    def __init__(self):
        super(ImageViewer, self).__init__()

        self.initUI()

    def initUI(self):


        file = open("email.txt", "r")
        self.text = file.read()

        # topleft = QtGui.QFrame()
        # topleft.setFrameShape(QtGui.QFrame.StyledPanel)

        self.btn = QtGui.QPushButton("save")
        self.btn.clicked.connect(self.SavetoPDF)

        self.textEdit = QtGui.QTextEdit()
        self.textEdit.setText(self.text)

        # self.frame = QtGui.QFrame()
        # self.frame.setFrameStyle(QtGui.QFrame.Panel |
        #         QtGui.QFrame.Plain)

        self.scrollArea = QtGui.QScrollArea()
        self.scrollArea.setBackgroundRole(QtGui.QPalette.Dark)
        #self.scrollArea.setWidget(self.textEdit)
        self.scrollArea.setWidgetResizable(True)





        self.table = QtGui.QTableWidget()
        self.table.setColumnCount(3)

        self.table.setHorizontalHeaderLabels(QtCore.QString("Page;Document Title;Text").split(";"))
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.horizontalHeader().setResizeMode(1, QtGui.QHeaderView.ResizeToContents)
        self.table.verticalHeader().hide()
        self.table.setColumnWidth(0,50)
        self.table.setEditTriggers(QtGui.QAbstractItemView.NoEditTriggers)
        self.table.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)

        self.table.setRowCount(18)

        self.table.setMinimumHeight(600)

        gbSearch = QtGui.QGroupBox('Search..')
        self.pageNavigratorSearch = QtGui.QHBoxLayout() #create Horizontal Box layout

        self.searchText =  QtGui.QLineEdit("Rear Admiral")

        self.searchBtn = QtGui.QPushButton('Search') #search btn


        self.cal = QtGui.QCalendarWidget()  #first calender
        self.cal.setGridVisible(True)
        self.cal.setVerticalHeaderFormat(QtGui.QCalendarWidget.NoVerticalHeader)

        self.calTo = QtGui.QCalendarWidget() #second calender
        self.calTo.setGridVisible(True)
        self.calTo.setVerticalHeaderFormat(QtGui.QCalendarWidget.NoVerticalHeader)

        self.pageNavigratorSearch.addWidget(self.cal) #add cal cal2 and button to horizontal layout
        self.pageNavigratorSearch.addWidget(self.calTo)
        self.pageNavigratorSearch.addWidget(self.searchBtn)

        gbSearch.setLayout(self.pageNavigratorSearch)

        self.configureLayout = QtGui.QGridLayout()      #------Another grid layout----------
        self.configureLayout.addWidget(self.searchText , 0, 0) #----adding line edit to layout
        self.configureLayout.addWidget(gbSearch , 1, 0) #-------adding gbsearch groupbox to layout
        #self.configureLayout.addWidget(self.searchBtn,2,0)
        self.configureLayout.addWidget(self.table , 2, 0) #--------adding table to layout-----
        self.configureLayout.setHorizontalSpacing(2)

        self.configureWidget = QtGui.QWidget()
        self.configureWidget.setMaximumWidth(550)
        self.configureWidget.setLayout(self.configureLayout)

        self.commentsLayout = QtGui.QGridLayout()  # --------------Another Grid layout--------

        self.commentsTable = QtGui.QTableWidget() #---------craeting comment table------
        self.commentsTable.setColumnCount(2)
        self.commentsTable.setRowCount(4)
        self.commentsTable.setHorizontalHeaderLabels(QtCore.QString(";User").split(";"))
        self.commentsTable.horizontalHeader().setStretchLastSection(True)
        self.commentsTable.verticalHeader().hide()
        self.commentsTable.setColumnWidth(0,50)
        self.commentsTable.setEditTriggers(QtGui.QAbstractItemView.NoEditTriggers)
        self.commentsTable.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)

        self.commentsViewTable = QtGui.QTableWidget() #------------creating Another comment table----
        self.commentsViewTable.setColumnCount(2)
        self.commentsViewTable.setRowCount(4)

        self.commentsViewTable.setHorizontalHeaderLabels(QtCore.QString(";Comment").split(";"))
        self.commentsViewTable.horizontalHeader().setStretchLastSection(True)
        self.commentsViewTable.verticalHeader().hide()
        self.commentsViewTable.setColumnWidth(0,50)
        self.commentsViewTable.setEditTriggers(QtGui.QAbstractItemView.NoEditTriggers)
        self.commentsViewTable.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
        self.commentsViewTable.setMinimumHeight(600)
        self.commentsLayout.addWidget(self.commentsTable ,0,0,QtCore.Qt.AlignTop ) #----------adding table to the layout
        self.commentsLayout.addWidget(self.commentsViewTable ,1,0)
        self.commentsLayout.setRowStretch(0,3)
        # self.commentsTable.setStretch(0, 1)
        self.commentsLayout.setHorizontalSpacing(2)

        self.commentsWidget = QtGui.QWidget()
        self.commentsWidget.setMaximumWidth(300)
        self.commentsWidget.setLayout(self.commentsLayout)


        self.mainLayout = QtGui.QGridLayout() # --------Main Layout-----------------------
        self.mainLayout.addWidget(self.btn,0,0)
        self.mainLayout.addWidget(self.scrollArea, 1,0)  #-------------adding grids to ths main layout----------
        self.mainLayout.addWidget(self.commentsWidget , 1,2)
        self.mainLayout.addWidget(self.configureWidget , 1,3)

        self.setCentralWidget(QtGui.QWidget(self))
        self.centralWidget().setLayout(self.mainLayout)

        self.showMaximized()

        #self.setGeometry(300,300,350,300)
        self.show()

    def SavetoPDF(self):



        filename = "temp.pdf"
        if filename:
            printer = QtGui.QPrinter(QtGui.QPrinter.HighResolution)

            printer.setPageSize(QtGui.QPrinter.A4)
            printer.setColorMode(QtGui.QPrinter.Color)
            printer.setOutputFormat(QtGui.QPrinter.PdfFormat)
            printer.setOutputFileName(filename)

            self.textEdit.document().print_(printer)

            # painter.begin(printer)
            # painter.drawText(500,500,500,500,500,text)
            # painter.end()

def main():

    app = QtGui.QApplication(sys.argv)
    ex = ImageViewer()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
